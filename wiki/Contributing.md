# Contributing

## Dev Setup

Clone the repo and install in editable mode with test dependencies:

```bash
git clone https://github.com/kickash/python-snacks.git
cd python-snacks
pip install -e ".[test]"
```

Verify the CLI works:

```bash
snack --help
```

## Running Tests

```bash
pytest tests/ -v
```

The test suite has 33 tests across two files:

- `tests/test_commands.py` — snippet commands (`list`, `search`, `unpack`, `pack`), config resolution, error cases
- `tests/test_stash_commands.py` — stash management commands (`create`, `list`, `move`, `add-remote`), including mocked HTTP for `add-remote`

Tests never write to `~/.snackstashrc` — the config path is redirected to a temp file via `monkeypatch`.

## CI

Every push and pull request to `main` runs the test suite against Python 3.10, 3.11, and 3.12 via GitHub Actions (`.github/workflows/ci.yml`). Pull requests must pass CI before merging.

## Release Process

Releases are fully automated via `.github/workflows/publish.yml`.

1. Update the version in `pyproject.toml`
2. Commit and push to `main`
3. Tag the commit with a `v`-prefixed version and push the tag:

```bash
git tag v0.2.0
git push origin v0.2.0
```

The publish workflow will:
- Run the test suite
- Build the sdist and wheel
- Publish to PyPI (via OIDC trusted publishing — no API token required)
- Create a GitHub Release with the built artifacts attached

## Project Structure

```
python-snacks/
├── pyproject.toml              # Package metadata and dependencies
├── snacks/
│   ├── main.py                 # Typer app and all command definitions
│   ├── config.py               # SnackConfig class, stash path resolution
│   └── ops.py                  # File ops: pack, unpack, add_remote
└── tests/
    ├── test_commands.py        # Snippet command tests
    └── test_stash_commands.py  # Stash management tests
```

## Key design notes

- **Config format:** `~/.snackstashrc` uses INI format (`[stash.<name>]` sections). The old `stash=<path>` sectionless format is still read for backwards compatibility but never written.
- **`SNACK_STASH` env var:** Always overrides the config file for all snippet commands. Useful for scripts and CI.
- **`add-remote`:** Uses only stdlib (`urllib`, `tarfile`) — no additional dependencies beyond Typer.
- **Test isolation:** `monkeypatch.setattr(config_module, "CONFIG_PATH", ...)` redirects the config file to a temp path so tests are hermetic.
