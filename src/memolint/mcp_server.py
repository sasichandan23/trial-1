"""Memolint as an MCP server: team memory for any coding agent.

Reviewing code after it is written is the narrow use of a team memory bank. The
broader one is letting the agent that *writes* the code consult the same memory
first, so it follows your conventions instead of being corrected afterwards.

This exposes the bank over the Model Context Protocol, so Claude Code, Codex,
Cursor, Antigravity or anything else that speaks MCP can use it.

Run it directly:

    memolint-mcp

Or point a client at it; see docs/MCP.md for per-client configuration.
"""

from __future__ import annotations

import os
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from .config import ConfigError, bank_id_for, load_settings
from .diff import from_file, from_git, parse_unified_diff
from .llm import LLM, LLMError
from .memory import Memory
from .reviewer import review_diff

INSTRUCTIONS = """Memolint stores what a software team has decided: its conventions, how
reviewers responded to past suggestions, and incidents tied to code patterns.

Call `recall_team_memory` BEFORE writing or changing code in a repository, so the code you
produce follows this team's conventions rather than generic best practice. It is cheap and
it is the whole point of this server.

Call `remember_convention` when the user states a rule ("we always...", "don't ever...").
Call `remember_incident` when the user describes a bug or outage caused by a code pattern.
Call `review_changes` to review a diff with the team's memory applied.

Memory is per repository. Pass `repo` as "owner/name" when you know it."""


def _default_repo() -> str:
    """Best guess at which repository the client is working in."""
    import subprocess
    from pathlib import Path

    if os.getenv("MEMOLINT_REPO"):
        return os.environ["MEMOLINT_REPO"]
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"],
                             capture_output=True, text=True, check=True, timeout=5).stdout.strip()
        tail = url.rstrip("/").removesuffix(".git").replace(":", "/")
        parts = [p for p in tail.split("/") if p]
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    except Exception:
        pass
    return Path.cwd().name


# One Memory per bank, reused across tool calls. Each one owns an HTTP session and
# registers an atexit handler, so building a fresh one per call leaks both.
_BANKS: dict[str, Memory] = {}


def _memory(repo: str | None) -> Memory:
    slug = repo or _default_repo()
    if slug not in _BANKS:
        settings = load_settings(require_llm=False)
        m = Memory(settings, bank_id_for(slug), slug)
        m.ensure_bank()
        _BANKS[slug] = m
    return _BANKS[slug]


Repo = Annotated[str | None, Field(default=None, description='Repository as "owner/name". Omit to use the current git remote.')]


def build_server() -> MCPServer:
    mcp = MCPServer(
        name="memolint",
        title="Memolint team memory",
        instructions=INSTRUCTIONS,
        version="0.1.0",
    )

    @mcp.tool(
        description="Recall what this team has decided that is relevant to the code you are "
                    "about to write or review: conventions, past review feedback, rejected "
                    "suggestions, and incidents tied to code patterns. Call this FIRST."
    )
    def recall_team_memory(
        query: Annotated[str, Field(description="What you are about to do, e.g. 'adding a loop that calls the payments API per order'")],
        repo: Repo = None,
    ) -> str:
        bundle = _memory(repo).recall_for_review(query)
        if bundle.is_empty():
            return "No memories yet for this repository. Nothing this team has decided applies here."
        return bundle.to_prompt_text()

    @mcp.tool(
        description="Store a standing team convention. Use when the user states a rule, "
                    "such as 'we always use guard clauses' or 'never log with print'."
    )
    def remember_convention(
        rule: Annotated[str, Field(description="The rule, phrased as a reusable instruction")],
        repo: Repo = None,
    ) -> str:
        _memory(repo).teach(rule)
        return f"Stored as a standing rule: {rule}"

    @mcp.tool(
        description="Record a bug or outage caused by a code pattern, so future changes "
                    "repeating that pattern get flagged with the precedent."
    )
    def remember_incident(
        description: Annotated[str, Field(description="What broke, the code pattern behind it, and what it cost")],
        reference: Annotated[str | None, Field(default=None, description="Linked PR, ticket or commit")] = None,
        repo: Repo = None,
    ) -> str:
        _memory(repo).record_incident(description, reference)
        return "Incident recorded. Future changes with this shape will cite it."

    @mcp.tool(
        description="Review a code change with the team's memory applied. Accepts a unified "
                    "diff, or a git range to diff in the current working directory."
    )
    def review_changes(
        diff: Annotated[str | None, Field(default=None, description="A unified diff")] = None,
        git_range: Annotated[str | None, Field(default=None, description="A git range such as main..HEAD")] = None,
        title: Annotated[str, Field(default="Pending change", description="What the change does")] = "Pending change",
        repo: Repo = None,
    ) -> str:
        if (diff is None) == (git_range is None):
            return "Error: pass exactly one of `diff` or `git_range`."
        try:
            settings = load_settings()
        except ConfigError as e:
            return f"Error: {e}"
        bundle = parse_unified_diff(diff, title=title) if diff else from_git(*git_range.split("..", 1))
        if not bundle.paths:
            return "Nothing reviewable in that change."
        try:
            review = review_diff(bundle, title, LLM(settings.llm_chain), _memory(repo))
        except LLMError as e:
            return f"Error: {e}"

        out = [review.summary, ""]
        for f in review.findings:
            where = f"{f.file}" + (f":{f.line}" if f.line else "")
            out.append(f"[{f.severity.upper()}] {f.title} ({where})")
            out.append(f"  {f.body}")
            if f.precedent:
                out.append(f"  precedent: {f.precedent}")
        if review.skipped_on_purpose:
            out.append("")
            out.append("Deliberately not raised, because this team rejected it before:")
            for s in review.skipped_on_purpose:
                out.append(f"  - {s.get('what')} ({s.get('why')})")
        out.append("")
        out.append(f"({review.memories_used} memories recalled)")
        return "\n".join(out)

    @mcp.tool(
        description="Ask the team's memory a free-form question, such as 'what does this "
                    "team care about in reviews?'. Reasons over the whole bank."
    )
    def ask_memory(
        question: Annotated[str, Field(description="The question to ask")],
        repo: Repo = None,
    ) -> str:
        return _memory(repo).reflect(question)

    @mcp.tool(
        description="List what this team's memory currently holds. Useful for showing the "
                    "user what the agent knows, or for auditing stale rules."
    )
    def list_team_memory(
        limit: Annotated[int, Field(default=50, description="Maximum memories to return")] = 50,
        repo: Repo = None,
    ) -> str:
        mem = _memory(repo)
        lines = []
        rules = mem.list_directives()
        if rules:
            lines.append("Standing rules:")
            lines += [f"  - {r}" for r in rules]
            lines.append("")
        items = mem.list_all(limit=limit)
        if not items:
            lines.append("No memories stored yet.")
        else:
            lines.append(f"{len(items)} memories:")
            lines += [f"  [{i.kind}] {i.text}" for i in items]
        return "\n".join(lines)

    return mcp


def main() -> None:
    build_server().run(transport=os.getenv("MEMOLINT_MCP_TRANSPORT", "stdio"))


if __name__ == "__main__":
    main()
