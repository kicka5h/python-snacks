# Commands Reference

## Summary

| Command | Description |
|---|---|
| `snack list [category]` | List all snippets, optionally filtered by category |
| `snack search <keyword>` | Search snippet filenames for a keyword |
| `snack unpack <snippet> [--flat] [--force]` | Copy a snippet from the stash into the current directory |
| `snack pack <snippet> [--force]` | Copy a snippet from the current directory into the stash |
| `snack stash create <name> <path>` | Register a new named stash directory |
| `snack stash list` | List all configured stashes |
| `snack stash move <name> <new-path>` | Move a stash to a new location |
| `snack stash add-remote <repo> [--subdir] [--force]` | Copy snippets from a GitHub repo into the active stash |

All commands accept `--help` for inline usage information.

---

## Snippet commands

These commands operate on the **active stash** (set via `snack stash create` or the `SNACK_STASH` env var).

### `snack list`

Lists all `.py` files in the stash, sorted alphabetically.

```bash
snack list
```

Output:

```
auth/google_oauth_fastapi.py
auth/google_oauth_flask.py
auth/jwt_helpers.py
forms/contact_form.py
forms/newsletter_signup.py
email/smtp_sender.py
```

#### Filter by category

Pass a category name (subdirectory) to narrow the output:

```bash
snack list auth
```

Output:

```
auth/google_oauth_fastapi.py
auth/google_oauth_flask.py
auth/jwt_helpers.py
```

---

### `snack search`

Searches snippet filenames (not file contents) for a keyword. Case-insensitive.

```bash
snack search oauth
```

Output:

```
auth/google_oauth_fastapi.py
auth/google_oauth_flask.py
```

---

### `snack unpack`

Copies a snippet **from the stash** into the **current working directory**.

```bash
snack unpack auth/google_oauth_fastapi.py
```

The path is relative to the stash root. Use `snack list` or `snack search` to find the correct path.

#### Flags

| Flag | Description |
|---|---|
| `--flat` | Copy the file directly into the current directory, discarding subdirectory structure |
| `--force` | Overwrite an existing file without prompting |

#### Default (preserves structure)

```bash
cd ~/projects/my-app
snack unpack auth/google_oauth_fastapi.py
# Creates: ./auth/google_oauth_fastapi.py
```

#### `--flat`

```bash
snack unpack auth/google_oauth_fastapi.py --flat
# Creates: ./google_oauth_fastapi.py
```

#### Overwrite prompt

If the destination file already exists:

```
'./auth/google_oauth_fastapi.py' already exists. Overwrite? [y/N]:
```

Pass `--force` to skip the prompt.

---

### `snack pack`

Copies a file **from the current working directory** into the stash. Use this when you have improved a snippet during a project and want to update the canonical version.

```bash
snack pack auth/google_oauth_fastapi.py
```

The path is relative to the current working directory and is used as-is inside the stash.

#### Flags

| Flag | Description |
|---|---|
| `--force` | Overwrite an existing stash file without prompting |

---

## Stash management commands

### `snack stash create`

Registers a new named stash directory and creates it on disk if it doesn't already exist.

```bash
snack stash create default ~/snack-stash
snack stash create work ~/work-stash
snack stash create work ~/work-stash --no-activate
```

The first stash created is automatically set as active. For subsequent stashes, use `--activate` (the default) to switch, or `--no-activate` to add without switching.

#### Flags

| Flag | Default | Description |
|---|---|---|
| `--activate` / `--no-activate` | `--activate` | Whether to set this as the active stash |

---

### `snack stash list`

Shows all configured stashes with their paths, marking the active one.

```bash
snack stash list
```

Output:

```
  default  /Users/you/snack-stash  ← active
  work     /Users/you/work-stash
```

If a stash path no longer exists on disk, it is flagged:

```
  default  /Users/you/snack-stash  ← active  [path missing!]
```

If `SNACK_STASH` env var is set, a note is shown at the bottom indicating it is overriding the active stash.

---

### `snack stash move`

Moves a stash directory to a new location on disk and updates the path in `~/.snackstashrc`.

```bash
snack stash move default ~/new-location/snack-stash
```

- The old directory and all its contents are moved to the new path
- The config is updated automatically
- If the old path no longer exists on disk, the new directory is created instead
- Errors if the new path already exists (to prevent accidental overwrites)

---

### `snack stash add-remote`

Downloads a public GitHub repository as a tarball and copies all `.py` files into the active stash, preserving directory structure.

```bash
snack stash add-remote owner/repo
snack stash add-remote https://github.com/owner/repo
```

#### Filter by subdirectory

Only copy files from a specific subdirectory of the repo:

```bash
snack stash add-remote owner/repo --subdir auth
```

This copies `auth/google_oauth.py` from the repo as `auth/google_oauth.py` in the stash (the full path is preserved).

#### Flags

| Flag | Description |
|---|---|
| `--subdir <dir>` | Only copy files under this subdirectory of the repo |
| `--force` | Overwrite existing stash files without prompting |

#### Accepted repo formats

- `owner/repo`
- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`

Non-Python files (`.md`, `.txt`, etc.) are never copied.
