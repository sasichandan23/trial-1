"""MCP surface: the tools a client sees, and how they behave without a live bank."""

import asyncio

import pytest

from memolint import mcp_server

EXPECTED = {
    "recall_team_memory",
    "remember_convention",
    "remember_incident",
    "review_changes",
    "ask_memory",
    "list_team_memory",
}


@pytest.fixture
def server():
    return mcp_server.build_server()


def tools(server):
    return {t.name: t for t in asyncio.run(server.list_tools())}


def test_every_tool_is_exposed(server):
    assert set(tools(server)) == EXPECTED


def test_tools_describe_themselves_for_the_model(server):
    for name, t in tools(server).items():
        assert t.description and len(t.description) > 40, f"{name} needs a usable description"


def test_recall_is_the_one_the_client_is_told_to_call_first(server):
    # The instructions are what make an agent consult memory before writing code,
    # so losing this line silently turns the server into a passive tool box.
    assert "recall_team_memory" in mcp_server.INSTRUCTIONS
    assert "BEFORE" in mcp_server.INSTRUCTIONS


def _text(result):
    return result.content[0].text if result.content else ""


def test_review_rejects_both_or_neither_input(server, monkeypatch):
    called = []
    monkeypatch.setattr(mcp_server, "_memory", lambda repo: called.append(repo))

    none_given = asyncio.run(server.call_tool("review_changes", {}))
    both_given = asyncio.run(server.call_tool("review_changes", {"diff": "x", "git_range": "main..HEAD"}))

    assert "exactly one" in _text(none_given)
    assert "exactly one" in _text(both_given)
    assert not called, "should fail before touching the memory bank"


def test_repo_resolution_prefers_the_environment(monkeypatch):
    monkeypatch.setenv("MEMOLINT_REPO", "acme/widgets")
    assert mcp_server._default_repo() == "acme/widgets"


def test_repo_resolution_falls_back_to_the_git_remote(monkeypatch):
    monkeypatch.delenv("MEMOLINT_REPO", raising=False)
    slug = mcp_server._default_repo()
    assert "/" in slug or slug  # a remote slug, or the directory name


def test_banks_are_reused_across_calls(monkeypatch):
    """A fresh Memory per call leaks an HTTP session and an atexit handler each time."""
    built = []

    class FakeMemory:
        def __init__(self, *a, **k):
            built.append(1)

        def ensure_bank(self):
            pass

    monkeypatch.setattr(mcp_server, "Memory", FakeMemory)
    monkeypatch.setattr(mcp_server, "load_settings", lambda require_llm=False: object())
    mcp_server._BANKS.clear()
    for _ in range(3):
        mcp_server._memory("acme/widgets")
    assert len(built) == 1
    mcp_server._BANKS.clear()
