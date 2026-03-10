# Snack Stash

A personal CLI tool for managing a local stash of reusable Python code snippets. Copy snippets in and out of projects with a single command, and manage multiple named stashes.

## Quick Start

```bash
# Install
pipx install snack-stash

# Create your first stash
snack stash create default ~/snack-stash

# Browse what you have
snack list

# Pull snippets from a GitHub repo into your stash
snack stash add-remote owner/my-snippets

# Copy a snippet into your project
snack unpack auth/google_oauth.py

# Copy an improved snippet back into the stash
snack pack auth/google_oauth.py
```

## Pages

- [[Installation]] — Install via pipx or pip
- [[Configuration]] — Named stashes, env var, and config file
- [[Commands-Reference]] — Full reference for all commands and flags
- [[Writing-Good-Snippets]] — How to write snippets that stay reusable
- [[Error-Reference]] — Diagnose and fix common errors
- [[Contributing]] — Dev setup, tests, and release process

## Links

- [PyPI — snack-stash](https://pypi.org/project/snack-stash/)
- [GitHub Repository](https://github.com/kickash/python-snacks)
