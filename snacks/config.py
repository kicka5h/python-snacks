import configparser
import os
from pathlib import Path
from typing import Optional

import typer

CONFIG_PATH = Path("~/.snackstashrc").expanduser()


class SnackConfig:
    """Read/write ~/.snackstashrc.

    New format (INI):
        [config]
        active = default

        [stash.default]
        path = ~/snack-stash

    Legacy format (still read, never written):
        stash=~/snack-stash
    """

    def __init__(self) -> None:
        self._cp = configparser.ConfigParser()
        self._legacy_path: Optional[Path] = None

        if not CONFIG_PATH.exists():
            return

        content = CONFIG_PATH.read_text().strip()
        if not content:
            return

        if not content.lstrip().startswith("["):
            # Legacy sectionless format
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("stash="):
                    self._legacy_path = Path(line[len("stash="):].strip()).expanduser()
                    break
        else:
            self._cp.read_string(content)

    # ── read ────────────────────────────────────────────────────────────────

    @property
    def is_legacy(self) -> bool:
        return self._legacy_path is not None

    @property
    def legacy_path(self) -> Optional[Path]:
        return self._legacy_path

    def active_name(self) -> Optional[str]:
        return self._cp.get("config", "active", fallback=None)

    def stashes(self) -> dict[str, Path]:
        return {
            section[len("stash."):]: Path(self._cp[section]["path"]).expanduser()
            for section in self._cp.sections()
            if section.startswith("stash.")
        }

    def stash_path(self, name: str) -> Optional[Path]:
        section = f"stash.{name}"
        if section in self._cp and "path" in self._cp[section]:
            return Path(self._cp[section]["path"]).expanduser()
        return None

    def has_stash(self, name: str) -> bool:
        return f"stash.{name}" in self._cp

    # ── write ───────────────────────────────────────────────────────────────

    def set_stash(self, name: str, path: Path) -> None:
        if "config" not in self._cp:
            self._cp["config"] = {}
        self._cp[f"stash.{name}"] = {"path": str(path)}

    def set_active(self, name: str) -> None:
        if "config" not in self._cp:
            self._cp["config"] = {}
        self._cp["config"]["active"] = name

    def remove_stash(self, name: str) -> bool:
        return self._cp.remove_section(f"stash.{name}")

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            self._cp.write(f)


def get_stash_path() -> Path:
    """Resolve the active stash directory. Raises Exit(1) on any error."""
    # Env var overrides everything
    env_val = os.environ.get("SNACK_STASH")
    if env_val:
        path = Path(env_val).expanduser()
        if not path.exists():
            typer.echo(
                f"[error] SNACK_STASH is set to '{env_val}' but that path does not exist.",
                err=True,
            )
            raise typer.Exit(1)
        return path

    cfg = SnackConfig()

    # Legacy format
    if cfg.is_legacy:
        path = cfg.legacy_path
        if not path.exists():
            typer.echo(
                f"[error] stash path in ~/.snackstashrc ('{path}') does not exist.",
                err=True,
            )
            raise typer.Exit(1)
        return path

    # Multi-stash: use active
    active = cfg.active_name()
    if active:
        path = cfg.stash_path(active)
        if path is None:
            typer.echo(
                f"[error] Active stash '{active}' is not defined in config.",
                err=True,
            )
            raise typer.Exit(1)
        if not path.exists():
            typer.echo(
                f"[error] Active stash '{active}' path '{path}' does not exist.",
                err=True,
            )
            raise typer.Exit(1)
        return path

    typer.echo(
        "[error] Snack stash location is not configured.\n"
        "Create a stash with:\n"
        "  snack stash create default ~/snack-stash\n"
        "Or set the SNACK_STASH environment variable:\n"
        "  export SNACK_STASH=~/snack-stash",
        err=True,
    )
    raise typer.Exit(1)
