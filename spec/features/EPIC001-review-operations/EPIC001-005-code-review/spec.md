# EPIC001-005 — Set Code-Review Score

## Requirements

1. Add `query_review_code_review(revision, score: int, host, port=None) ->
   dict` in `gerrit.py`. Shell command:
   `ssh [-p <port>] <host> gerrit review <revision> --code-review <N>` where
   `N` is the signed integer score (Gerrit accepts `-2`, `-1`, `0`, `+1`,
   `+2`; `+` sign is optional on the wire — send the bare signed int).
   - Reject out-of-range scores (`abs(score) > 2`) before invoking SSH with
     a `ValueError`, or let the caller validate. Preferred: caller
     validates (see step 4) — the `gerrit.py` wrapper stays thin.
2. Log with `action=review_code_review score=<N>`, otherwise same shape as
   other wrappers.
3. Add `review_code_review(self, row: int, score: int) -> None` to `App`:
   - Validate `-2 <= score <= 2`; red status and return otherwise.
   - Resolve change, require `current_revision`, resolve instance.
   - Call `gerrit.query_review_code_review(...)`.
   - Red / WARNING on error, green + `_start_refresh()` on success.
4. Add `review_code_review` to `AppContext` in `models.py`.
5. Add a score input field:
   ```python
   CODE_REVIEW_FIELD = InputField(
       "score",
       special_chars=frozenset({"-2", "-1", "0", "+1", "+2"}),
       special_hint_func=_code_review_hint,
   )
   ```
   Where `_code_review_hint(app_ctx)` returns the meaning of each value:
   ```
   -2=Do not submit, -1=I prefer not, 0=No score, +1=Looks good, +2=Approved
   ```
   (Literal text is a v1 open question; it must be shown per FEATURES.md.)
6. The `special_chars` approach above treats each score as a multi-char
   atomic selection, which the current `_handle_input` does not support
   (it only branches on single-char `key in special_chars`). Options:
   a. Extend `_handle_input` to recognise multi-char sequences in
      `special_chars` — generalises beyond this feature but is a bigger
      change.
   b. Use a normal typed field (`digits_only=False`) and validate numerically
      in the handler. Simpler; preferred for v1.
   Pick **(b)** unless (a) is explicitly requested. See Open Questions.
7. Register:
   ```python
   "c": SubAction(review_code_review_action, [SCORE_FIELD]),
   ```
8. Handler:
   ```python
   def review_code_review_action(app_ctx: AppContext, ctx: Context) -> None:
       raw = ctx["score"].strip()
       try:
           score = int(raw)
       except ValueError:
           app_ctx.status_msg = f"[red]Invalid score: {raw}[/red]"
           return
       if score < -2 or score > 2:
           app_ctx.status_msg = f"[red]Score out of range: {score}[/red]"
           return
       app_ctx.review_code_review(int(ctx["idx"]), score)
   ```
9. `PROMPTS_FOR_LAST_KEY["c"]` (inside review submenu) — since `c` is also
   the comment leader outside the submenu, the prompt lookup must not
   collide. Options:
   - Use a sub-action-specific hint; do not rely on `PROMPTS_FOR_LAST_KEY`.
   - Or key `PROMPTS_FOR_LAST_KEY` by `(menu_label, key)` — too invasive.
   Preferred: compute the hint from the active sub-action (pair this with
   the EPIC001-001 prompt refactor).

## Acceptance Criteria

- `<Space>` + `r` + `<idx>` + `c` prompts for a score with the value
  meanings visible.
- Valid scores (-2..+2, with optional `+`) invoke
  `gerrit review <rev> --code-review N` and succeed.
- Out-of-range or non-numeric input shows a red status and does NOT call
  SSH.
- Success triggers a refresh.
- Missing revision / unknown instance match `set_automerge` error shape.
- Score of `0` is accepted (clears any existing score).

## Open Questions

- Should the prompt list meanings statically or fetch them from the Gerrit
  project config (`labels.Code-Review.values`)? Static is simpler; fetching
  per instance is a future enhancement.
- Should we accept `-2..+2` with the `+` sign verbatim, or normalise to
  a bare int before sending to Gerrit? (Gerrit accepts both — pass the int
  directly; formatting is the wrapper's concern.)

## Out of Scope

- Other labels (Verified, Automerge etc.) — handled elsewhere.
- Bulk scoring of multiple changes in one prompt.
