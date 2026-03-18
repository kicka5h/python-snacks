# Error Reference

## Stash not configured

**Message:**
```
[error] Snack stash location is not configured.
Create a stash with:
  snack stash create default ~/snack-stash
Or set the SNACK_STASH environment variable:
  export SNACK_STASH=~/snack-stash
```

**Cause:** No stash has been created and `SNACK_STASH` is not set.

**Fix:** Run `snack stash create default ~/snack-stash` to get started. See [[Configuration]] for full details.

---

## Stash path does not exist

**Message:**
```
[error] SNACK_STASH is set to '/path/to/stash' but that path does not exist.
```

or

```
[error] Active stash 'default' path '/path/to/stash' does not exist.
```

**Cause:** The configured path is not present on disk. Common reasons:
- The directory was moved or deleted manually (use `snack stash move` instead)
- A typo in the path
- The drive or volume it lives on is not mounted

**Fix:** Either recreate the directory, correct the path in `~/.snackstashrc`, or run `snack stash move` to point the stash to its new location.

---

## Snippet not found in stash (`unpack`)

**Message:**
```
[error] 'auth/nope.py' not found in stash (/path/to/stash).
```

**Cause:** The path passed to `snack unpack` does not exist in the stash.

**Fix:** Use `snack list` or `snack search` to find the correct path:

```bash
snack list auth
snack search oauth
```

---

## Source file not found (`pack`)

**Message:**
```
[error] 'auth/google_oauth.py' not found in current directory.
```

**Cause:** The file passed to `snack pack` does not exist relative to the current working directory.

**Fix:** Check your working directory and the path you provided:

```bash
pwd
ls auth/
```

---

## Overwrite conflict

**Message:**
```
'/path/to/file.py' already exists. Overwrite? [y/N]:
```

**Cause:** The destination file already exists. Applies to `snack unpack`, `snack pack`, and `snack stash add-remote`.

**Fix:**
- Answer `y` at the prompt to overwrite
- Answer `n` (or press Enter) to abort
- Pass `--force` to skip the prompt:

```bash
snack unpack auth/google_oauth.py --force
snack pack auth/google_oauth.py --force
snack stash add-remote owner/repo --force
```

---

## Stash name already exists (`stash create`)

**Message:**
```
[error] A stash named 'default' already exists.
```

**Cause:** You ran `snack stash create` with a name that is already registered in `~/.snackstashrc`.

**Fix:** Choose a different name, or edit `~/.snackstashrc` directly to remove the existing entry first.

---

## Unknown stash name (`stash move`)

**Message:**
```
[error] No stash named 'foo'. Run 'snack stash list' to see available stashes.
```

**Cause:** The name passed to `snack stash move` is not registered in `~/.snackstashrc`.

**Fix:** Run `snack stash list` to see valid names.

---

## Move target already exists (`stash move`)

**Message:**
```
[error] '/new/path' already exists.
```

**Cause:** The destination path for `snack stash move` is already present on disk.

**Fix:** Choose a different target path, or remove the existing directory first if it is safe to do so.

---

## GitHub repo not found or inaccessible (`stash add-remote`)

**Message:**
```
[error] HTTP 404: Not Found
```

**Cause:** The repository does not exist, is private, or the URL is incorrect.

**Fix:** Check the repo name and ensure it is public. Private repos are not supported without a token (which is not currently a supported feature).

---

## Invalid repo format (`stash add-remote`)

**Message:**
```
[error] Invalid repo 'not-a-repo'. Use 'owner/repo' or a full GitHub URL.
```

**Cause:** The argument passed to `snack stash add-remote` could not be parsed.

**Fix:** Use one of the supported formats:

```bash
snack stash add-remote owner/repo
snack stash add-remote https://github.com/owner/repo
```
