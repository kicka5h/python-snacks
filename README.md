# python-snacks

A personal CLI tool for managing a local stash of reusable Python code snippets. Browse, copy, and curate snippets across projects with a single command.

```bash
pipx install python-snacks
snack stash create default ~/snack-stash
snack unpack auth/google_oauth.py
```

---

## Installation

**Recommended (pipx):**
```bash
pipx install python-snacks
```

**Alternative (pip):**
```bash
pip install python-snacks
```

Requires Python 3.10+.

**Updating:**
```bash
pipx upgrade python-snacks   # if installed with pipx
pip install --upgrade python-snacks  # if installed with pip
```

---

## Configuration

### First-time setup

Create a stash directory and register it:

```bash
snack stash create default ~/snack-stash
```

This creates `~/snack-stash`, writes `~/.snackstashrc`, and sets `default` as the active stash.

### Environment variable (overrides config file)

```bash
export SNACK_STASH=~/snack-stash
```

Add to `~/.zshrc` or `~/.bashrc` to make it permanent. Takes priority over everything else.

### Config file (`~/.snackstashrc`)

Created automatically by `snack stash create`. You can also edit it by hand:

```ini
[config]
active = default

[stash.default]
path = ~/snack-stash

[stash.work]
path = ~/work-stash
```

**Priority order:** `SNACK_STASH` env var → `~/.snackstashrc` active stash → error.

---

## Stash structure

A stash is a plain directory of `.py` files, organized into subdirectories by category:

```
~/snack-stash/
├── auth/
│   ├── google_oauth_fastapi.py
│   ├── google_oauth_flask.py
│   └── jwt_helpers.py
├── forms/
│   ├── contact_form.py
│   └── newsletter_signup.py
└── email/
    └── smtp_sender.py
```

You can manage the directory with Git, Dropbox, or any sync tool independently of this CLI.

---

## Commands

### `snack list [category]`

List all snippets in the active stash.

```bash
snack list           # all snippets
snack list auth      # filtered by category (subdirectory)
```

### `snack search <keyword>`

Search snippet filenames for a keyword (case-insensitive).

```bash
snack search oauth
# auth/google_oauth_fastapi.py
# auth/google_oauth_flask.py
```

### `snack unpack <snippet>`

Copy a snippet **from the stash** into the current working directory.

```bash
snack unpack auth/google_oauth_fastapi.py
# → ./auth/google_oauth_fastapi.py

snack unpack auth/google_oauth_fastapi.py --flat
# → ./google_oauth_fastapi.py  (no subdirectory)

snack unpack auth/google_oauth_fastapi.py --force
# Overwrites without prompting
```

### `snack pack <snippet>`

Copy a file **from the current directory** back into the stash. Use this when you've improved a snippet on a project and want to update the canonical version.

```bash
snack pack auth/google_oauth_fastapi.py
snack pack auth/google_oauth_fastapi.py --force
```

---

## Stash management

### `snack stash create <name> <path>`

Register a new named stash. Creates the directory if it doesn't exist.

```bash
snack stash create default ~/snack-stash
snack stash create work ~/work-stash --no-activate
```

The first stash created is automatically set as active. Use `--no-activate` to add a stash without switching to it.

### `snack stash list`

Show all configured stashes and which one is active.

```bash
snack stash list
#   default  /Users/you/snack-stash  ← active
#   work     /Users/you/work-stash
```

### `snack stash move <name> <new-path>`

Move a stash to a new location. Moves the directory on disk and updates the config.

```bash
snack stash move default ~/new-location/snack-stash
```

### `snack stash add-remote <repo>`

Copy Python snippets from a public GitHub repository into the active stash. Downloads the repo as a tarball and copies all `.py` files, preserving directory structure.

```bash
snack stash add-remote owner/repo
snack stash add-remote https://github.com/owner/repo
snack stash add-remote owner/repo --subdir auth   # only copy files under auth/
snack stash add-remote owner/repo --force         # overwrite without prompting
```

---

## Error handling

| Situation | Behaviour |
|---|---|
| No stash configured | Error with setup instructions |
| Stash path doesn't exist | Error with the attempted path |
| Snippet not found in stash | Error — use `snack list` or `snack search` |
| Source file not found | Error |
| Destination file already exists | Prompt to confirm, or skip with `--force` |
| Named stash already exists | Error |
| Move target already exists | Error |
| GitHub repo not found (HTTP 404) | Error with status code |

---

## Project structure

```
python-snacks/
├── pyproject.toml
├── snacks/
│   ├── main.py      # Typer app, all command definitions
│   ├── config.py    # SnackConfig class, stash path resolution
│   └── ops.py       # File copy logic (pack, unpack, add_remote)
└── tests/
    ├── test_commands.py        # snippet commands
    └── test_stash_commands.py  # stash management commands
```

---

## CI / CD

- **CI:** Tests run on every push and PR to `main` across Python 3.10, 3.11, and 3.12.
- **Publish:** Push a `v*` tag to trigger a build, PyPI publish, and GitHub Release.

```bash
git tag v0.2.0 && git push origin v0.2.0
```
