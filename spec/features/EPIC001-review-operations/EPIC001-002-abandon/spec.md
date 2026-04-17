# EPIC001-002 — Abandon a Change

## Requirements

1. Add `query_review_abandon(revision: str, host: str, port: int | None =
   None) -> dict` in `gerrit.py`, modeled on `query_set_automerge`. Shell
   command: `ssh [-p <port>] <host> gerrit review <revision> --abandon`.
2. Log `action=review_abandon endpoint=... revision=... duration=... status=...`
   at INFO on success, WARNING on failure / timeout (same shape as
   `query_set_automerge`).
3. Add `review_abandon(self, row: int) -> None` to `App` in `app.py`:
   - Resolve change via `self.changes.at(row - 1)`; error if missing.
   - Require `ch.current_revision` (error if `None`, same message style as
     `set_automerge`).
   - Resolve instance via `self.config.get_instance_by_name(ch.instance)`.
   - Call `gerrit.query_review_abandon(...)`.
   - On `error` set a red `status_msg` and log warning.
   - On success set a green `status_msg` (e.g. `"Change #<row> abandoned"`)
     and call `self._start_refresh()`.
4. Add `review_abandon` to the `AppContext` Protocol in `models.py`.
5. Register a review sub-action in `REVIEW_SUBACTIONS`:
   ```python
   "a": SubAction(review_abandon_action, [CONFIRM_FIELD]),
   ```
6. Add a handler in `input_handler.py`:
   ```python
   def review_abandon_action(app_ctx: AppContext, ctx: Context) -> None:
       if ctx.get("confirm") != "y":
           app_ctx.status_msg = "[yellow]Abandon cancelled[/yellow]"
           return
       idx = int(ctx["idx"])
       app_ctx.review_abandon(idx)
   ```
7. Extend `InputHandler.prompt()` / `PROMPTS_FOR_LAST_KEY` so the confirm
   prompt reads something like `Abandon change #<idx>? [y / n]`.
   - Simplest: add `"a": "Abandon change"` (or similar) to
     `PROMPTS_FOR_LAST_KEY` — acceptable since the sub-action key is
     unique inside the review submenu.
   - Alternative: compute hint from the active sub-action. Pick whichever
     requires fewer changes to the existing prompt rendering.

## Acceptance Criteria

- `<Space>` + `r` + `<idx>` + `a` + `y` runs `gerrit review <rev> --abandon`
  against the correct host/port and reports success.
- `<Space>` + `r` + `<idx>` + `a` + `n` (or `<esc>` partway through) does
  NOT run the SSH command and sets a neutral/cancel status.
- When `ch.current_revision is None`, no SSH is attempted and the user sees
  a red status.
- On SSH failure, status is red and the error is logged at WARNING.
- On success, `_start_refresh()` is triggered so approvals reflect the new
  state.
- Confirmation prompt visibly shows the change identifier (number or row
  index) so the user does not abandon the wrong change.
- Abandoning via the submenu does not touch `changes.json` directly — the
  subsequent refresh updates state.

## Out of Scope

- Recording a custom abandon reason (`--message`) — future enhancement.
- Multi-index batch abandon — see EPIC001 spec Open Questions.
