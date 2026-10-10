# Getting the latest work into MemoLint

Two things to do. The first is a live bug; do it even if you skip the second.

## 1. Fix two dead links (one minute)

The find-and-replace that swapped the co-author name also replaced the name *inside* two
URLs, so both now 404. They are in `docs/FORM-LINKS.md`.

| Currently in your repo | Should be |
|---|---|
| `dev.to/WaifuPuller_068c2e22e9b0/...` | `dev.to/sasi_chandan_068c2e22e9b0/...` |
| `linkedin.com/posts/WaifuPuller-733054365_...` | `linkedin.com/posts/sasi-chandan-733054365_...` |

Verified: the `WaifuPuller` variants return 404, the `sasi_chandan` ones return 200.

Also check the links you put on the submission form. If you copied them from that file,
the article and LinkedIn post for the second member were unreachable.

Fix it from the repo root:

```bash
sed -i 's|dev.to/WaifuPuller_068c2e22e9b0|dev.to/sasi_chandan_068c2e22e9b0|; s|posts/WaifuPuller-733054365|posts/sasi-chandan-733054365|' docs/FORM-LINKS.md
```

The same replace also turned an em dash into a replacement character on line 31 of that
file, and changed two section headings from "Sasi Chandan" to "WaifuPuller". Cosmetic,
but worth tidying while you are in there.

## 2. Pull the MCP server and packaging work

Your history was rewritten, so the hashes differ from ours and `git pull` will not
fast-forward. Cherry-pick instead. The two commits are already attributed to
`sasichandan23`, so nothing to rewrite afterwards.

```bash
git fetch https://github.com/sasichandan23/trial-1.git for-lead
git cherry-pick 71c8d18..FETCH_HEAD
git push
```

If `71c8d18` is not known locally, use this instead, which picks the two commits by
message:

```bash
git fetch https://github.com/sasichandan23/trial-1.git for-lead
git cherry-pick FETCH_HEAD~1 FETCH_HEAD
git push
```

### What arrives

- `src/memolint/mcp_server.py`, six tools over the Model Context Protocol, so Claude Code,
  Codex, Cursor and anything else that speaks MCP can query the team memory. Tested
  against the live bank.
- PyPI packaging: full metadata, builds clean, installs into an empty environment.
- `HINDSIGHT_BASE_URL` now defaults to Hindsight Cloud, so new users need one key instead
  of a key plus a URL.
- `docs/MCP.md`, `docs/PUBLISHING.md`, and seven more tests. 36 pass.

### If a conflict appears

It will be in `docs/FORM-LINKS.md` or `docs/SUBMISSION.md`, the only two files that differ
between the repos. Keep the version with `sasi_chandan` and `sasi-chandan` inside the URLs,
since those are the ones that actually resolve.

## 3. Publish to PyPI

Pushing to GitHub does **not** publish the package. PyPI is a separate system. Until it is
uploaded, `pip install memolint` fails and installing still means cloning this repo.

The name `memolint` is free. Two routes.

### Recommended: no token anywhere

A human does steps 1 and 2 in a browser, once. After that, releasing is a git tag, which
an agent can run safely because no credential exists.

1. Create a PyPI account. Two-factor authentication is mandatory, so this part cannot be
   automated.
2. At https://pypi.org/manage/account/publishing add a **pending publisher**. Pending
   publishers exist precisely for projects that do not exist yet:

   | Field | Value |
   |---|---|
   | PyPI project name | `memolint` |
   | Owner | `WaifuPuller` |
   | Repository name | `MemoLint` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

3. In GitHub, Settings then Environments, create an environment named exactly `pypi`.
4. Release:

   ```bash
   git tag v0.1.0 && git push --tags
   ```

GitHub proves its own identity to PyPI over OIDC and the package publishes. No token is
created, stored or pasted anywhere.

**Three things that break it, all silent:**

- The environment name must match on both sides. The workflow sets `environment: pypi`, so
  PyPI must have `pypi` in that field and GitHub must have an environment of that name. If
  you leave it blank on PyPI, remove it from the workflow too.
- Renaming the repository, moving it to another owner, or renaming `publish.yml` breaks
  the trust relationship.
- A pending publisher does not reserve the name. If someone else registers `memolint`
  before your first publish, it is invalidated.

### Faster but uses a token

```bash
pip install build twine
python -m build --wheel --sdist
python -m twine upload dist/*
```

Username `__token__`, password a token from https://pypi.org/manage/account/token/.

Do this one yourself rather than handing the token to an agent. The token has permanent
publish rights over the package name.

### What it unlocks either way

```bash
pipx install memolint
claude mcp add memolint -- uvx --from memolint memolint-mcp
```

That one line is the answer when someone asks how to run it on their own laptop.
