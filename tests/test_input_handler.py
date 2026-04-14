"""Tests for input_handler.py — parsing, validation, actions, and InputHandler key sequences."""

from __future__ import annotations

from input_handler import (
    InputHandler,
    add_change,
    comment_add,
    comment_delete,
    comment_edit_last,
    comment_replace_all,
    handle_deletion,
    open_change,
    parse_idx_notation,
    set_automerge,
    toggle_disable,
    toggle_waiting,
    validate_idx,
)
from tests.conftest import FakeApp

# ============================================================================
# parse_idx_notation
# ============================================================================


class TestParseIdxNotation:
    """parse_idx_notation converts flexible index notation into sorted unique lists."""

    def test_single_index(self) -> None:
        assert parse_idx_notation("3", 10) == [3]

    def test_comma_separated(self) -> None:
        assert parse_idx_notation("3,1,5", 10) == [1, 3, 5]

    def test_range_inclusive(self) -> None:
        assert parse_idx_notation("2-5", 10) == [2, 3, 4, 5]

    def test_combined(self) -> None:
        assert parse_idx_notation("1-3, 7, 9-10", 10) == [1, 2, 3, 7, 9, 10]

    def test_deduplicates(self) -> None:
        assert parse_idx_notation("1,1,2,2", 5) == [1, 2]

    def test_overlapping_ranges(self) -> None:
        assert parse_idx_notation("1-3,2-4", 5) == [1, 2, 3, 4]

    def test_whitespace_ignored(self) -> None:
        assert parse_idx_notation("  1 , 3 - 5 ", 10) == [1, 3, 4, 5]

    # --- edge cases ---

    def test_empty_string(self) -> None:
        assert parse_idx_notation("", 10) is None

    def test_whitespace_only(self) -> None:
        assert parse_idx_notation("   ", 10) is None

    def test_zero_index(self) -> None:
        assert parse_idx_notation("0", 10) is None

    def test_index_exceeds_max(self) -> None:
        assert parse_idx_notation("11", 10) is None

    def test_range_exceeds_max(self) -> None:
        assert parse_idx_notation("8-11", 10) is None

    def test_reversed_range(self) -> None:
        assert parse_idx_notation("5-2", 10) is None

    def test_double_comma(self) -> None:
        assert parse_idx_notation("1,,3", 10) is None

    def test_trailing_comma(self) -> None:
        assert parse_idx_notation("1,", 10) is None

    def test_leading_comma(self) -> None:
        assert parse_idx_notation(",1", 10) is None

    def test_non_numeric(self) -> None:
        assert parse_idx_notation("abc", 10) is None

    def test_negative(self) -> None:
        assert parse_idx_notation("-1", 10) is None

    def test_incomplete_range(self) -> None:
        assert parse_idx_notation("1-", 10) is None
        assert parse_idx_notation("-5", 10) is None

    def test_max_idx_one(self) -> None:
        assert parse_idx_notation("1", 1) == [1]
        assert parse_idx_notation("2", 1) is None

    def test_range_equal_bounds(self) -> None:
        assert parse_idx_notation("3-3", 5) == [3]


# ============================================================================
# validate_idx
# ============================================================================


class TestValidateIdx:
    def test_valid_index(self) -> None:
        assert validate_idx("1", 5) == 1
        assert validate_idx("5", 5) == 5

    def test_zero_is_invalid(self) -> None:
        assert validate_idx("0", 5) is None

    def test_exceeds_count(self) -> None:
        assert validate_idx("6", 5) is None

    def test_non_numeric(self) -> None:
        assert validate_idx("abc", 5) is None
        assert validate_idx("", 5) is None

    def test_negative_string(self) -> None:
        assert validate_idx("-1", 5) is None

    def test_boundary_values(self) -> None:
        assert validate_idx("1", 1) == 1
        assert validate_idx("2", 1) is None


# ============================================================================
# add_change action
# ============================================================================


class TestAddChange:
    def test_valid_number_and_explicit_host(self, fake_app: FakeApp) -> None:
        add_change(fake_app, {"number": "42", "host": "myhost.com"})
        assert fake_app.last_call() == ("add_change", (42, "myhost.com"))

    def test_empty_host_uses_default(self, fake_app: FakeApp) -> None:
        fake_app.config.default_host = "default.host"
        add_change(fake_app, {"number": "10", "host": ""})
        assert fake_app.last_call() == ("add_change", (10, "default.host"))

    def test_host_from_index(self, populated_app: FakeApp) -> None:
        """When host is a digit, look up the host from that change index."""
        add_change(populated_app, {"number": "99", "host": "1"})
        expected_host = populated_app.changes[0].host
        assert populated_app.last_call() == ("add_change", (99, expected_host))

    def test_host_index_out_of_range(self, populated_app: FakeApp) -> None:
        add_change(populated_app, {"number": "99", "host": "999"})
        assert "add_change" not in populated_app.call_names()
        assert "No change at index" in populated_app.status_msg

    def test_host_index_zero(self, populated_app: FakeApp) -> None:
        add_change(populated_app, {"number": "99", "host": "0"})
        assert "add_change" not in populated_app.call_names()
        assert "No change at index" in populated_app.status_msg

    def test_empty_number_invalid(self, fake_app: FakeApp) -> None:
        add_change(fake_app, {"number": "", "host": "h"})
        assert "add_change" not in fake_app.call_names()
        assert "Invalid change number" in fake_app.status_msg

    def test_non_digit_number(self, fake_app: FakeApp) -> None:
        add_change(fake_app, {"number": "abc", "host": "h"})
        assert "Invalid change number" in fake_app.status_msg

    def test_zero_number_invalid(self, fake_app: FakeApp) -> None:
        add_change(fake_app, {"number": "0", "host": "h"})
        assert "Invalid change number" in fake_app.status_msg

    def test_no_host_and_no_default(self, fake_app: FakeApp) -> None:
        fake_app.config.default_host = None
        add_change(fake_app, {"number": "1", "host": ""})
        assert "No host specified" in fake_app.status_msg


# ============================================================================
# toggle_waiting
# ============================================================================


class TestToggleWaiting:
    def test_single_index(self, populated_app: FakeApp) -> None:
        toggle_waiting(populated_app, {"idx": "1"})
        assert populated_app.last_call() == ("toggle_waiting", (1,))

    def test_all(self, populated_app: FakeApp) -> None:
        toggle_waiting(populated_app, {"idx": "a"})
        assert populated_app.last_call() == ("toggle_all_waiting", ())

    def test_range(self, populated_app: FakeApp) -> None:
        toggle_waiting(populated_app, {"idx": "1-3"})
        calls = [(name, args) for name, args in populated_app.calls if name == "toggle_waiting"]
        assert calls == [("toggle_waiting", (1,)), ("toggle_waiting", (2,)), ("toggle_waiting", (3,))]

    def test_invalid_index(self, populated_app: FakeApp) -> None:
        toggle_waiting(populated_app, {"idx": "999"})
        assert "Invalid idx" in populated_app.status_msg

    def test_empty_index(self, populated_app: FakeApp) -> None:
        toggle_waiting(populated_app, {"idx": ""})
        assert "Invalid idx" in populated_app.status_msg


# ============================================================================
# handle_deletion
# ============================================================================


class TestHandleDeletion:
    def test_single_index(self, populated_app: FakeApp) -> None:
        handle_deletion(populated_app, {"idx": "2"})
        assert populated_app.last_call() == ("toggle_deleted", (2,))

    def test_all_submitted(self, populated_app: FakeApp) -> None:
        handle_deletion(populated_app, {"idx": "a"})
        assert populated_app.last_call() == ("delete_all_submitted", ())

    def test_purge(self, populated_app: FakeApp) -> None:
        handle_deletion(populated_app, {"idx": "x"})
        assert populated_app.last_call() == ("purge_deleted", ())

    def test_restore(self, populated_app: FakeApp) -> None:
        handle_deletion(populated_app, {"idx": "r"})
        assert populated_app.last_call() == ("restore_all", ())

    def test_range(self, populated_app: FakeApp) -> None:
        handle_deletion(populated_app, {"idx": "1,3"})
        calls = [(n, a) for n, a in populated_app.calls if n == "toggle_deleted"]
        assert calls == [("toggle_deleted", (1,)), ("toggle_deleted", (3,))]

    def test_invalid_index(self, populated_app: FakeApp) -> None:
        handle_deletion(populated_app, {"idx": "abc"})
        assert "Invalid idx" in populated_app.status_msg


# ============================================================================
# toggle_disable
# ============================================================================


class TestToggleDisable:
    def test_single_index(self, populated_app: FakeApp) -> None:
        toggle_disable(populated_app, {"idx": "2"})
        assert populated_app.last_call() == ("toggle_disabled", (2,))

    def test_all(self, populated_app: FakeApp) -> None:
        toggle_disable(populated_app, {"idx": "a"})
        assert populated_app.last_call() == ("toggle_all_disabled", ())

    def test_range(self, populated_app: FakeApp) -> None:
        toggle_disable(populated_app, {"idx": "1-2"})
        calls = [(n, a) for n, a in populated_app.calls if n == "toggle_disabled"]
        assert calls == [("toggle_disabled", (1,)), ("toggle_disabled", (2,))]

    def test_invalid(self, populated_app: FakeApp) -> None:
        toggle_disable(populated_app, {"idx": ""})
        assert "Invalid idx" in populated_app.status_msg


# ============================================================================
# open_change / set_automerge
# ============================================================================


class TestOpenChange:
    def test_single_index(self, populated_app: FakeApp) -> None:
        open_change(populated_app, {"idx": "1"})
        assert populated_app.last_call() == ("open_change_webui", (1,))

    def test_range(self, populated_app: FakeApp) -> None:
        open_change(populated_app, {"idx": "1-3"})
        calls = [(n, a) for n, a in populated_app.calls if n == "open_change_webui"]
        assert len(calls) == 3

    def test_invalid(self, populated_app: FakeApp) -> None:
        open_change(populated_app, {"idx": "abc"})
        assert "Invalid idx" in populated_app.status_msg


class TestSetAutomerge:
    def test_single_index(self, populated_app: FakeApp) -> None:
        set_automerge(populated_app, {"idx": "2"})
        assert populated_app.last_call() == ("set_automerge", (2,))

    def test_range(self, populated_app: FakeApp) -> None:
        set_automerge(populated_app, {"idx": "1,3"})
        calls = [(n, a) for n, a in populated_app.calls if n == "set_automerge"]
        assert len(calls) == 2

    def test_invalid(self, populated_app: FakeApp) -> None:
        set_automerge(populated_app, {"idx": "xyz"})
        assert "Invalid idx" in populated_app.status_msg


# ============================================================================
# Comment actions
# ============================================================================


class TestCommentAdd:
    def test_add_comment(self, populated_app: FakeApp) -> None:
        comment_add(populated_app, {"idx": "1", "text": "hello"})
        assert populated_app.last_call() == ("add_comment", (1, "hello"))


class TestCommentReplaceAll:
    def test_replace_all(self, populated_app: FakeApp) -> None:
        comment_replace_all(populated_app, {"idx": "2", "text": "replaced"})
        assert populated_app.last_call() == ("replace_all_comments", (2, "replaced"))


class TestCommentEditLast:
    def test_edit_last(self, populated_app: FakeApp) -> None:
        comment_edit_last(populated_app, {"idx": "3", "text": "edited"})
        assert populated_app.last_call() == ("edit_last_comment", (3, "edited"))


class TestCommentDelete:
    def test_delete_single_comment(self, populated_app: FakeApp) -> None:
        comment_delete(populated_app, {"idx": "1", "comment_idx": "2"})
        assert populated_app.last_call() == ("delete_comment", (1, 2))

    def test_delete_all_comments(self, populated_app: FakeApp) -> None:
        comment_delete(populated_app, {"idx": "1", "comment_idx": "a"})
        assert populated_app.last_call() == ("delete_all_comments", (1,))


# ============================================================================
# InputHandler — key sequence processing
# ============================================================================


class TestInputHandlerBasic:
    """Test the InputHandler state machine for basic shortcuts."""

    def test_quit(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("q")
        assert "quit" in populated_app.call_names()

    def test_refresh(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("r")
        assert "refresh_all" in populated_app.call_names()

    def test_fetch(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("f")
        assert "fetch_open_changes" in populated_app.call_names()

    def test_escape_resets(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        assert handler.sequence == [" "]
        handler.handle_key("<esc>")
        assert handler.sequence == []
        assert handler.input is None


class TestInputHandlerLeaderActions:
    """Test leader key ( space ) → action letter → input collection → execution."""

    def test_add_change_flow(self, populated_app: FakeApp) -> None:
        """Space → a → type number → enter → type host → enter."""
        populated_app.config.default_host = "fallback.host"
        handler = InputHandler(populated_app)

        handler.handle_key(" ")
        handler.handle_key("a")

        # Now in input mode for "number"
        assert handler.input == ""
        assert handler.current_field is not None
        assert handler.current_field.name == "number"

        # Type "123"
        handler.handle_key("1")
        handler.handle_key("2")
        handler.handle_key("3")
        assert handler.input == "123"

        # Confirm number
        handler.handle_key("<enter>")

        # Now in input mode for "host"
        assert handler.current_field is not None
        assert handler.current_field.name == "host"

        # Leave host empty to use default
        handler.handle_key("<enter>")

        assert ("add_change", (123, "fallback.host")) in populated_app.calls

    def test_toggle_waiting_flow(self, populated_app: FakeApp) -> None:
        """Space → w → type index → enter."""
        handler = InputHandler(populated_app)

        handler.handle_key(" ")
        handler.handle_key("w")

        # Type "2"
        handler.handle_key("2")
        handler.handle_key("<enter>")

        assert ("toggle_waiting", (2,)) in populated_app.calls

    def test_toggle_waiting_all(self, populated_app: FakeApp) -> None:
        """Space → w → 'a' (special char) → immediately dispatches."""
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("w")
        handler.handle_key("a")

        assert ("toggle_all_waiting", ()) in populated_app.calls

    def test_deletion_flow(self, populated_app: FakeApp) -> None:
        """Space → x → type index → enter."""
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("x")
        handler.handle_key("1")
        handler.handle_key("<enter>")

        assert ("toggle_deleted", (1,)) in populated_app.calls

    def test_deletion_purge(self, populated_app: FakeApp) -> None:
        """Space → x → 'x' (special char for purge)."""
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("x")
        handler.handle_key("x")

        assert ("purge_deleted", ()) in populated_app.calls

    def test_deletion_restore(self, populated_app: FakeApp) -> None:
        """Space → x → 'r' (special char for restore)."""
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("x")
        handler.handle_key("r")

        assert ("restore_all", ()) in populated_app.calls

    def test_disable_flow(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("d")
        handler.handle_key("3")
        handler.handle_key("<enter>")

        assert ("toggle_disabled", (3,)) in populated_app.calls

    def test_open_change_flow(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("o")
        handler.handle_key("1")
        handler.handle_key("<enter>")

        assert ("open_change_webui", (1,)) in populated_app.calls

    def test_set_automerge_flow(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("s")
        handler.handle_key("2")
        handler.handle_key("<enter>")

        assert ("set_automerge", (2,)) in populated_app.calls


class TestInputHandlerBackspace:
    """Backspace should delete last character in input mode."""

    def test_backspace_removes_character(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("w")

        handler.handle_key("1")
        handler.handle_key("2")
        assert handler.input == "12"

        handler.handle_key("<bs>")
        assert handler.input == "1"

    def test_backspace_on_empty_input(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("w")

        handler.handle_key("<bs>")
        assert handler.input == ""


class TestInputHandlerEditorActions:
    """Test editor submenu: e → c / e → a."""

    def test_editor_config(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("e")
        handler.handle_key("c")

        assert ("open_config_in_editor", ()) in populated_app.calls

    def test_editor_approvals(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("e")
        handler.handle_key("a")

        assert ("open_changes_in_editor", ()) in populated_app.calls

    def test_editor_invalid_key(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("e")
        handler.handle_key("z")
        # No action should be called — z is not a valid editor subkey
        assert len(populated_app.calls) == 0


class TestInputHandlerCommentFlow:
    """Test comment submenu: space → c → idx → enter → sub-action → text → enter."""

    def test_comment_add_flow(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")

        # Enter idx
        handler.handle_key("1")
        handler.handle_key("<enter>")

        # Now in sub-action selection mode
        assert handler.pending_sub_actions is not None

        # Select 'a' (add)
        handler.handle_key("a")

        # Now in text input mode
        assert handler.current_field is not None
        assert handler.current_field.name == "text"

        # Type comment
        for ch in "hello world":
            handler.handle_key(ch)
        handler.handle_key("<enter>")

        assert ("add_comment", (1, "hello world")) in populated_app.calls

    def test_comment_replace_all_flow(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")
        handler.handle_key("2")
        handler.handle_key("<enter>")
        handler.handle_key("A")

        for ch in "new comment":
            handler.handle_key(ch)
        handler.handle_key("<enter>")

        assert ("replace_all_comments", (2, "new comment")) in populated_app.calls

    def test_comment_edit_last_flow(self, populated_app: FakeApp) -> None:
        """Edit last comment — should pre-fill input with last comment text."""
        # Give the change some comments
        populated_app.changes[0].comments = ["first", "last comment"]

        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")
        handler.handle_key("1")
        handler.handle_key("<enter>")
        handler.handle_key("e")

        # Input should be pre-filled with last comment
        assert handler.input == "last comment"

        # Append some text
        handler.handle_key("!")
        handler.handle_key("<enter>")

        assert ("edit_last_comment", (1, "last comment!")) in populated_app.calls

    def test_comment_edit_last_no_comments(self, populated_app: FakeApp) -> None:
        """Edit last when there are no comments should show error and reset."""
        populated_app.changes[0].comments = []

        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")
        handler.handle_key("1")
        handler.handle_key("<enter>")
        handler.handle_key("e")

        assert "No comments to edit" in populated_app.status_msg
        assert handler.sequence == []

    def test_comment_delete_flow(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")
        handler.handle_key("1")
        handler.handle_key("<enter>")
        handler.handle_key("d")

        # Enter comment index
        handler.handle_key("3")
        handler.handle_key("<enter>")

        assert ("delete_comment", (1, 3)) in populated_app.calls

    def test_comment_delete_all_flow(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")
        handler.handle_key("1")
        handler.handle_key("<enter>")
        handler.handle_key("d")

        # 'a' is a special char for COMMENT_IDX_FIELD
        handler.handle_key("a")

        assert ("delete_all_comments", (1,)) in populated_app.calls

    def test_invalid_comment_subaction(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")
        handler.handle_key("1")
        handler.handle_key("<enter>")

        # 'z' is not a valid sub-action
        handler.handle_key("z")
        assert "Invalid option" in populated_app.status_msg
        assert handler.sequence == []


class TestInputHandlerDigitsOnlyFilter:
    """The digits_only field constraint should reject non-digit input."""

    def test_rejects_letters_in_idx(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("o")

        # Try typing a letter — should be ignored
        handler.handle_key("x")
        assert handler.input == ""

        handler.handle_key("2")
        assert handler.input == "2"

    def test_rejects_letters_in_number_field(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("a")

        handler.handle_key("a")  # should be ignored
        handler.handle_key("1")
        assert handler.input == "1"


class TestInputHandlerExtraChars:
    """Fields with extra_chars should accept those characters alongside digits."""

    def test_comma_in_idx_for_waiting(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("w")

        handler.handle_key("1")
        handler.handle_key(",")
        handler.handle_key("3")
        assert handler.input == "1,3"

    def test_dash_in_idx_for_deletion(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("x")

        handler.handle_key("1")
        handler.handle_key("-")
        handler.handle_key("3")
        assert handler.input == "1-3"


class TestInputHandlerPromptAndHints:
    """Test the prompt() and hints() methods."""

    def test_hints_default(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        hints = handler.hints()
        assert "Space" in hints
        assert "quit" in hints

    def test_hints_after_space(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        hints = handler.hints()
        assert "add" in hints
        assert "wait" in hints

    def test_hints_after_e(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("e")
        hints = handler.hints()
        assert "config" in hints
        assert "approvals" in hints

    def test_prompt_empty_by_default(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        assert handler.prompt() == ""

    def test_prompt_during_input(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("w")
        prompt = handler.prompt()
        assert "Toggle waiting" in prompt

    def test_prompt_during_subaction_selection(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("c")
        handler.handle_key("1")
        handler.handle_key("<enter>")
        prompt = handler.prompt()
        assert "comment" in prompt
        assert "add" in prompt


class TestInputHandlerKeyAllowed:
    """Test that invalid keys are rejected at each stage of the sequence."""

    def test_random_key_at_root(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("z")
        # No action triggered, just a status message
        assert handler.sequence == []

    def test_invalid_key_after_space(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key(" ")
        handler.handle_key("z")
        # 'z' not in LEADER_ACTIONS — should still append to sequence but no action
        assert "key not allowed" in populated_app.status_msg

    def test_enter_on_empty_sequence(self, populated_app: FakeApp) -> None:
        handler = InputHandler(populated_app)
        handler.handle_key("<enter>")
        assert len(populated_app.calls) == 0


class TestInputHandlerArrowKeys:
    """Arrow keys should be ignored (no crash, no action)."""

    def test_arrow_ignored(self, populated_app: FakeApp) -> None:
        from utils import Arrow

        handler = InputHandler(populated_app)
        handler.handle_key(Arrow.UP)
        handler.handle_key(Arrow.DOWN)
        assert len(populated_app.calls) == 0
        assert handler.sequence == []
