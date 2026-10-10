# Memolint as an MCP server

Reviewing code after it is written is the narrow use of a team memory bank. The broader
one is letting the agent that *writes* the code consult the same memory first, so it
follows your conventions instead of being corrected afterwards.

Memolint exposes its memory over the Model Context Protocol, so any MCP client can use
it. Same server, same bank, every client.

```
                        ┌──────────────────┐
  Claude Code  ──┐      │                  │
  Codex        ──┤      │  memolint-mcp    │ ◄──► Hindsight bank
  Cursor       ──┼─────►│  (stdio)         │      (per repository)
  Antigravity  ──┤      │                  │
  anything MCP ──┘      └──────────────────┘
```

## Tools it exposes

| Tool | When the agent should call it |
|---|---|
| `recall_team_memory` | **Before writing or changing code.** Returns conventions, past feedback and incidents relevant to what you are about to do. |
| `remember_convention` | The user states a rule: "we always...", "never...". |
| `remember_incident` | The user describes a bug or outage caused by a code pattern. |
| `review_changes` | Review a diff or a git range with memory applied. |
| `ask_memory` | Free-form question over the whole bank. |
| `list_team_memory` | Show what the agent knows, or audit stale rules. |

The server ships instructions telling the client to call `recall_team_memory` first. That
single habit is what turns this from a review tool into a memory layer.

## Install

No PyPI account or clone required:

```bash
pip install git+https://github.com/WaifuPuller/MemoLint
```

Or from a checkout:

```bash
pip install -e .
```

Either puts `memolint-mcp` on your PATH. It needs the same `.env` as the CLI, so follow
[KEYS.md](../KEYS.md) first. Only the Hindsight values are required for the memory tools;
`review_changes` also needs a model key.

## Claude Code

```bash
claude mcp add memolint -- memolint-mcp
```

Or add it to `.mcp.json` in the project root so the whole team gets it:

```json
{
  "mcpServers": {
    "memolint": {
      "command": "memolint-mcp",
      "env": { "MEMOLINT_REPO": "owner/repo" }
    }
  }
}
```

## Codex

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.memolint]
command = "memolint-mcp"
```

## Cursor, Windsurf, and other MCP clients

They all take the same shape in their own config file:

```json
{
  "mcpServers": {
    "memolint": { "command": "memolint-mcp" }
  }
}
```

## Antigravity

Antigravity supports MCP, but confirm the current config file location in its docs before
relying on this. The server itself needs no change; stdio is stdio.

## Who sees what

The server runs locally and stores nothing. The memory lives in a Hindsight bank, and the
API key decides which bank you reach. Everything else follows from that.

| Situation | What happens |
|---|---|
| One person, own key | Their own bank. Nobody else can read it, and installing from a public repo exposes no one else's memory. |
| A team sharing memory | Every member uses a key from the **same** Hindsight account, so they all reach one bank. A rule one person teaches shows up in everyone's next review. |
| Code that cannot leave the building | Self-host Hindsight and point everyone at that URL. With a local model, nothing reaches a third party. |

Separate Hindsight accounts mean separate banks even for the same repository, because the
bank id is scoped to the account behind the key. Memory is shared when the Hindsight
instance is shared, not when the tool is installed.

## Which repository does it use

In order: the `repo` argument on the tool call, then `MEMOLINT_REPO` in the environment,
then the `origin` git remote of the working directory. One Hindsight bank per repository,
so a team's opinions stay scoped to the team that formed them.

## Verifying it works

```bash
memolint-mcp
```

It will sit there waiting on stdin, which is correct: stdio transport means the client
drives it. To exercise it end to end, use any MCP client, or the script in this repo's
history that drives it with the Python MCP client.

Set `MEMOLINT_MCP_TRANSPORT=streamable-http` to run it over HTTP instead of stdio, for
clients that prefer that.
