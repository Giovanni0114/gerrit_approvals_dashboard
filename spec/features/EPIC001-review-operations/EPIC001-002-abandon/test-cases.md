# EPIC001-002 — Test Cases

## TC-001: query_review_abandon builds correct SSH command

Mock `subprocess.run`. Call `query_review_abandon("abc123", "gerrit.example",
29418)`. Verify the command is
`["ssh", "-x", "-p", "29418", "gerrit.example", "gerrit", "review", "abc123",
"--abandon"]`.

## TC-002: query_review_abandon omits port when None

Call with `port=None`. Verify `-p` and a port value are absent from the
command.

## TC-003: query_review_abandon returns success on rc=0

Mock a `CompletedProcess` with `returncode=0`. Verify return value is
`{"success": True}`.

## TC-004: query_review_abandon returns error on non-zero rc

Mock `returncode=1`, `stderr="permission denied"`. Verify return value is
`{"error": "Gerrit review failed (permission denied)"}`.

## TC-005: query_review_abandon handles timeout

Make `subprocess.run` raise `subprocess.TimeoutExpired`. Verify return value
is `{"error": "SSH timeout"}`.

## TC-006: App.review_abandon rejects missing change

Call `app.review_abandon(99)` where row 99 does not exist. Verify
`status_msg` starts with `[red]cannot find change for row`.

## TC-007: App.review_abandon rejects missing revision

Create a `TrackedChange` with `current_revision=None`. Call `review_abandon`.
Verify SSH wrapper is NOT called and `status_msg` mentions
`no current revision known`.

## TC-008: App.review_abandon rejects missing instance

Point `ch.instance` at an unknown instance. Verify `status_msg` starts with
`[red]cannot find instance`.

## TC-009: App.review_abandon reports gerrit error

Mock `query_review_abandon` to return `{"error": "X"}`. Verify
`status_msg` is red and contains `X`, warning is logged.

## TC-010: App.review_abandon triggers refresh on success

Mock `query_review_abandon` to return `{"success": True}`. Verify
`_start_refresh` is called and `status_msg` is green.

## TC-011: Confirm = n does not call App.review_abandon

Drive input handler through `" "`, `r`, `1`, `<enter>`, `a`, `n`. Verify
`app_ctx.review_abandon` was NOT invoked and a neutral / yellow "cancelled"
status is set.

## TC-012: Confirm = y calls App.review_abandon

Drive `" "`, `r`, `1`, `<enter>`, `a`, `y`. Verify `app_ctx.review_abandon(1)`
was invoked exactly once.

## TC-013: ESC during confirm cancels cleanly

Drive `" "`, `r`, `1`, `<enter>`, `a`, then `<esc>`. Verify handler resets
and `review_abandon` was not called.

## TC-014: Prompt contains change identifier

During the confirm step, `prompt()` returns a string containing the row
number (e.g. `#1`) or change number.
