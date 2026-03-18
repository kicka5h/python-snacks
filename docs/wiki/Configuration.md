# Configuration

Snack Stash supports multiple named stashes. The active stash is used by all snippet commands (`list`, `search`, `unpack`, `pack`).

## Priority Order

1. `SNACK_STASH` environment variable (overrides everything)
2. Active stash in `~/.snackstashrc`
3. Error — nothing is configured

---

## Method 1: Named stashes (recommended)

Use `snack stash create` to register stashes. This is the standard workflow and requires no manual config editing.

```bash
# Create your first stash (auto-activated)
snack stash create default ~/snack-stash

# Add a second stash without switching to it
snack stash create work ~/work-stash --no-activate

# See what's configured
snack stash list
#   default  /Users/you/snack-stash  ← active
#   work     /Users/you/work-stash
```

This writes `~/.snackstashrc` in INI format:

```ini
[config]
active = default

[stash.default]
path = /Users/you/snack-stash

[stash.work]
path = /Users/you/work-stash
```

You can edit this file by hand if needed.

---

## Method 2: Environment variable

Set `SNACK_STASH` to override the config file entirely. Useful for scripts, CI, or quickly switching context.

```bash
export SNACK_STASH=~/snack-stash
```

Add to `~/.zshrc` or `~/.bashrc` to make it permanent:

```bash
echo 'export SNACK_STASH=~/snack-stash' >> ~/.zshrc
```

When `SNACK_STASH` is set, named stashes in the config file are ignored for all snippet commands. `snack stash list` will still display configured stashes but will note the override.

---

## Stash directory structure

A stash is a plain directory of `.py` files, organized into subdirectories by category. No special files or metadata are required.

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

The directory can be managed with Git, Dropbox, or any other sync mechanism independently of this tool. Syncing is outside the scope of `snack` — it only copies files in and out.

---

## Switching the active stash

To change which named stash is active, create a new one with `--activate` or edit `~/.snackstashrc` directly and update the `active` key under `[config]`.

---

## Verifying your configuration

```bash
snack stash list    # see all stashes and which is active
snack list          # confirm the active stash has snippets
```

See [[Error-Reference]] for help with configuration errors.
