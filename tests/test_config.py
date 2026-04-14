"""Tests for the AppConfig class (config.py)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from config import DEFAULT_CHANGES_FILENAME, DEFAULT_DEFAULT_PORT, DEFAULT_INTERVAL, AppConfig
from tests.conftest import write_toml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def minimal_toml(
    interval: int | str = 30,
    default_host: str | None = "gerrit.example.com",
    default_port: int | str | None = None,
    changes_file: str | None = None,
    email: str | None = None,
    editor: str | None = None,
) -> str:
    """Build a minimal valid TOML string for testing."""
    lines = ["[config]", f"interval = {interval}"]
    if default_host is not None:
        lines.append(f'default_host = "{default_host}"')
    if default_port is not None:
        lines.append(f"default_port = {default_port}")
    if changes_file is not None:
        lines.append(f'changes_file = "{changes_file}"')
    if email is not None:
        lines.append(f'email = "{email}"')
    if editor is not None:
        lines.append(f'editor = "{editor}"')
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Loading valid config
# ---------------------------------------------------------------------------


class TestAppConfigValid:
    def test_loads_all_fields(self, tmp_config_path: Path) -> None:
        write_toml(
            tmp_config_path,
            minimal_toml(
                interval=60,
                default_host="mygerrit.com",
                default_port=29418,
                changes_file="my_changes.json",
                email="dev@example.com",
                editor="vim",
            ),
        )
        cfg = AppConfig(tmp_config_path)

        assert cfg.interval == 60
        assert cfg.default_host == "mygerrit.com"
        assert cfg.default_port == 29418
        assert cfg.changes_path == (tmp_config_path.parent / "my_changes.json").resolve()
        assert cfg.email == "dev@example.com"
        assert cfg.editor == "vim"

    def test_defaults_are_applied(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, "[config]\n")
        cfg = AppConfig(tmp_config_path)

        assert cfg.interval == DEFAULT_INTERVAL
        assert cfg.default_port == DEFAULT_DEFAULT_PORT
        assert cfg.default_host is None
        assert cfg.email is None
        assert cfg.editor is None
        assert cfg.changes_path == (tmp_config_path.parent / DEFAULT_CHANGES_FILENAME).resolve()

    def test_changes_path_resolves_relative_to_config(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml(changes_file="./sub/changes.json"))
        cfg = AppConfig(tmp_config_path)
        assert cfg.changes_path == (tmp_config_path.parent / "sub" / "changes.json").resolve()

    def test_interval_as_integer_string_in_toml(self, tmp_config_path: Path) -> None:
        """TOML naturally parses integers, but int() cast should also handle edge cases."""
        write_toml(tmp_config_path, "[config]\ninterval = 15\n")
        cfg = AppConfig(tmp_config_path)
        assert cfg.interval == 15


# ---------------------------------------------------------------------------
# Missing [config] section
# ---------------------------------------------------------------------------


class TestAppConfigMissingSection:
    def test_raises_on_missing_config_section(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, "[other]\nfoo = 1\n")
        with pytest.raises(ValueError, match="Missing \\[config\\] section"):
            AppConfig(tmp_config_path)

    def test_raises_on_empty_file(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, "")
        with pytest.raises(ValueError, match="Missing \\[config\\] section"):
            AppConfig(tmp_config_path)


# ---------------------------------------------------------------------------
# Invalid interval
# ---------------------------------------------------------------------------


class TestAppConfigInvalidInterval:
    def test_zero_interval_raises(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, "[config]\ninterval = 0\n")
        with pytest.raises(ValueError, match="interval must be >= 1"):
            AppConfig(tmp_config_path)

    def test_negative_interval_raises(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, "[config]\ninterval = -5\n")
        with pytest.raises(ValueError, match="interval must be >= 1"):
            AppConfig(tmp_config_path)


# ---------------------------------------------------------------------------
# mtime
# ---------------------------------------------------------------------------


class TestAppConfigMtime:
    def test_mtime_returns_float(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml())
        cfg = AppConfig(tmp_config_path)
        assert isinstance(cfg.mtime(), float)
        assert cfg.mtime() > 0

    def test_mtime_zero_for_missing(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml())
        cfg = AppConfig(tmp_config_path)
        cfg.path = Path("/nonexistent/config.toml")
        assert cfg.mtime() == 0.0


# ---------------------------------------------------------------------------
# resolve_email / resolve_editor
# ---------------------------------------------------------------------------


class TestResolveEmail:
    def test_returns_configured_email(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml(email="configured@test.com"))
        cfg = AppConfig(tmp_config_path)
        assert cfg.resolve_email() == "configured@test.com"

    def test_falls_back_to_git_config(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml())
        cfg = AppConfig(tmp_config_path)
        assert cfg.email is None

        with patch("config.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "git@example.com\n"
            assert cfg.resolve_email() == "git@example.com"

    def test_returns_none_when_git_fails(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml())
        cfg = AppConfig(tmp_config_path)

        with patch("config.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            assert cfg.resolve_email() is None

    def test_returns_none_on_git_not_found(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml())
        cfg = AppConfig(tmp_config_path)

        with patch("config.subprocess.run", side_effect=FileNotFoundError):
            assert cfg.resolve_email() is None


class TestResolveEditor:
    def test_returns_configured_editor(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml(editor="nvim"))
        cfg = AppConfig(tmp_config_path)
        assert cfg.resolve_editor() == "nvim"

    def test_falls_back_to_env_variable(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml())
        cfg = AppConfig(tmp_config_path)
        assert cfg.editor is None

        with patch.dict("os.environ", {"EDITOR": "nano"}):
            assert cfg.resolve_editor() == "nano"

    def test_returns_none_when_no_editor(self, tmp_config_path: Path) -> None:
        write_toml(tmp_config_path, minimal_toml())
        cfg = AppConfig(tmp_config_path)

        with patch.dict("os.environ", {}, clear=True):
            assert cfg.resolve_editor() is None
