# EPIC001-003 — Test Cases

## TC-001: query_review_rebase builds correct SSH command

Mock `subprocess.run`. Call `query_review_rebase("abc", "host", 29418)`.
Verify command ends with `gerrit review abc --rebase`.

## TC-002: query_review_rebase success

Mock rc=0. Verify return `{"success": True}`.

## TC-003: query_review_rebase error

Mock rc=1 with stderr "merge conflict". Verify
`{"error": "Gerrit review failed (merge conflict)"}`.

## TC-004: query_review_rebase timeout

`subprocess.run` raises `TimeoutExpired`. Verify `{"error": "SSH timeout"}`.

## TC-005: App.review_rebase happy path

Fake change with `current_revision="abc"`, known instance. Mock
`query_review_rebase` → success. Call `app.review_rebase(1)`. Verify
`status_msg` is green, `_start_refresh` called once.

## TC-006: App.review_rebase missing revision

`current_revision=None`. Verify SSH wrapper not invoked, red status.

## TC-007: App.review_rebase error propagates

Mock `query_review_rebase` → `{"error": "X"}`. Verify red status and
warning log.

## TC-008: Sub-action has no extra required inputs

Inspect the registered `SubAction`. Verify `required_inputs == []`.

## TC-009: Driving through InputHandler triggers review_rebase

`" "`, `r`, `1`, `<enter>`, `b`. Verify `app_ctx.review_rebase(1)` is called
exactly once without any further input.

## TC-010: No confirmation prompt

After `b` in TC-009, `prompt()` does not contain `y / n`.
