# EPIC001-004 — Restore an Abandoned Change

## Requirements

1. Add `query_review_restore(revision, host, port=None) -> dict` in
   `gerrit.py`. Shell command:
   `ssh [-p <port>] <host> gerrit review <revision> --restore`.
2. Log with `action=review_restore`, same shape as other wrappers.
3. Add `review_restore(self, row: int) -> None` to `App`, modeled on
   `set_automerge`:
   - Resolve change, require `current_revision`, resolve instance.
   - Call `gerrit.query_review_restore(...)`.
   - Red status / WARNING log on `error`, green status + `_start_refresh()`
     on success.
4. Add `review_restore` to `AppContext` in `models.py`.
5. Register in `REVIEW_SUBACTIONS`:
   ```python
   "R": SubAction(review_restore_action, []),
   ```
   Capital `R` so it does not collide with `r` (which is the submenu
   entry key, though not reachable here — capitalisation is for user
   clarity vs lowercase actions).
6. Handler:
   ```python
   def review_restore_action(app_ctx: AppContext, ctx: Context) -> None:
       app_ctx.review_restore(int(ctx["idx"]))
   ```
7. No confirmation — restoring is reversible (another abandon is a single
   keypress away).

## Acceptance Criteria

- `<Space>` + `r` + `<idx>` + `R` runs `gerrit review <rev> --restore` and
  reports success.
- Restoring a non-abandoned change may error at the Gerrit side — dashboard
  surfaces the error unchanged.
- Missing revision / unknown instance cases match `set_automerge`'s error
  messages.
- No confirmation prompt.
- Refresh is triggered on success.

## Out of Scope

- Restore with a message.
- Filtering the `R` sub-action to only appear for abandoned changes
  (always available — Gerrit handles the state check).
