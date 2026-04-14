"""Shared fixtures and fake implementations for the test suite."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pytest

from changes import Changes
from models import TrackedChange

# ---------------------------------------------------------------------------
# FakeConfig — lightweight stand-in for config.AppConfig
# ---------------------------------------------------------------------------


@dataclass
class FakeConfig:
    """Mimics the attributes of AppConfig without reading a real TOML file."""

    path: Path = field(default_factory=lambda: Path("/fake/config.toml"))
    interval: int = 30
    changes_path: Path = field(default_factory=lambda: Path("/fake/approvals.json"))
    default_host: str | None = "gerrit.example.com"
    default_port: int | None = 29418
    email: str | None = None
    editor: str | None = None

    def mtime(self) -> float:
        try:
            return self.path.stat().st_mtime
        except OSError:
            return 0.0


# ---------------------------------------------------------------------------
# FakeChanges — wraps a list and supports all operations used by input_handler
# ---------------------------------------------------------------------------


class FakeChanges:
    """In-memory replacement for Changes that avoids filesystem I/O."""

    def __init__(self, items: list[TrackedChange] | None = None) -> None:
        self.changes: list[TrackedChange] = items or []
        self._save_count: int = 0

    def __len__(self) -> int:
        return len(self.changes)

    def __getitem__(self, idx: int) -> TrackedChange:
        return self.changes[idx]

    def count(self) -> int:
        return len(self.changes)

    def at(self, idx: int) -> TrackedChange | None:
        if idx < 0 or idx >= len(self.changes):
            return None
        return self.changes[idx]

    def append(self, ch: TrackedChange) -> None:
        self.changes.append(ch)

    def get_all(self) -> list[TrackedChange]:
        return self.changes

    def get_running(self) -> list[TrackedChange]:
        return [ch for ch in self.changes if ch.is_running()]

    def get_active(self) -> list[TrackedChange]:
        return [ch for ch in self.changes if ch.is_active()]

    def get_disabled(self) -> list[TrackedChange]:
        return [ch for ch in self.changes if ch.disabled]

    def get_submitted(self) -> list[TrackedChange]:
        return [ch for ch in self.changes if ch.submitted]

    def get_deleted(self) -> list[TrackedChange]:
        return [ch for ch in self.changes if ch.deleted]

    def remove_all_deleted(self) -> None:
        self.changes[:] = [ch for ch in self.changes if not ch.deleted]

    @contextmanager
    def edit_change(self, idx: int):
        if idx < 0 or idx >= len(self.changes):
            yield None
            return
        yield self.changes[idx]
        self._save_count += 1

    @contextmanager
    def edit_changes(self, indexes: list[int]):
        valid = [self.changes[i] for i in indexes if 0 <= i < len(self.changes)]
        yield valid
        self._save_count += 1

    def save_changes(self) -> None:
        self._save_count += 1

    def load_changes(self, default_host: str | None, default_port: int | None) -> None:
        pass  # no-op for testing


# ---------------------------------------------------------------------------
# FakeApp — satisfies the AppContext protocol
# ---------------------------------------------------------------------------


class FakeApp:
    """Fake application context that records every method call for assertions."""

    def __init__(
        self,
        changes: FakeChanges | None = None,
        config: FakeConfig | None = None,
    ) -> None:
        self.changes: FakeChanges = changes or FakeChanges()
        self.config: FakeConfig = config or FakeConfig()
        self.status_msg: str = ""
        self.calls: list[tuple[str, tuple]] = []

    # --- helpers ---

    def _record(self, name: str, *args: object) -> None:
        self.calls.append((name, args))

    def last_call(self) -> tuple[str, tuple] | None:
        return self.calls[-1] if self.calls else None

    def call_names(self) -> list[str]:
        return [name for name, _ in self.calls]

    # --- AppContext protocol methods ---

    def get_changes(self) -> Iterable[TrackedChange]:
        self._record("get_changes")
        return self.changes.get_all()

    def toggle_waiting(self, row: int) -> None:
        self._record("toggle_waiting", row)

    def toggle_deleted(self, row: int) -> None:
        self._record("toggle_deleted", row)

    def toggle_disabled(self, row: int) -> None:
        self._record("toggle_disabled", row)

    def toggle_all_waiting(self) -> None:
        self._record("toggle_all_waiting")

    def toggle_all_disabled(self) -> None:
        self._record("toggle_all_disabled")

    def refresh_all(self) -> None:
        self._record("refresh_all")

    def open_change_webui(self, row: int) -> None:
        self._record("open_change_webui", row)

    def set_automerge(self, row: int) -> None:
        self._record("set_automerge", row)

    def add_change(self, number: int, host: str) -> None:
        self._record("add_change", number, host)

    def delete_all_submitted(self) -> None:
        self._record("delete_all_submitted")

    def purge_deleted(self) -> None:
        self._record("purge_deleted")

    def restore_all(self) -> None:
        self._record("restore_all")

    def fetch_open_changes(self) -> None:
        self._record("fetch_open_changes")

    def open_config_in_editor(self) -> None:
        self._record("open_config_in_editor")

    def open_changes_in_editor(self) -> None:
        self._record("open_changes_in_editor")

    def quit(self) -> None:
        self._record("quit")

    # --- Comments ---

    def add_comment(self, row: int, text: str) -> None:
        self._record("add_comment", row, text)

    def replace_all_comments(self, row: int, text: str) -> None:
        self._record("replace_all_comments", row, text)

    def edit_last_comment(self, row: int, text: str) -> None:
        self._record("edit_last_comment", row, text)

    def delete_comment(self, row: int, comment_idx: int) -> None:
        self._record("delete_comment", row, comment_idx)

    def delete_all_comments(self, row: int) -> None:
        self._record("delete_all_comments", row)


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_config() -> FakeConfig:
    """Return a FakeConfig with sensible defaults."""
    return FakeConfig()


@pytest.fixture
def fake_changes() -> FakeChanges:
    """Return an empty FakeChanges."""
    return FakeChanges()


@pytest.fixture
def fake_app(fake_changes: FakeChanges, fake_config: FakeConfig) -> FakeApp:
    """Return a FakeApp wired to the default FakeChanges and FakeConfig."""
    return FakeApp(changes=fake_changes, config=fake_config)


@pytest.fixture
def sample_changes() -> list[TrackedChange]:
    """Return a representative list of TrackedChange objects for testing."""
    return [
        TrackedChange(number=100, host="gerrit.example.com", port=29418, current_revision="aaa111"),
        TrackedChange(number=200, host="gerrit.example.com", port=29418, current_revision="bbb222", submitted=True),
        TrackedChange(number=300, host="other.host", port=22, current_revision="ccc333", disabled=True),
        TrackedChange(number=400, host="gerrit.example.com", port=29418, current_revision="ddd444", deleted=True),
        TrackedChange(number=500, host="gerrit.example.com", port=29418, current_revision="eee555", waiting=True),
    ]


@pytest.fixture
def populated_app(sample_changes: list[TrackedChange], fake_config: FakeConfig) -> FakeApp:
    """Return a FakeApp whose changes list is pre-populated with *sample_changes*."""
    fc = FakeChanges(sample_changes)
    return FakeApp(changes=fc, config=fake_config)


@pytest.fixture
def tmp_changes_path(tmp_path: Path) -> Path:
    """Return a path inside tmp_path suitable for a Changes JSON file."""
    return tmp_path / "approvals.json"


@pytest.fixture
def tmp_changes(tmp_changes_path: Path) -> Changes:
    """Return a real Changes instance backed by a temp file."""
    return Changes(tmp_changes_path)


@pytest.fixture
def tmp_config_path(tmp_path: Path) -> Path:
    """Return a path inside tmp_path suitable for a TOML config file."""
    return tmp_path / "config.toml"


def write_changes_json(path: Path, data: list[dict]) -> None:
    """Helper: write a JSON list to *path*."""
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_toml(path: Path, content: str) -> None:
    """Helper: write a TOML string to *path*."""
    path.write_text(content, encoding="utf-8")
