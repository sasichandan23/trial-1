# Publishing to PyPI

Until this is on PyPI, installing means cloning the repo. After it, installing is one
line, and that is the difference between someone trying it and someone not.

The name `memolint` is free on PyPI (checked before we chose it).

## Build

```bash
pip install build twine
python -m build --wheel --sdist
python -m twine check dist/*
```

Both artifacts already pass `twine check`.

## Publish

You need a PyPI account and an API token from https://pypi.org/manage/account/token/.
Test it on TestPyPI first if you want a dry run:

```bash
python -m twine upload --repository testpypi dist/*
```

Then the real thing:

```bash
python -m twine upload dist/*
```

Username is `__token__` and the password is the token, including the `pypi-` prefix.

## What it unlocks

```bash
pipx install memolint
```

Or, with no install at all, which is how most people try an MCP server:

```bash
claude mcp add memolint -- uvx --from memolint memolint-mcp
```

`uvx` downloads the package into a throwaway environment and runs it. Nothing to clone,
nothing left behind.

## Automatic releases

`.github/workflows/publish.yml` publishes on a version tag:

```bash
git tag v0.1.0 && git push --tags
```

It uses PyPI Trusted Publishing, so no token is stored in the repository. One-time setup
on pypi.org, under the project's Publishing settings:

| Field | Value |
|---|---|
| Owner | `WaifuPuller` |
| Repository | `MemoLint` |
| Workflow | `publish.yml` |
| Environment | `pypi` |

You still need a PyPI account to do that configuration. There is no way around it: PyPI
has to know who owns the name.

For the very first release, uploading manually with a token is simpler, and the workflow
takes over from the second release onward.

## Before each release

- Bump `version` in `pyproject.toml`. PyPI refuses a version that already exists.
- Run the tests.
- Rebuild. `dist/` is gitignored, so delete old artifacts first or you will upload stale ones.
