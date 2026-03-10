"""GitHub authentication for snack CLI.

Resolution order:
1. GITHUB_TOKEN env var (useful for CI)
2. `gh auth token` (GitHub CLI, if installed and logged in)
3. GitHub OAuth device flow (prompts user in browser)
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

import typer

# Register at https://github.com/settings/apps/new (Device Flow, no client secret needed)
_CLIENT_ID = os.environ.get("SNACK_GITHUB_CLIENT_ID", "")


def get_github_token() -> Optional[str]:
    """Return a GitHub token, prompting via device flow if needed."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    token = _token_from_gh_cli()
    if token:
        return token

    return _device_flow()


def _token_from_gh_cli() -> Optional[str]:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _device_flow() -> Optional[str]:
    if not _CLIENT_ID:
        typer.echo(
            "[error] No GitHub client ID configured. "
            "Set SNACK_GITHUB_CLIENT_ID or GITHUB_TOKEN to authenticate.",
            err=True,
        )
        raise typer.Exit(1)

    # Step 1 — request device + user code
    data = urllib.parse.urlencode({"client_id": _CLIENT_ID, "scope": "repo"}).encode()
    req = urllib.request.Request(
        "https://github.com/login/device/code",
        data=data,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read())
    except urllib.error.URLError as e:
        typer.echo(f"[error] Could not reach GitHub: {e.reason}", err=True)
        raise typer.Exit(1)

    device_code = payload["device_code"]
    user_code = payload["user_code"]
    verification_uri = payload["verification_uri"]
    interval = payload.get("interval", 5)
    expires_in = payload.get("expires_in", 900)

    typer.echo(f"\nOpen: {verification_uri}")
    typer.echo(f"Code: {user_code}\n")

    # Step 2 — poll until the user approves
    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)

        data = urllib.parse.urlencode({
            "client_id": _CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }).encode()
        req = urllib.request.Request(
            "https://github.com/login/oauth/access_token",
            data=data,
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())

        if "access_token" in result:
            typer.echo("Authenticated.")
            return result["access_token"]

        error = result.get("error")
        if error == "slow_down":
            interval += 5
        elif error != "authorization_pending":
            typer.echo(f"[error] Authentication failed: {error}", err=True)
            raise typer.Exit(1)

    typer.echo("[error] Authentication timed out.", err=True)
    raise typer.Exit(1)
