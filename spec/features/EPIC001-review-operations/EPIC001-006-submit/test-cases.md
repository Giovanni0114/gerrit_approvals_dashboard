# EPIC001-006 — Test Cases

## TC-001: query_review_submit builds correct SSH command

Command ends with `gerrit review <rev> --submit`.

## TC-002: query_review_submit success

rc=0 → `{"success": True}`.

## TC-003: query_review_submit error

rc=1 stderr="needs Code-Review+2" →
`{"error": "Gerrit review failed (needs Code-Review+2)"}`.

## TC-004: query_review_submit timeout

TimeoutExpired → `{"error": "SSH timeout"}`.

## TC-005: App.review_submit happy path

Mock success → green status, `_start_refresh` called.

## TC-006: App.review_submit missing revision

`current_revision=None` → red status, SSH not called.

## TC-007: App.review_submit error propagates

Mock `{"error": "X"}` → red status, WARNING log.

## TC-008: Confirm = n skips SSH

`" "`, `r`, `1`, `<enter>`, `s`, `n`. Verify `app_ctx.review_submit` NOT
called, yellow/neutral "cancelled" status.

## TC-009: Confirm = y calls submit

`" "`, `r`, `1`, `<enter>`, `s`, `y`. Verify `app_ctx.review_submit(1)`
called exactly once.

## TC-010: ESC aborts confirm

`" "`, `r`, `1`, `<enter>`, `s`, `<esc>`. Verify submit NOT called, handler
reset.

## TC-011: Confirm prompt warns about irreversibility

While the `s` sub-action is awaiting confirm, `prompt()` contains the word
`irreversible` (or equivalent, e.g. `cannot be undone`) AND the change row
number.

## TC-012: <Space>+s automerge still works pre-EPIC001-007

Driving `" "`, `s`, `1`, `<enter>` triggers `set_automerge(1)`. Confirms
this feature does not touch the existing binding.
