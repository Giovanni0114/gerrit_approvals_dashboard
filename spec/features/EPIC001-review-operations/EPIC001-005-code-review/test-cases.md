# EPIC001-005 — Test Cases

## TC-001: query_review_code_review builds correct SSH command for +2

Mock `subprocess.run`. Call with `score=2`. Verify command ends with
`gerrit review <rev> --code-review 2`.

## TC-002: query_review_code_review handles negative score

Call with `score=-1`. Command ends with `--code-review -1`.

## TC-003: query_review_code_review handles zero

Call with `score=0`. Command ends with `--code-review 0`.

## TC-004: query_review_code_review success

rc=0 → `{"success": True}`.

## TC-005: query_review_code_review error

rc=1 stderr="invalid label" →
`{"error": "Gerrit review failed (invalid label)"}`.

## TC-006: query_review_code_review timeout

TimeoutExpired → `{"error": "SSH timeout"}`.

## TC-007: App.review_code_review validates range — below

`score=-3` → red status, SSH not called.

## TC-008: App.review_code_review validates range — above

`score=3` → red status, SSH not called.

## TC-009: App.review_code_review happy path

`score=2`, valid change, mock success. Verify green status + refresh.

## TC-010: App.review_code_review missing revision

`current_revision=None` → red status, SSH not called.

## TC-011: Handler parses leading + sign

Input `"+1"` to the score field. Handler calls `review_code_review(..., 1)`.

## TC-012: Handler rejects non-numeric input

Input `"abc"` → red `Invalid score` status, `review_code_review` NOT called.

## TC-013: Handler rejects out-of-range input

Input `"5"` → red `Score out of range` status, `review_code_review` NOT
called.

## TC-014: Score prompt surfaces meanings

Collect the rendered prompt when the score field is active. Verify it
contains the strings `-2`, `-1`, `0`, `+1`, `+2` and a description for each
(e.g. `Approved`, `Do not submit`).

## TC-015: Driving full sequence through InputHandler

`" "`, `r`, `1`, `<enter>`, `c`, `+`, `2`, `<enter>`. Verify
`app_ctx.review_code_review(1, 2)` is called.
