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

Pushing to GitHub does **not** publish the package. PyPI is a separate system and has to
be uploaded to explicitly. Until that happens, `pip install memolint` fails and installing
still means cloning this repo.

The name `memolint` is free. Claim it:

1. Make a PyPI account and an API token at https://pypi.org/manage/account/token/
2. From the repo root:

```bash
pip install build twine
python -m build --wheel --sdist
python -m twine upload dist/*
```

Username is `__token__`, password is the token including the `pypi-` prefix.

After that, anyone can run:

```bash
pipx install memolint
claude mcp add memolint -- uvx --from memolint memolint-mcp
```

That one line is the answer when someone asks how to run it on their own laptop.

Releases after the first one are automatic: `.github/workflows/publish.yml` publishes on a
version tag, using Trusted Publishing so no token lives in the repository. It needs a
one-time configuration on pypi.org, described in `docs/PUBLISHING.md`.
