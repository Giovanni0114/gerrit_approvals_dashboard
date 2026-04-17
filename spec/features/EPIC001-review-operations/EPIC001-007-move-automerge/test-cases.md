# EPIC001-007 — Test Cases

## TC-001: Old <Space>+s binding removed

Send `" "`, `s`. Verify `LEADER_ACTIONS.get("s") is None` and the handler
produces the "key not allowed" / no-op path (no `set_automerge` invocation).

## TC-002: New path invokes automerge

Send `" "`, `r`, `1`, `<enter>`, `m`. Verify `app_ctx.set_automerge(1)` is
called exactly once.

## TC-003: Leader hints no longer mention `s automerge`

After `" "`, `hints()` output does NOT contain the substring
`s[/] automerge`.

## TC-004: Review submenu options include `m automerge`

When the review submenu is active (`pending_sub_actions` set), the rendered
prompt lists `m` as an option labelled "automerge".

## TC-005: SSH command unchanged

Via `query_set_automerge` mock, verify the command produced by the new
path is byte-identical to the command produced by the old path (regression
check).

## TC-006: Already-automerged yellow status preserved

Change with an `Automerge` approval already present. Driving through the
new path yields the existing yellow status
(`Label Automerge already exists`).

## TC-007: Error path preserved

Mock `query_set_automerge` → `{"error": "X"}`. Verify red status and
WARNING log, same as pre-move behaviour.

## TC-008: Refresh still triggered on success

Mock success. Verify `_start_refresh` called, same as pre-move behaviour.

## TC-009: No change to AppContext protocol

`AppContext` still has `set_automerge(row: int) -> None` — no rename,
no signature change.

## TC-010: PROMPTS_FOR_LAST_KEY no longer has stale entry

`"s"` key removed from `PROMPTS_FOR_LAST_KEY` (unless transition alias is
kept).
