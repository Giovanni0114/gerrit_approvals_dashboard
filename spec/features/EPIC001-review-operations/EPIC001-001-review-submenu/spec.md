# EPIC001-001 — Review Submenu Scaffolding

## Requirements

1. Add a new `REVIEW_SUBACTIONS: dict[str, SubAction]` in `input_handler.py`,
   initially empty. Sub-features 002–007 register their entries here.
2. Add `"r": MenuAction([IDX_FIELD], REVIEW_SUBACTIONS)` to `LEADER_ACTIONS`.
   Leaves bare `r` (refresh) untouched because `LEADER_ACTIONS` is consulted
   only after `<Space>`.
3. Add `"r"` to `PROMPTS_FOR_LAST_KEY` with value `"Review"`.
4. Extend `InputHandler.hints()`:
   - When `self.sequence[:1] == [" "]`, append `"[bold]r[/] review"` to the
     leader hint string.
5. Extend `InputHandler.prompt()` rendering of `pending_sub_actions` so the
   review submenu shows `"review > <options> [ESC=cancel]"` instead of the
   hardcoded `"comment > ..."` label.
   - Factor the label out of the comment branch (e.g. a small helper that
     picks `comment` vs `review` based on which submenu is active, or store
     the label on the `MenuAction`).
6. Add a `CONFIRM_FIELD = InputField("confirm", frozenset({"y", "n"}))`
   constant in `input_handler.py` for use by sub-features 002 and 006.
7. No change to `match_action` — the existing `MenuAction` handling already
   works for this flow.

## Acceptance Criteria

- Typing `<Space>` + `r` opens the Review submenu and prompts for index.
- After entering a valid index, the submenu prompt shows `review > ...`.
- `REVIEW_SUBACTIONS` is reachable and empty (no options shown until 002–007
  are implemented).
- Bare `r` still triggers a refresh.
- `<Space>` + `r` + `<idx>` + `<esc>` cancels cleanly with no status error.
- `<Space>` + `r` + `<idx>` + invalid-key produces the existing
  "Invalid option. Choose from: ..." status message.
- Hint line shows `r review` alongside the other leader options.
- No regression in `comment` submenu (`<Space>` + `c` still works).
- No change in behaviour for `<Space>` + `s` (automerge) — that moves in
  EPIC001-007, not here.

## Out of Scope

- Implementing any concrete review action (002–007).
- Styling / colouring the submenu hint.
