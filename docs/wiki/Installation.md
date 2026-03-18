# Installation

## Requirements

- Python 3.10 or later

## Recommended: pipx

[pipx](https://pipx.pypa.io) installs CLI tools in isolated environments so they don't conflict with your project dependencies.

```bash
pipx install python-snacks
```

## Alternative: pip

```bash
pip install python-snacks
```

If you want it available globally, use `pip install --user python-snacks` or install inside a virtual environment you always activate.

## Verify

```bash
snack --help
```

You should see:

```
Usage: snack [OPTIONS] COMMAND [ARGS]...

  Manage your personal snack stash of reusable Python snippets.

Commands:
  unpack  Copy a snippet FROM the stash INTO the current working directory.
  pack    Copy a snippet FROM the current working directory INTO the stash.
  list    List all snippets in the stash.
  search  Search snippet filenames for a keyword.
  stash   Manage stash directories.
```

## Upgrading

```bash
pipx upgrade python-snacks
# or
pip install --upgrade python-snacks
```

New versions are published to PyPI automatically when a `v*` tag is pushed to the repository.

## Next Step

[[Configuration]] — create your first stash and tell the tool where it lives.
