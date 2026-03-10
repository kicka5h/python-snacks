# Writing Good Snippets

A snippet is only as useful as it is reusable. These guidelines help you write snippets that are easy to drop into any project and immediately understand.

---

## The core principle: self-containment

A snippet should work correctly after a single `cp` into a new project. That means:

- All imports are explicit and at the top of the file
- All configuration comes from parameters or environment variables — never hardcoded values
- No assumptions about what else exists in the project
- No side effects at import time (wrap executable code in functions or `if __name__ == "__main__"`)

If unpacking a snippet requires you to also copy another file, refactor until it doesn't.

---

## Use a standard header

The single most useful habit is a consistent docstring that captures three things: what the snippet does, what it depends on, and how to use it. Anyone (including future you) can read this without opening the file.

```python
"""Send transactional email via SMTP.

Dependencies:
    stdlib only

Usage:
    from email.smtp_sender import send_email
    send_email(to="user@example.com", subject="Hello", body="<p>World</p>")

Config (env vars):
    SMTP_HOST     — mail server hostname
    SMTP_PORT     — defaults to 587
    SMTP_USER     — sender login
    SMTP_PASSWORD — sender password
"""
```

Keep it short. The goal is a five-second orientation, not full API documentation.

---

## Name files to be searchable

Filenames are the primary search surface — `snack search` matches against them. Choose names that are specific and predictable.

**Good:**
```
auth/google_oauth_fastapi.py
auth/google_oauth_flask.py
forms/contact_form_wtf.py
email/smtp_sender.py
storage/s3_upload.py
```

**Avoid:**
```
auth/helpers.py       # too vague
auth/utils.py         # tells you nothing
auth/new_version.py   # not a meaningful name
```

When a snippet has framework-specific variants, use a suffix: `_fastapi`, `_flask`, `_django`, `_sqlalchemy`. This makes `snack search fastapi` return only what's relevant.

---

## One file, one job

Resist the urge to bundle related utilities into a single file. A snippet called `auth_helpers.py` that contains OAuth, JWT, and session logic will only ever be partially useful. Three focused snippets are more valuable than one large one.

The right size for a snippet is: "I need exactly this, and I copy exactly this."

---

## Organise by what a project needs, not by technical category

Think about how you reach for snippets when starting a project. Categories like `auth/`, `forms/`, `email/`, `storage/`, `payments/` map to features. Categories like `decorators/` or `metaclasses/` map to implementation details and are harder to browse purposefully.

```
~/snack-stash/
├── auth/           # authentication and authorisation
├── email/          # sending and templating emails
├── forms/          # form handling and validation
├── payments/       # Stripe, etc.
├── storage/        # file uploads, S3, local disk
└── tasks/          # background jobs, queues
```

---

## Keep configuration out of the code

Configuration that varies per-project (API keys, hostnames, feature flags) should be read from environment variables or passed as function arguments. Never commit a snippet with hardcoded credentials or URLs.

```python
# Good — caller provides credentials
def create_oauth_client(client_id: str, client_secret: str) -> OAuth2Session:
    ...

# Good — reads from environment
STRIPE_KEY = os.environ["STRIPE_SECRET_KEY"]

# Bad — hardcoded
STRIPE_KEY = "sk_live_abc123"
```

---

## Update the stash when you improve a snippet

The stash is most valuable when it reflects your current best practice, not the version from two years ago. When you improve a snippet during a project, pack it back:

```bash
snack pack auth/google_oauth_fastapi.py
```

If you manage your stash as a Git repo, commit the improvement there too. The stash stays useful only if it gets maintained like any other codebase.
