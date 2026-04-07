"""Tests for display.py — build_table refactoring and new build_layout function.

Feature 004: Move input field above the table.
- build_table accepts hints parameter (rendered in caption at bottom)
- New build_layout function composes optional prompt above table
- Integration: App.build() calls build_layout with table (containing hints in caption)
"""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from display import build_header, build_layout, build_table
from models import TrackedChange

# ---------------------------------------------------------------------------
# build_table refactoring (TC-001 to TC-004)
# ---------------------------------------------------------------------------


class TestBuildTableRefactoring:
    """Tests for build_table after hints are in caption (at bottom)."""

    def test_build_table_accepts_hints(self) -> None:
        """TC-001: build_table accepts hints parameter.

        Verify that build_table can be called with hints (rendered in caption).
        """
        changes: list[TrackedChange] = []
        hints = "[bold]Space[/] Changes  [bold]q[/] quit"
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints=hints,
        )
        assert isinstance(table, Table)
        # Verify hints are in caption
        assert "[bold]Space[/]" in table.caption, "Caption should contain hints"

    def test_build_table_hints_optional(self) -> None:
        """TC-002: build_table works without hints parameter."""
        changes: list[TrackedChange] = []
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
        )
        assert isinstance(table, Table)

    def test_build_table_caption_has_config_path_and_interval(self) -> None:
        """TC-003: Caption contains config path and interval."""
        changes: list[TrackedChange] = []
        config_path = "/custom/path/approvals.json"
        interval = 45.0
        table = build_table(
            changes=changes,
            config_path=config_path,
            interval=interval,
            status_msg="",
        )
        assert config_path in table.caption
        assert f"{interval}s" in table.caption

    def test_build_table_no_title(self) -> None:
        """TC-004: Table no longer has a title (moved to header Panel)."""
        changes: list[TrackedChange] = []
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            ssh_requests=42,
        )
        # Table title should be empty/None since we moved it to header Panel
        assert table.title is None or table.title == "", "Table should have no title"


# ---------------------------------------------------------------------------
# build_layout function (TC-005 to TC-008)
# ---------------------------------------------------------------------------


class TestBuildLayout:
    """Tests for the new build_layout function."""

    def test_build_layout_no_active_input(self) -> None:
        """TC-005: Layout with no active input (prompt=None).

        Returns a Group with 2 renderables: header + table (no prompt line).
        """
        changes: list[TrackedChange] = []
        header = build_header(ssh_requests=5)
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints="Space Changes, q quit, r refresh, f fetch",
        )

        layout = build_layout(header, table, prompt=None)

        assert isinstance(layout, Group), "build_layout should return a Group"
        assert len(layout.renderables) == 2, "Group should have 2 items: header + table (no prompt)"

    def test_build_layout_empty_prompt_string(self) -> None:
        """TC-006: Layout with empty prompt string.

        Empty string treated same as None — no prompt line.
        """
        changes: list[TrackedChange] = []
        header = build_header(ssh_requests=3)
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints="Space Changes, q quit, r refresh",
        )

        layout = build_layout(header, table, prompt="")

        assert isinstance(layout, Group)
        assert len(layout.renderables) == 2, "Empty prompt should be treated as None (2 items)"

    def test_build_layout_with_active_input(self) -> None:
        """TC-007: Layout with active input.

        Returns a Group with 3 renderables: header + prompt Text + table.
        """
        changes: list[TrackedChange] = []
        header = build_header(ssh_requests=2)
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints="Space Changes, q quit, r refresh",
        )
        prompt_text = "add > hash: abc_ ESC=cancel"

        layout = build_layout(header, table, prompt=prompt_text)

        assert isinstance(layout, Group)
        assert len(layout.renderables) == 3, "Group should have 3 items: header + prompt + table"

    def test_build_layout_prompt_is_bold_yellow(self) -> None:
        """TC-008: Prompt text is styled with bold yellow.

        The second renderable (when prompt exists) is a Text with bold yellow style.
        """
        changes: list[TrackedChange] = []
        header = build_header(ssh_requests=1)
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints="Space Changes",
        )
        prompt_text = "add > hash: abc_"

        layout = build_layout(header, table, prompt=prompt_text)

        prompt_renderable = layout.renderables[1]
        assert isinstance(prompt_renderable, Text), "Second item should be a Text (prompt)"
        assert prompt_renderable.style == "bold yellow", "Prompt should have bold yellow style"


# ---------------------------------------------------------------------------
# build_header function (TC-009 to TC-011)
# ---------------------------------------------------------------------------


class TestBuildHeader:
    """Tests for the new build_header function."""

    def test_build_header_returns_panel(self) -> None:
        """TC-009: build_header returns a Panel."""
        header = build_header(ssh_requests=5)
        assert isinstance(header, Panel), "build_header should return a Panel"

    def test_build_header_contains_timestamp(self) -> None:
        """TC-010: Header Panel contains 'refreshed' timestamp."""
        header = build_header(ssh_requests=5)
        # The header is a Panel with a Text renderable inside
        assert isinstance(header, Panel), "Header should be a Panel"
        # Access the Panel's renderable (the Text inside)
        assert "refreshed" in str(header.renderable).lower(), "Header should contain refreshed timestamp"

    def test_build_header_contains_ssh_count(self) -> None:
        """TC-011: Header Panel contains SSH request count."""
        ssh_count = 42
        header = build_header(ssh_requests=ssh_count)
        assert isinstance(header, Panel), "Header should be a Panel"
        assert "ssh requests: 42" in str(header.renderable), "Header should contain SSH request count"


# ---------------------------------------------------------------------------
# Integration tests with App.build() (TC-009 to TC-012)
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests: App.build() returns a Group with header, optional prompt, and table."""

    def test_app_build_returns_group_not_table(self) -> None:
        """TC-012: App.build() returns a Group (not a Table).

        This verifies the integration where build_layout composes a Group.
        """
        changes: list[TrackedChange] = []
        header = build_header(ssh_requests=3)
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints="Space Changes, q quit",
        )
        prompt = "add > hash: abc123"

        layout = build_layout(header, table, prompt=prompt)

        assert isinstance(layout, Group), "build_layout must return a Group for App.build() integration"

    def test_prompt_disappears_when_empty(self) -> None:
        """TC-013: When prompt is empty, layout has header + table (no prompt line)."""
        header = build_header(ssh_requests=2)
        changes: list[TrackedChange] = []
        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints="Space Changes, q quit",
        )

        # First with prompt
        layout_with_prompt = build_layout(header, table, prompt="add > hash: abc_")
        assert len(layout_with_prompt.renderables) == 3

        # Then without prompt (empty)
        layout_without_prompt = build_layout(header, table, prompt="")
        assert len(layout_without_prompt.renderables) == 2

    def test_hints_in_table_caption(self) -> None:
        """TC-014: Hints are in table caption (at bottom of table)."""
        changes: list[TrackedChange] = []
        hints = "[bold]Space[/] Changes  [bold]q[/] quit"

        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            hints=hints,
        )

        assert hints in table.caption, "Hints should be in table caption"

    def test_status_message_in_caption(self) -> None:
        """TC-015: Status message appears in table caption."""
        changes: list[TrackedChange] = []
        status_msg = "Config reloaded"

        table = build_table(
            changes=changes,
            config_path="/path/to/config.json",
            interval=30.0,
            status_msg=status_msg,
            hints="Space Changes",
        )

        assert status_msg in table.caption, "Status message should be in table caption"
