from __future__ import annotations

import importlib.metadata
import os
import shutil
from pathlib import Path
from typing import Optional

import typer

from snacks.config import SnackConfig, get_stash_path
from snacks.ops import add_remote as do_add_remote
from snacks.ops import pack as do_pack, unpack as do_unpack

app = typer.Typer(
    name="snack",
    help="Manage your personal snack stash of reusable Python snippets.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        version = importlib.metadata.version("snack-stash")
        typer.echo(f"snack-stash v{version}")
        raise typer.Exit()


@app.callback()
def _main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
) -> None:
    pass

stash_app = typer.Typer(help="Manage stash directories.")
app.add_typer(stash_app, name="stash")


# ── snippet commands ─────────────────────────────────────────────────────────

@app.command()
def unpack(
    snippet: str = typer.Argument(..., help="Path relative to the stash root (e.g. auth/google_oauth.py)"),
    flat: bool = typer.Option(False, "--flat", help="Copy file into cwd without preserving subdirectory structure."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files without prompting."),
) -> None:
    """Copy a snippet FROM the stash INTO the current working directory."""
    do_unpack(get_stash_path(), snippet, flat=flat, force=force)


@app.command()
def pack(
    snippet: str = typer.Argument(..., help="Path relative to cwd (e.g. auth/google_oauth.py)"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing stash file without prompting."),
) -> None:
    """Copy a snippet FROM the current working directory INTO the stash."""
    do_pack(get_stash_path(), snippet, force=force)


@app.command(name="list")
def list_snacks(
    category: Optional[str] = typer.Argument(None, help="Filter by category (subdirectory name)."),
) -> None:
    """List all snippets in the stash."""
    stash = get_stash_path()
    snippets = sorted(
        p.relative_to(stash).as_posix()
        for p in stash.rglob("*.py")
        if not p.name.startswith("_")
    )
    if category:
        snippets = [s for s in snippets if s.startswith(f"{category}/")]
    typer.echo("\n".join(snippets) if snippets else "No snippets found.")


@app.command()
def search(
    keyword: str = typer.Argument(..., help="Keyword to search for in snippet filenames."),
) -> None:
    """Search snippet filenames for a keyword."""
    stash = get_stash_path()
    matches = sorted(
        p.relative_to(stash).as_posix()
        for p in stash.rglob("*.py")
        if keyword.lower() in p.name.lower() and not p.name.startswith("_")
    )
    typer.echo("\n".join(matches) if matches else f"No snippets matching '{keyword}'.")


# ── stash management commands ────────────────────────────────────────────────

@stash_app.command("create")
def stash_create(
    name: str = typer.Argument(..., help="Name for the new stash (e.g. 'default', 'work')."),
    path: Path = typer.Argument(..., help="Directory path for the new stash."),
    activate: bool = typer.Option(True, "--activate/--no-activate", help="Set as the active stash."),
) -> None:
    """Create a new stash directory and register it in config."""
    cfg = SnackConfig()
    if cfg.has_stash(name):
        typer.echo(f"[error] A stash named '{name}' already exists.", err=True)
        raise typer.Exit(1)

    is_first = len(cfg.stashes()) == 0
    expanded = path.expanduser().resolve()
    expanded.mkdir(parents=True, exist_ok=True)
    cfg.set_stash(name, expanded)

    if activate or is_first:
        cfg.set_active(name)

    cfg.save()
    typer.echo(f"Created stash '{name}' at {expanded}.")
    if activate or is_first:
        typer.echo(f"Active stash → '{name}'.")


@stash_app.command("list")
def stash_list() -> None:
    """List all configured stashes."""
    cfg = SnackConfig()
    env_val = os.environ.get("SNACK_STASH")

    if cfg.is_legacy:
        typer.echo(f"  (legacy)  {cfg.legacy_path}  ← active")
        return

    stashes = cfg.stashes()
    if not stashes:
        typer.echo(
            "No stashes configured. Create one with:\n"
            "  snack stash create <name> <path>"
        )
        return

    active = cfg.active_name()
    width = max(len(n) for n in stashes)
    for name, stash_path in sorted(stashes.items()):
        marker = " ← active" if name == active else ""
        missing = " [path missing!]" if not stash_path.exists() else ""
        typer.echo(f"  {name:<{width}}  {stash_path}{marker}{missing}")

    if env_val:
        typer.echo(f"\n  Note: SNACK_STASH env var is set and overrides the active stash.")


@stash_app.command("move")
def stash_move(
    name: str = typer.Argument(..., help="Name of the stash to move."),
    new_path: Path = typer.Argument(..., help="New directory path."),
) -> None:
    """Move a stash to a new location and update config."""
    cfg = SnackConfig()
    if not cfg.has_stash(name):
        typer.echo(
            f"[error] No stash named '{name}'. Run 'snack stash list' to see available stashes.",
            err=True,
        )
        raise typer.Exit(1)

    old_path = cfg.stash_path(name)
    expanded_new = new_path.expanduser().resolve()

    if expanded_new.exists() and expanded_new != old_path:
        typer.echo(f"[error] '{expanded_new}' already exists.", err=True)
        raise typer.Exit(1)

    if old_path.exists():
        shutil.move(str(old_path), str(expanded_new))
        typer.echo(f"Moved '{name}': {old_path} → {expanded_new}")
    else:
        expanded_new.mkdir(parents=True, exist_ok=True)
        typer.echo(f"Old path {old_path} did not exist. Created {expanded_new}.")

    cfg.set_stash(name, expanded_new)
    cfg.save()


@stash_app.command("add-remote")
def stash_add_remote(
    repo: str = typer.Argument(..., help="GitHub repo as 'owner/repo' or a full GitHub URL."),
    subdir: Optional[str] = typer.Option(None, "--subdir", help="Only copy files from this subdirectory of the repo."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files without prompting."),
) -> None:
    """Copy Python snippets from a GitHub repository into the active stash."""
    do_add_remote(get_stash_path(), repo, subdir=subdir, force=force)
