# EPIC001-003 — Rebase a Change

## Requirements

1. Add `query_review_rebase(revision: str, host: str, port: int | None =
   None) -> dict` in `gerrit.py`. Shell command:
   `ssh [-p <port>] <host> gerrit review <revision> --rebase`.
2. Same logging shape as `query_set_automerge` with
   `action=review_rebase`.
3. Add `review_rebase(self, row: int) -> None` to `App`, mirroring
   `set_automerge`:
   - Resolve change, require `current_revision`, resolve instance.
   - Call `gerrit.query_review_rebase(...)`.
   - Red status + WARNING log on `error`, green status + `_start_refresh()`
     on success.
4. Add `review_rebase` to `AppContext` in `models.py`.
5. Register in `REVIEW_SUBACTIONS`:
   ```python
   "b": SubAction(review_rebase_action, []),
   ```
6. Handler:
   ```python
   def review_rebase_action(app_ctx: AppContext, ctx: Context) -> None:
       app_ctx.review_rebase(int(ctx["idx"]))
   ```
7. No confirmation — rebase is reversible (another rebase or manual push can
   recover).

## Acceptance Criteria

- `<Space>` + `r` + `<idx>` + `b` runs `gerrit review <rev> --rebase` and
  reports success.
- On Gerrit error (e.g. merge conflict), status is red and logs a warning
  with the stderr text.
- Missing revision / unknown instance cases match the error messages of
  `set_automerge`.
- Rebase does not ask for confirmation.
- Approvals refresh is triggered on success.

## Out of Scope

- Specifying a base commit / parent for the rebase (`--base`).
- Handling merge-conflict resolution UX — dashboard just surfaces the error.
