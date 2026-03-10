"""Tests for `snack stash *` commands."""
import io
import os
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

local_only = pytest.mark.skipif(os.environ.get("CI") == "true", reason="local only")

import snacks.config as config_module
from snacks.main import app

runner = CliRunner()


@pytest.fixture()
def cfg_file(tmp_path, monkeypatch):
    """Redirect CONFIG_PATH to a temp file so tests never touch ~/.snackstashrc."""
    p = tmp_path / "snackstashrc"
    monkeypatch.setattr(config_module, "CONFIG_PATH", p)
    return p


# ── stash create ─────────────────────────────────────────────────────────────

def test_stash_create_makes_dir(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    result = runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    assert result.exit_code == 0, result.output
    assert stash_dir.exists()
    assert "Created stash 'default'" in result.output


def test_stash_create_writes_config(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    assert cfg_file.exists()
    content = cfg_file.read_text()
    assert "stash.default" in content
    assert str(stash_dir) in content


def test_stash_create_first_is_auto_active(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    result = runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    assert "Active stash" in result.output
    content = cfg_file.read_text()
    assert "active = default" in content


def test_stash_create_no_activate_flag(cfg_file, tmp_path):
    # First stash: auto-activated regardless of --no-activate (it's the only one)
    first = tmp_path / "first"
    runner.invoke(app, ["stash", "create", "first", str(first)], env={})
    # Second stash with --no-activate should not become active
    second = tmp_path / "second"
    runner.invoke(app, ["stash", "create", "second", str(second), "--no-activate"], env={})
    content = cfg_file.read_text()
    assert "active = first" in content


def test_stash_create_duplicate_name_errors(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    result = runner.invoke(app, ["stash", "create", "default", str(tmp_path / "other")], env={})
    assert result.exit_code != 0
    assert "already exists" in result.output


# ── stash list ───────────────────────────────────────────────────────────────

def test_stash_list_empty(cfg_file):
    result = runner.invoke(app, ["stash", "list"], env={})
    assert result.exit_code == 0
    assert "No stashes configured" in result.output


def test_stash_list_shows_stashes(cfg_file, tmp_path):
    a = tmp_path / "stash-a"
    b = tmp_path / "stash-b"
    runner.invoke(app, ["stash", "create", "alpha", str(a)], env={})
    runner.invoke(app, ["stash", "create", "beta", str(b), "--no-activate"], env={})
    result = runner.invoke(app, ["stash", "list"], env={})
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output
    assert "← active" in result.output


def test_stash_list_missing_path_flagged(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    stash_dir.rmdir()
    result = runner.invoke(app, ["stash", "list"], env={})
    assert "path missing" in result.output


# ── stash move ───────────────────────────────────────────────────────────────

def test_stash_move_relocates_directory(cfg_file, tmp_path):
    old = tmp_path / "old-stash"
    (old / "auth").mkdir(parents=True)
    (old / "auth" / "helper.py").write_text("# helper\n")
    runner.invoke(app, ["stash", "create", "default", str(old)], env={})

    new = tmp_path / "new-stash"
    result = runner.invoke(app, ["stash", "move", "default", str(new)], env={})
    assert result.exit_code == 0, result.output
    assert not old.exists()
    assert (new / "auth" / "helper.py").exists()


def test_stash_move_updates_config(cfg_file, tmp_path):
    old = tmp_path / "old-stash"
    old.mkdir()
    runner.invoke(app, ["stash", "create", "default", str(old)], env={})

    new = tmp_path / "new-stash"
    runner.invoke(app, ["stash", "move", "default", str(new)], env={})
    content = cfg_file.read_text()
    assert str(new) in content
    assert str(old) not in content


def test_stash_move_unknown_name_errors(cfg_file, tmp_path):
    result = runner.invoke(app, ["stash", "move", "nonexistent", str(tmp_path / "x")], env={})
    assert result.exit_code != 0
    assert "No stash named" in result.output


def test_stash_move_target_exists_errors(cfg_file, tmp_path):
    old = tmp_path / "old"
    old.mkdir()
    existing = tmp_path / "existing"
    existing.mkdir()
    runner.invoke(app, ["stash", "create", "default", str(old)], env={})
    result = runner.invoke(app, ["stash", "move", "default", str(existing)], env={})
    assert result.exit_code != 0
    assert "already exists" in result.output


# ── stash delete ─────────────────────────────────────────────────────────────

def test_stash_delete_removes_from_config(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    result = runner.invoke(app, ["stash", "delete", "default"], env={})
    assert result.exit_code == 0, result.output
    assert "Deleted stash 'default'" in result.output
    assert "stash.default" not in cfg_file.read_text()


def test_stash_delete_does_not_remove_files(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    runner.invoke(app, ["stash", "delete", "default"], env={})
    assert stash_dir.exists()


def test_stash_delete_unknown_name_errors(cfg_file):
    result = runner.invoke(app, ["stash", "delete", "nonexistent"], env={})
    assert result.exit_code != 0
    assert "No stash named" in result.output


def test_stash_delete_active_promotes_next(cfg_file, tmp_path):
    a = tmp_path / "stash-a"
    b = tmp_path / "stash-b"
    runner.invoke(app, ["stash", "create", "alpha", str(a)], env={})
    runner.invoke(app, ["stash", "create", "beta", str(b), "--no-activate"], env={})
    result = runner.invoke(app, ["stash", "delete", "alpha"], env={})
    assert result.exit_code == 0
    assert "beta" in result.output
    assert "active = beta" in cfg_file.read_text()


def test_stash_delete_last_stash_leaves_no_active(cfg_file, tmp_path):
    stash_dir = tmp_path / "my-stash"
    runner.invoke(app, ["stash", "create", "default", str(stash_dir)], env={})
    result = runner.invoke(app, ["stash", "delete", "default"], env={})
    assert result.exit_code == 0
    assert "No stashes remaining" in result.output


# ── stash add-remote ─────────────────────────────────────────────────────────

def _make_tarball(files: dict[str, str]) -> bytes:
    """Build an in-memory tar.gz with the given {path: content} files.
    Wrapped in a top-level 'owner-repo-abc123/' directory, like GitHub does."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for rel_path, content in files.items():
            full_path = f"owner-repo-abc123/{rel_path}"
            data = content.encode()
            info = tarfile.TarInfo(name=full_path)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


@pytest.fixture()
def remote_stash(tmp_path_factory):
    return tmp_path_factory.mktemp("remote-stash")


@pytest.fixture()
def remote_stash_env(remote_stash):
    return {"SNACK_STASH": str(remote_stash)}


def _mock_urlopen(tarball_bytes: bytes):
    response = MagicMock()
    response.read.return_value = tarball_bytes
    response.__enter__ = lambda s: s
    response.__exit__ = MagicMock(return_value=False)
    return response


def test_add_remote_copies_py_files(remote_stash, remote_stash_env):
    tarball = _make_tarball({
        "auth/google_oauth.py": "# oauth\n",
        "forms/contact.py": "# contact\n",
        "README.md": "# readme",
    })
    mock_response = _mock_urlopen(tarball)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = runner.invoke(
            app, ["stash", "add-remote", "owner/repo"], env=remote_stash_env
        )
    assert result.exit_code == 0, result.output
    assert (remote_stash / "auth" / "google_oauth.py").exists()
    assert (remote_stash / "forms" / "contact.py").exists()
    assert not (remote_stash / "README.md").exists()


def test_add_remote_subdir_filter(remote_stash, remote_stash_env):
    tarball = _make_tarball({
        "auth/google_oauth.py": "# oauth\n",
        "forms/contact.py": "# contact\n",
    })
    mock_response = _mock_urlopen(tarball)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = runner.invoke(
            app, ["stash", "add-remote", "owner/repo", "--subdir", "auth"],
            env=remote_stash_env,
        )
    assert result.exit_code == 0, result.output
    assert (remote_stash / "auth" / "google_oauth.py").exists()
    assert not (remote_stash / "forms").exists()


def test_add_remote_github_url_accepted(remote_stash, remote_stash_env):
    tarball = _make_tarball({"utils/helpers.py": "# helpers\n"})
    mock_response = _mock_urlopen(tarball)
    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        runner.invoke(
            app,
            ["stash", "add-remote", "https://github.com/owner/repo"],
            env=remote_stash_env,
        )
    called_url = mock_open.call_args[0][0].full_url
    assert "owner/repo" in called_url


def test_add_remote_invalid_repo_errors(remote_stash_env):
    result = runner.invoke(
        app, ["stash", "add-remote", "not-a-valid-repo"], env=remote_stash_env
    )
    assert result.exit_code != 0
    assert "Invalid repo" in result.output


def test_add_remote_http_error(remote_stash_env):
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="", code=500, msg="Internal Server Error", hdrs=None, fp=None
    )):
        result = runner.invoke(
            app, ["stash", "add-remote", "owner/repo"], env=remote_stash_env
        )
    assert result.exit_code != 0
    assert "500" in result.output


def test_add_remote_not_found_after_auth(remote_stash_env):
    """Repo not found even after authentication — should report 404."""
    import urllib.error
    not_found = urllib.error.HTTPError(url="", code=404, msg="Not Found", hdrs=None, fp=None)
    with patch("urllib.request.urlopen", side_effect=not_found), \
         patch("snacks.auth._token_from_gh_cli", return_value="ghp_token"):
        result = runner.invoke(
            app, ["stash", "add-remote", "owner/missing-repo"], env=remote_stash_env
        )
    assert result.exit_code != 0
    assert "404" in result.output


def test_add_remote_public_repo_needs_no_auth(remote_stash, remote_stash_env):
    tarball = _make_tarball({"auth/oauth.py": "# oauth\n"})
    mock_response = _mock_urlopen(tarball)
    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        result = runner.invoke(app, ["stash", "add-remote", "owner/repo"], env=remote_stash_env)
    assert result.exit_code == 0
    req = mock_open.call_args[0][0]
    assert req.get_header("Authorization") is None


@local_only
def test_add_remote_private_repo_retries_with_gh_token(remote_stash, remote_stash_env):
    """On 404, auth via gh CLI and retry."""
    import urllib.error
    tarball = _make_tarball({"auth/oauth.py": "# oauth\n"})
    not_found = urllib.error.HTTPError(url="", code=404, msg="Not Found", hdrs=None, fp=None)
    auth_response = _mock_urlopen(tarball)

    with patch("urllib.request.urlopen", side_effect=[not_found, auth_response]), \
         patch("snacks.auth._token_from_gh_cli", return_value="ghp_cli_token"):
        result = runner.invoke(app, ["stash", "add-remote", "owner/private-repo"], env=remote_stash_env)

    assert result.exit_code == 0
    assert (remote_stash / "auth" / "oauth.py").exists()


@local_only
def test_add_remote_private_repo_uses_github_token_env(remote_stash, remote_stash_env):
    """GITHUB_TOKEN env var is used without prompting."""
    import urllib.error
    tarball = _make_tarball({"auth/oauth.py": "# oauth\n"})
    not_found = urllib.error.HTTPError(url="", code=404, msg="Not Found", hdrs=None, fp=None)
    auth_response = _mock_urlopen(tarball)

    env = {**remote_stash_env, "GITHUB_TOKEN": "ghp_envtoken"}
    with patch("urllib.request.urlopen", side_effect=[not_found, auth_response]) as mock_open:
        result = runner.invoke(app, ["stash", "add-remote", "owner/private-repo"], env=env)

    assert result.exit_code == 0
    final_req = mock_open.call_args[0][0]
    assert final_req.get_header("Authorization") == "Bearer ghp_envtoken"


def test_add_remote_no_py_files(remote_stash, remote_stash_env):
    tarball = _make_tarball({"README.md": "# readme"})
    mock_response = _mock_urlopen(tarball)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = runner.invoke(
            app, ["stash", "add-remote", "owner/repo"], env=remote_stash_env
        )
    assert result.exit_code == 0
    assert "No Python files found" in result.output
