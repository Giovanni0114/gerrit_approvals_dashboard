# EPIC001-006 — Submit a Change

## Requirements

1. Add `query_review_submit(revision, host, port=None) -> dict` in
   `gerrit.py`. Shell command:
   `ssh [-p <port>] <host> gerrit review <revision> --submit`.
2. Log with `action=review_submit`.
3. Add `review_submit(self, row: int) -> None` to `App`, mirroring
   `set_automerge`:
   - Resolve change, require `current_revision`, resolve instance.
   - Call `gerrit.query_review_submit(...)`.
   - Red / WARNING on error, green + `_start_refresh()` on success.
4. Add `review_submit` to `AppContext` in `models.py`.
5. Register:
   ```python
   "s": SubAction(review_submit_action, [CONFIRM_FIELD]),
   ```
   (Inside the review submenu; does not collide with the top-level
   `<Space>` + `s` automerge binding until EPIC001-007 moves it.)
6. Handler mirrors abandon:
   ```python
   def review_submit_action(app_ctx: AppContext, ctx: Context) -> None:
       if ctx.get("confirm") != "y":
           app_ctx.status_msg = "[yellow]Submit cancelled[/yellow]"
           return
       idx = int(ctx["idx"])
       app_ctx.review_submit(idx)
   ```
7. Confirmation prompt should make the irreversibility explicit, e.g.
   `Submit change #<idx>? This is irreversible [y / n]`.

## Acceptance Criteria

- `<Space>` + `r` + `<idx>` + `s` + `y` submits the change and reports
  success.
- `n` or `<esc>` during confirm aborts without SSH call.
- Missing revision / unknown instance match other review ops.
- Gerrit errors (e.g. missing required labels) bubble up as red status
  with stderr text.
- Success triggers `_start_refresh()` so the change flips to submitted /
  disappears from the active list.
- Confirmation prompt contains the word `irreversible` (or equivalent
  strong warning) and the change row number.

## Out of Scope

- Submitting with a message (`--message`).
- Batch submit (multiple changes in one invocation).
