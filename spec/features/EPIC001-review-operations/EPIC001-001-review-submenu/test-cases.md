# EPIC001-001 — Test Cases

## TC-001: Bare `r` still refreshes

Send key `r` with an empty sequence. Verify `match_action(["r"])` returns
`REFRESH_ACTION` and no submenu is entered.

## TC-002: `<Space>` + `r` enters the review submenu

Send keys `" "`, `r`. Verify `match_action([" ", "r"])` returns the
`MenuAction` registered under `"r"` in `LEADER_ACTIONS`.

## TC-003: Index is collected before sub-action

After `" "`, `r`, the handler enters input mode with `current_field.name ==
"idx"`. Sub-actions are not yet queried.

## TC-004: Valid index shows review submenu prompt

Send `" "`, `r`, `3`, `<enter>`. Verify `pending_sub_actions` is the
`REVIEW_SUBACTIONS` dict and `InputHandler.prompt()` contains `review >`
(not `comment >`).

## TC-005: ESC cancels submenu cleanly

After `" "`, `r`, `3`, `<enter>`, send `<esc>`. Verify
`pending_sub_actions is None`, `sequence == []`, and no status error was
set.

## TC-006: Invalid sub-action key shows error

With `REVIEW_SUBACTIONS` populated with key `"x"` (test-only), send
`" "`, `r`, `3`, `<enter>`, then `z` (not a valid key). Verify status_msg
matches `"Invalid option. Choose from: ..."` and the handler resets.

## TC-007: `r review` appears in leader hints

After sending `" "`, call `hints()`. Verify the returned string contains
`"r[/] review"` substring.

## TC-008: Empty REVIEW_SUBACTIONS does not crash

With `REVIEW_SUBACTIONS == {}`, send `" "`, `r`, `3`, `<enter>`. Verify no
exception. The prompt may show an empty options list — acceptable for this
intermediate state.

## TC-009: Comment submenu unchanged

Send `" "`, `c`, `1`, `<enter>`. Verify `pending_sub_actions` is
`COMMENT_SUBACTIONS` and prompt starts with `comment >`.

## TC-010: Automerge `<Space>` + `s` unchanged

Send `" "`, `s`, `1`, `<enter>`. Verify the `set_automerge` action fires
(or attempts to) — confirms this feature does not disturb the existing
binding (that moves in EPIC001-007).

## TC-011: CONFIRM_FIELD accepts only y / n

Create an `InputField` equal to `CONFIRM_FIELD`. Verify `special_chars ==
frozenset({"y", "n"})` and no other chars are accepted as single-press
selections (pressing any other non-digit char appends to `input` instead).
