"""Tests for the Changes class (changes.py)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from changes import Changes
from models import TrackedChange
from tests.conftest import write_changes_json

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestChangesInit:
    """Creating a Changes instance should bootstrap the JSON file."""

    def test_creates_empty_file_when_missing(self, tmp_changes_path: Path) -> None:
        assert not tmp_changes_path.exists()
        Changes(tmp_changes_path)
        assert tmp_changes_path.exists()
        assert json.loads(tmp_changes_path.read_text(encoding="utf-8")) == []

    def test_creates_empty_file_when_empty(self, tmp_changes_path: Path) -> None:
        tmp_changes_path.write_text("", encoding="utf-8")
        Changes(tmp_changes_path)
        assert json.loads(tmp_changes_path.read_text(encoding="utf-8")) == []

    def test_leaves_existing_data_alone(self, tmp_changes_path: Path) -> None:
        data = [{"number": 1, "host": "h", "hash": "aaa"}]
        write_changes_json(tmp_changes_path, data)
        Changes(tmp_changes_path)
        assert json.loads(tmp_changes_path.read_text(encoding="utf-8")) == data

    def test_starts_with_empty_in_memory_list(self, tmp_changes: Changes) -> None:
        assert len(tmp_changes) == 0
        assert tmp_changes.count() == 0


# ---------------------------------------------------------------------------
# load_changes — valid data
# ---------------------------------------------------------------------------


class TestLoadChangesValid:
    def test_basic_load(self, tmp_changes_path: Path) -> None:
        write_changes_json(
            tmp_changes_path,
            [
                {"number": 42, "host": "h1", "hash": "abc123"},
            ],
        )
        ch = Changes(tmp_changes_path)
        ch.load_changes(default_host=None, default_port=22)

        assert len(ch) == 1
        assert ch[0].number == 42
        assert ch[0].host == "h1"
        assert ch[0].current_revision == "abc123"

    def test_uses_default_host_when_missing(self, tmp_changes_path: Path) -> None:
        write_changes_json(
            tmp_changes_path,
            [
                {"number": 1, "hash": "aaa"},
            ],
        )
        ch = Changes(tmp_changes_path)
        ch.load_changes(default_host="fallback.host", default_port=22)
        assert ch[0].host == "fallback.host"

    def test_uses_default_port_when_missing(self, tmp_changes_path: Path) -> None:
        write_changes_json(
            tmp_changes_path,
            [
                {"number": 1, "host": "h", "hash": "aaa"},
            ],
        )
        ch = Changes(tmp_changes_path)
        ch.load_changes(default_host=None, default_port=9999)
        assert ch[0].port == 9999

    def test_explicit_port_overrides_default(self, tmp_changes_path: Path) -> None:
        write_changes_json(
            tmp_changes_path,
            [
                {"number": 1, "host": "h", "hash": "aaa", "port": 1234},
            ],
        )
        ch = Changes(tmp_changes_path)
        ch.load_changes(default_host=None, default_port=22)
        assert ch[0].port == 1234

    def test_loads_optional_flags(self, tmp_changes_path: Path) -> None:
        write_changes_json(
            tmp_changes_path,
            [
                {"number": 1, "host": "h", "hash": "x", "waiting": True, "disabled": True},
            ],
        )
        ch = Changes(tmp_changes_path)
        ch.load_changes(default_host=None, default_port=22)
        assert ch[0].waiting is True
        assert ch[0].disabled is True

    def test_loads_comments(self, tmp_changes_path: Path) -> None:
        write_changes_json(
            tmp_changes_path,
            [
                {"number": 1, "host": "h", "hash": "x", "comments": ["c1", "c2"]},
            ],
        )
        ch = Changes(tmp_changes_path)
        ch.load_changes(default_host=None, default_port=22)
        assert ch[0].comments == ["c1", "c2"]

    def test_multiple_entries(self, tmp_changes_path: Path) -> None:
        write_changes_json(
            tmp_changes_path,
            [
                {"number": 1, "host": "h1", "hash": "a1"},
                {"number": 2, "host": "h2", "hash": "a2"},
                {"number": 3, "host": "h3", "hash": "a3"},
            ],
        )
        ch = Changes(tmp_changes_path)
        ch.load_changes(default_host=None, default_port=22)
        assert len(ch) == 3
        assert [c.number for c in ch.get_all()] == [1, 2, 3]


# ---------------------------------------------------------------------------
# load_changes — invalid data
# ---------------------------------------------------------------------------


class TestLoadChangesInvalid:
    def test_non_list_json_raises(self, tmp_changes_path: Path) -> None:
        tmp_changes_path.write_text('{"not": "a list"}', encoding="utf-8")
        ch = Changes(tmp_changes_path)
        with pytest.raises(ValueError, match="not a list"):
            ch.load_changes(default_host=None, default_port=22)

    def test_missing_number_raises(self, tmp_changes_path: Path) -> None:
        write_changes_json(tmp_changes_path, [{"host": "h", "hash": "abc"}])
        ch = Changes(tmp_changes_path)
        with pytest.raises(ValueError, match="Invalid number"):
            ch.load_changes(default_host=None, default_port=22)

    def test_non_numeric_number_raises(self, tmp_changes_path: Path) -> None:
        write_changes_json(tmp_changes_path, [{"number": "not_a_number", "host": "h", "hash": "abc"}])
        ch = Changes(tmp_changes_path)
        with pytest.raises(ValueError, match="Invalid number"):
            ch.load_changes(default_host=None, default_port=22)

    def test_missing_hash_raises(self, tmp_changes_path: Path) -> None:
        write_changes_json(tmp_changes_path, [{"number": 1, "host": "h"}])
        ch = Changes(tmp_changes_path)
        with pytest.raises(ValueError, match="missing required 'hash' field"):
            ch.load_changes(default_host=None, default_port=22)

    def test_empty_hash_raises(self, tmp_changes_path: Path) -> None:
        write_changes_json(tmp_changes_path, [{"number": 1, "host": "h", "hash": ""}])
        ch = Changes(tmp_changes_path)
        with pytest.raises(ValueError, match="missing required 'hash' field"):
            ch.load_changes(default_host=None, default_port=22)

    def test_bad_port_raises(self, tmp_changes_path: Path) -> None:
        write_changes_json(tmp_changes_path, [{"number": 1, "host": "h", "hash": "abc", "port": "xyz"}])
        ch = Changes(tmp_changes_path)
        with pytest.raises(ValueError, match="Invalid port"):
            ch.load_changes(default_host=None, default_port=22)

    def test_no_host_and_no_default_raises(self, tmp_changes_path: Path) -> None:
        write_changes_json(tmp_changes_path, [{"number": 1, "hash": "abc"}])
        ch = Changes(tmp_changes_path)
        with pytest.raises(ValueError, match="no host"):
            ch.load_changes(default_host=None, default_port=22)


# ---------------------------------------------------------------------------
# save_changes round-trip
# ---------------------------------------------------------------------------


class TestSaveChanges:
    def test_round_trip(self, tmp_changes: Changes) -> None:
        """save → reload should yield identical TrackedChange objects."""
        tc = TrackedChange(number=99, host="h", port=29418, current_revision="rev1", waiting=True)
        tmp_changes.append(tc)
        tmp_changes.save_changes()

        ch2 = Changes(tmp_changes.path)
        ch2.load_changes(default_host=None, default_port=22)
        assert len(ch2) == 1
        assert ch2[0].number == 99
        assert ch2[0].host == "h"
        assert ch2[0].port == 29418
        assert ch2[0].current_revision == "rev1"
        assert ch2[0].waiting is True

    def test_saves_only_truthy_flags(self, tmp_changes: Changes) -> None:
        tc = TrackedChange(number=1, host="h", current_revision="rev")
        tmp_changes.append(tc)
        tmp_changes.save_changes()

        raw = json.loads(tmp_changes.path.read_text(encoding="utf-8"))
        entry = raw[0]
        assert "waiting" not in entry
        assert "disabled" not in entry
        assert "deleted" not in entry
        assert "submitted" not in entry

    def test_saves_comments(self, tmp_changes: Changes) -> None:
        tc = TrackedChange(number=1, host="h", current_revision="r", comments=["first", "second"])
        tmp_changes.append(tc)
        tmp_changes.save_changes()

        raw = json.loads(tmp_changes.path.read_text(encoding="utf-8"))
        assert raw[0]["comments"] == ["first", "second"]

    def test_empty_comments_omitted(self, tmp_changes: Changes) -> None:
        tc = TrackedChange(number=1, host="h", current_revision="r", comments=[])
        tmp_changes.append(tc)
        tmp_changes.save_changes()

        raw = json.loads(tmp_changes.path.read_text(encoding="utf-8"))
        assert "comments" not in raw[0]

    def test_port_none_omitted(self, tmp_changes: Changes) -> None:
        tc = TrackedChange(number=1, host="h", current_revision="r", port=None)
        tmp_changes.append(tc)
        tmp_changes.save_changes()

        raw = json.loads(tmp_changes.path.read_text(encoding="utf-8"))
        assert "port" not in raw[0]

    def test_saves_all_truthy_flags(self, tmp_changes: Changes) -> None:
        tc = TrackedChange(
            number=1,
            host="h",
            current_revision="r",
            waiting=True,
            disabled=True,
            deleted=True,
            submitted=True,
        )
        tmp_changes.append(tc)
        tmp_changes.save_changes()

        raw = json.loads(tmp_changes.path.read_text(encoding="utf-8"))
        entry = raw[0]
        assert entry["waiting"] is True
        assert entry["disabled"] is True
        assert entry["deleted"] is True
        assert entry["submitted"] is True


# ---------------------------------------------------------------------------
# append / count / at / __len__ / __getitem__
# ---------------------------------------------------------------------------


class TestCollectionMethods:
    def test_append_increments_length(self, tmp_changes: Changes) -> None:
        assert len(tmp_changes) == 0
        tmp_changes.append(TrackedChange(number=1, host="h"))
        assert len(tmp_changes) == 1
        assert tmp_changes.count() == 1

    def test_getitem(self, tmp_changes: Changes) -> None:
        tc = TrackedChange(number=42, host="h")
        tmp_changes.append(tc)
        assert tmp_changes[0] is tc

    def test_getitem_out_of_range_raises(self, tmp_changes: Changes) -> None:
        with pytest.raises(IndexError):
            _ = tmp_changes[0]

    def test_at_valid(self, tmp_changes: Changes) -> None:
        tc = TrackedChange(number=1, host="h")
        tmp_changes.append(tc)
        assert tmp_changes.at(0) is tc

    def test_at_out_of_range_returns_none(self, tmp_changes: Changes) -> None:
        assert tmp_changes.at(0) is None
        assert tmp_changes.at(-1) is None
        assert tmp_changes.at(999) is None

    def test_count_matches_len(self, tmp_changes: Changes) -> None:
        for i in range(5):
            tmp_changes.append(TrackedChange(number=i, host="h"))
        assert tmp_changes.count() == len(tmp_changes) == 5


# ---------------------------------------------------------------------------
# Getters (filtering)
# ---------------------------------------------------------------------------


class TestGetters:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_changes: Changes) -> None:
        self.ch = tmp_changes
        self.ch.append(TrackedChange(number=1, host="h"))  # running, active
        self.ch.append(TrackedChange(number=2, host="h", submitted=True))  # submitted
        self.ch.append(TrackedChange(number=3, host="h", disabled=True))  # disabled, active
        self.ch.append(TrackedChange(number=4, host="h", deleted=True))  # deleted
        self.ch.append(TrackedChange(number=5, host="h", waiting=True))  # running, active, waiting

    def test_get_all(self) -> None:
        assert len(self.ch.get_all()) == 5

    def test_get_running(self) -> None:
        running = self.ch.get_running()
        nums = [c.number for c in running]
        assert nums == [1, 5]

    def test_get_active(self) -> None:
        active = self.ch.get_active()
        nums = [c.number for c in active]
        assert nums == [1, 3, 5]

    def test_get_disabled(self) -> None:
        disabled = self.ch.get_disabled()
        assert len(disabled) == 1
        assert disabled[0].number == 3

    def test_get_submitted(self) -> None:
        submitted = self.ch.get_submitted()
        assert len(submitted) == 1
        assert submitted[0].number == 2

    def test_get_deleted(self) -> None:
        deleted = self.ch.get_deleted()
        assert len(deleted) == 1
        assert deleted[0].number == 4


# ---------------------------------------------------------------------------
# remove_all_deleted
# ---------------------------------------------------------------------------


class TestRemoveAllDeleted:
    def test_removes_only_deleted(self, tmp_changes: Changes) -> None:
        tmp_changes.append(TrackedChange(number=1, host="h"))
        tmp_changes.append(TrackedChange(number=2, host="h", deleted=True))
        tmp_changes.append(TrackedChange(number=3, host="h"))
        tmp_changes.append(TrackedChange(number=4, host="h", deleted=True))

        tmp_changes.remove_all_deleted()
        assert len(tmp_changes) == 2
        assert [c.number for c in tmp_changes.get_all()] == [1, 3]

    def test_noop_when_none_deleted(self, tmp_changes: Changes) -> None:
        tmp_changes.append(TrackedChange(number=1, host="h"))
        tmp_changes.remove_all_deleted()
        assert len(tmp_changes) == 1


# ---------------------------------------------------------------------------
# edit_change context manager
# ---------------------------------------------------------------------------


class TestEditChange:
    def test_yields_change_and_saves(self, tmp_changes: Changes) -> None:
        tmp_changes.append(TrackedChange(number=1, host="h", current_revision="rev"))

        with tmp_changes.edit_change(0) as tc:
            assert tc is not None
            tc.waiting = True

        # Verify it was saved
        raw = json.loads(tmp_changes.path.read_text(encoding="utf-8"))
        assert len(raw) == 1
        assert raw[0]["waiting"] is True

    def test_out_of_range_yields_none(self, tmp_changes: Changes) -> None:
        with tmp_changes.edit_change(99) as tc:
            assert tc is None

    def test_negative_index_yields_none(self, tmp_changes: Changes) -> None:
        with tmp_changes.edit_change(-1) as tc:
            assert tc is None


# ---------------------------------------------------------------------------
# edit_changes context manager
# ---------------------------------------------------------------------------


class TestEditChanges:
    def test_yields_valid_changes(self, tmp_changes: Changes) -> None:
        for i in range(3):
            tmp_changes.append(TrackedChange(number=i, host="h", current_revision=f"rev{i}"))

        with tmp_changes.edit_changes([0, 2]) as batch:
            assert len(batch) == 2
            assert batch[0].number == 0
            assert batch[1].number == 2

    def test_skips_out_of_range(self, tmp_changes: Changes) -> None:
        tmp_changes.append(TrackedChange(number=1, host="h", current_revision="rev"))

        with tmp_changes.edit_changes([0, 5, 99]) as batch:
            assert len(batch) == 1

    def test_saves_after_yield(self, tmp_changes: Changes) -> None:
        tmp_changes.append(TrackedChange(number=1, host="h", current_revision="rev"))

        with tmp_changes.edit_changes([0]) as batch:
            batch[0].disabled = True

        raw = json.loads(tmp_changes.path.read_text(encoding="utf-8"))
        assert raw[0]["disabled"] is True


# ---------------------------------------------------------------------------
# mtime
# ---------------------------------------------------------------------------


class TestMtime:
    def test_mtime_returns_float(self, tmp_changes: Changes) -> None:
        assert isinstance(tmp_changes.mtime(), float)
        assert tmp_changes.mtime() > 0

    def test_mtime_updates_after_save(self, tmp_changes: Changes) -> None:
        t1 = tmp_changes.mtime()
        time.sleep(0.05)
        tmp_changes.append(TrackedChange(number=1, host="h"))
        tmp_changes.save_changes()
        t2 = tmp_changes.mtime()
        assert t2 >= t1

    def test_mtime_returns_zero_for_missing_file(self, tmp_path: Path) -> None:
        ch = Changes(tmp_path / "approvals.json")
        ch.path.unlink()  # remove the file that __init__ created
        assert ch.mtime() == 0.0
