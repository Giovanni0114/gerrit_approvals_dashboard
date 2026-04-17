# EPIC001-004 — Test Cases

## TC-001: query_review_restore builds correct SSH command

Verify command ends with `gerrit review <rev> --restore`.

## TC-002: query_review_restore success

rc=0 → `{"success": True}`.

## TC-003: query_review_restore error

rc=1 stderr="not abandoned" →
`{"error": "Gerrit review failed (not abandoned)"}`.

## TC-004: query_review_restore timeout

TimeoutExpired → `{"error": "SSH timeout"}`.

## TC-005: App.review_restore happy path

Mock success, verify green status + `_start_refresh` called.

## TC-006: App.review_restore missing revision

`current_revision=None` → no SSH call, red status.

## TC-007: App.review_restore error propagates

Mock error → red status, WARNING log.

## TC-008: Handler driven via InputHandler

`" "`, `r`, `1`, `<enter>`, `R`. Verify `app_ctx.review_restore(1)` called
once.

## TC-009: Capital R distinct from lowercase

Driving `" "`, `r`, `1`, `<enter>`, `r` (lowercase) does NOT trigger
restore. (If lowercase `r` is not registered, should produce the
"Invalid option" error.)

## TC-010: No confirmation prompt

`prompt()` after `R` does not include `y / n`.
