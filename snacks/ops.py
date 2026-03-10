import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import typer


def unpack(stash: Path, snippet_path: str, flat: bool, force: bool) -> None:
    """Copy a file from the stash into the current working directory."""
    src = stash / snippet_path
    if not src.exists():
        typer.echo(f"[error] '{snippet_path}' not found in stash ({stash}).", err=True)
        raise typer.Exit(1)

    dest = Path.cwd() / (src.name if flat else snippet_path)
    _copy(src, dest, force)
    typer.echo(f"Unpacked {snippet_path} → {dest}")


def pack(stash: Path, snippet_path: str, force: bool) -> None:
    """Copy a file from the current working directory into the stash."""
    src = Path.cwd() / snippet_path
    if not src.exists():
        typer.echo(f"[error] '{snippet_path}' not found in current directory.", err=True)
        raise typer.Exit(1)

    dest = stash / snippet_path
    _copy(src, dest, force)
    typer.echo(f"Packed {snippet_path} → {dest}")


def add_remote(stash: Path, repo: str, subdir: Optional[str], force: bool) -> None:
    """Download .py files from a GitHub repo into the stash."""
    owner, repo_name = _parse_github_repo(repo)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/tarball"

    typer.echo(f"Fetching {owner}/{repo_name}...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "snack-stash", "Accept": "application/vnd.github+json"},
    )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            tarball = tmp / "repo.tar.gz"

            with urllib.request.urlopen(req) as response:
                tarball.write_bytes(response.read())

            extract_dir = tmp / "repo"
            extract_dir.mkdir()
            with tarfile.open(tarball) as tf:
                try:
                    tf.extractall(extract_dir, filter="data")
                except TypeError:
                    tf.extractall(extract_dir)  # Python < 3.12

            roots = list(extract_dir.iterdir())
            if not roots:
                typer.echo("[error] Downloaded archive was empty.", err=True)
                raise typer.Exit(1)
            repo_root = roots[0]

            py_files = sorted(
                p for p in repo_root.rglob("*.py")
                if subdir is None or _is_under_subdir(p.relative_to(repo_root), subdir)
            )

            if not py_files:
                msg = "No Python files found"
                if subdir:
                    msg += f" under '{subdir}'"
                typer.echo(msg + ".")
                return

            for src in py_files:
                rel = src.relative_to(repo_root)
                _copy(src, stash / rel, force)
                typer.echo(f"  + {rel.as_posix()}")

            typer.echo(f"\nAdded {len(py_files)} file(s) from {owner}/{repo_name}.")

    except urllib.error.HTTPError as e:
        typer.echo(f"[error] HTTP {e.code}: {e.reason}", err=True)
        raise typer.Exit(1)
    except urllib.error.URLError as e:
        typer.echo(f"[error] Network error: {e.reason}", err=True)
        raise typer.Exit(1)


def _parse_github_repo(repo: str) -> tuple[str, str]:
    repo = repo.strip().rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if repo.startswith(prefix):
            repo = repo[len(prefix):]
            break
    if repo.endswith(".git"):
        repo = repo[:-4]
    parts = repo.split("/")
    if len(parts) != 2 or not all(parts):
        typer.echo(
            f"[error] Invalid repo '{repo}'. Use 'owner/repo' or a full GitHub URL.",
            err=True,
        )
        raise typer.Exit(1)
    return parts[0], parts[1]


def _is_under_subdir(rel: Path, subdir: str) -> bool:
    target = tuple(Path(subdir.strip("/")).parts)
    return rel.parts[: len(target)] == target


def _copy(src: Path, dest: Path, force: bool) -> None:
    if dest.exists() and not force:
        overwrite = typer.confirm(f"'{dest}' already exists. Overwrite?")
        if not overwrite:
            typer.echo("Aborted.")
            raise typer.Exit(0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
