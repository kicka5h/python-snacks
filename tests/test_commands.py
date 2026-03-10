import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from snacks.main import app

runner = CliRunner()


@pytest.fixture()
def stash(tmp_path_factory):
    """A temp stash directory pre-populated with a few snippets."""
    d = tmp_path_factory.mktemp("stash")
    (d / "auth").mkdir()
    (d / "auth" / "google_oauth.py").write_text("# google oauth\n")
    (d / "auth" / "jwt_helpers.py").write_text("# jwt\n")
    (d / "forms").mkdir()
    (d / "forms" / "contact_form.py").write_text("# contact\n")
    return d


@pytest.fixture()
def stash_env(stash):
    return {"SNACK_STASH": str(stash)}


@pytest.fixture()
def cwd(tmp_path):
    """A separate temp dir used as the current working directory."""
    os.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

def test_no_stash_configured():
    result = runner.invoke(app, ["list"], env={})
    assert result.exit_code != 0
    assert "SNACK_STASH" in result.output


def test_stash_path_missing(tmp_path):
    missing = str(tmp_path / "does_not_exist")
    result = runner.invoke(app, ["list"], env={"SNACK_STASH": missing})
    assert result.exit_code != 0
    assert "does not exist" in result.output


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_all(stash_env):
    result = runner.invoke(app, ["list"], env=stash_env)
    assert result.exit_code == 0
    assert "auth/google_oauth.py" in result.output
    assert "auth/jwt_helpers.py" in result.output
    assert "forms/contact_form.py" in result.output


def test_list_category(stash_env):
    result = runner.invoke(app, ["list", "auth"], env=stash_env)
    assert result.exit_code == 0
    assert "auth/google_oauth.py" in result.output
    assert "forms/contact_form.py" not in result.output


def test_list_empty_category(stash_env):
    result = runner.invoke(app, ["list", "nonexistent"], env=stash_env)
    assert result.exit_code == 0
    assert "No snippets found" in result.output


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

def test_search_match(stash_env):
    result = runner.invoke(app, ["search", "oauth"], env=stash_env)
    assert result.exit_code == 0
    assert "auth/google_oauth.py" in result.output
    assert "jwt_helpers.py" not in result.output


def test_search_no_match(stash_env):
    result = runner.invoke(app, ["search", "zzznomatch"], env=stash_env)
    assert result.exit_code == 0
    assert "No snippets" in result.output


# ---------------------------------------------------------------------------
# unpack
# ---------------------------------------------------------------------------

def test_unpack_preserves_structure(stash_env, cwd):
    result = runner.invoke(app, ["unpack", "auth/google_oauth.py"], env=stash_env)
    assert result.exit_code == 0
    assert (cwd / "auth" / "google_oauth.py").exists()


def test_unpack_flat(stash_env, cwd):
    result = runner.invoke(app, ["unpack", "auth/google_oauth.py", "--flat"], env=stash_env)
    assert result.exit_code == 0
    assert (cwd / "google_oauth.py").exists()
    assert not (cwd / "auth").exists()


def test_unpack_not_found(stash_env, cwd):
    result = runner.invoke(app, ["unpack", "auth/nope.py"], env=stash_env)
    assert result.exit_code != 0
    assert "not found" in result.output


def test_unpack_force_overwrites(stash, stash_env, cwd):
    dest = cwd / "auth" / "google_oauth.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("old content\n")
    result = runner.invoke(app, ["unpack", "auth/google_oauth.py", "--force"], env=stash_env)
    assert result.exit_code == 0
    assert dest.read_text() == "# google oauth\n"


def test_unpack_conflict_aborted(stash, stash_env, cwd):
    dest = cwd / "auth" / "google_oauth.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("old content\n")
    result = runner.invoke(app, ["unpack", "auth/google_oauth.py"], env=stash_env, input="n\n")
    assert dest.read_text() == "old content\n"


# ---------------------------------------------------------------------------
# pack
# ---------------------------------------------------------------------------

def test_pack_copies_to_stash(stash, stash_env, cwd):
    src = cwd / "utils" / "helpers.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("# helpers\n")
    result = runner.invoke(app, ["pack", "utils/helpers.py"], env=stash_env)
    assert result.exit_code == 0
    assert (stash / "utils" / "helpers.py").exists()


def test_pack_source_not_found(stash_env, cwd):
    result = runner.invoke(app, ["pack", "missing.py"], env=stash_env)
    assert result.exit_code != 0
    assert "not found" in result.output


def test_pack_force_overwrites(stash, stash_env, cwd):
    src = cwd / "auth" / "google_oauth.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("# updated oauth\n")
    result = runner.invoke(app, ["pack", "auth/google_oauth.py", "--force"], env=stash_env)
    assert result.exit_code == 0
    assert (stash / "auth" / "google_oauth.py").read_text() == "# updated oauth\n"
