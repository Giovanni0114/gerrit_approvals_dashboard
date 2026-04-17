# EPIC001 — Review Operations on a Change

## Motivation

Today `set automerge` (`<Space>` + `s`) is the only `gerrit review` operation
exposed by the dashboard. The `gerrit review` command supports many more useful
actions: abandon, rebase, restore, submit, code-review score, custom messages.
Users currently must leave the dashboard and run SSH or the web UI to perform
these.

## Scope

This EPIC adds a dedicated **Review submenu** entered via `<Space>` + `r` that
groups review operations behind a consistent `<Space>` + `r` + `<idx>` + `<op>`
flow. It covers:

- Review submenu scaffolding (EPIC001-001)
- Abandon (EPIC001-002)
- Rebase (EPIC001-003)
- Restore (EPIC001-004)
- Set Code-Review score (EPIC001-005)
- Submit (EPIC001-006)
- Move `set automerge` into the submenu (EPIC001-007)

This EPIC does **not** cover:
- Custom free-text review messages
- Multi-label batch operations (setting several labels in one command)
- Draft/private/work-in-progress toggles

## Prerequisites

- **Feature 006** (track latest patchset hash) — **DONE** (merged in PR #6).
  Review commands target `ch.current_revision`, not a stale hash from config.

## Design Overview

### Keybind pattern

The Review submenu follows the existing `MenuAction` pattern already used for
comments (`<Space>` + `c`). The flow is:

```
<Space>  r  <idx>  <op-key>  [extra inputs if required]
```

- `r` enters the submenu (only valid after `<Space>`; bare `r` keeps its
  current refresh behaviour).
- `<idx>` collects a 1-based change index (digits-only field, same as other
  index collectors in `input_handler.py`).
- `<op-key>` is a single-letter sub-action key selected from a new
  `REVIEW_SUBACTIONS: dict[str, SubAction]`.
- Operations that need extra input (Code-Review score) or confirmation
  (abandon, submit) collect an additional field defined on the `SubAction`.

### Key assignments (proposed)

| Op              | Key | Sub-feature   | Needs confirm? | Extra input             |
|-----------------|-----|---------------|----------------|-------------------------|
| Abandon         | `a` | EPIC001-002   | yes            | confirm field           |
| Rebase          | `b` | EPIC001-003   | no             | —                       |
| Restore         | `R` | EPIC001-004   | no             | —                       |
| Code-Review     | `c` | EPIC001-005   | no             | score field (-2..+2)    |
| Submit          | `s` | EPIC001-006   | yes            | confirm field           |
| Automerge +1    | `m` | EPIC001-007   | no             | —                       |

`a`/`R` distinguished by case to avoid collision. Final key assignments may be
revised during implementation — see Open Questions.

### SSH commands

Each sub-feature adds a thin wrapper in `gerrit.py` modeled on
`query_set_automerge()`:

| Function                      | Shell invocation                                  |
|-------------------------------|---------------------------------------------------|
| `query_review_abandon`        | `gerrit review <rev> --abandon`                   |
| `query_review_rebase`         | `gerrit review <rev> --rebase`                    |
| `query_review_restore`        | `gerrit review <rev> --restore`                   |
| `query_review_code_review`    | `gerrit review <rev> --code-review <N>`           |
| `query_review_submit`         | `gerrit review <rev> --submit`                    |

All wrappers share the same shape: build `cmd`, `subprocess.run` with 30s
timeout, log `action=... endpoint=... revision=... duration=... status=...`,
return `{"success": True}` or `{"error": msg}`.

### Confirmation primitive

Abandon and Submit need user confirmation because they are either
user-visible-to-reviewers or irreversible. The codebase has no confirm dialog
today. This EPIC introduces a lightweight confirmation using the existing
`InputField` machinery:

- A `CONFIRM_FIELD = InputField("confirm", frozenset({"y", "n"}))` that accepts
  only `y` / `n` as single-char selections.
- When the field is collected, the action handler checks `ctx["confirm"] == "y"`
  and aborts with a status message otherwise.
- No new UI primitive required — the existing `prompt()` `special_chars` hint
  already renders `[y / n]`.

### AppContext additions

`models.py` extends the `AppContext` Protocol with:

```python
def review_abandon(self, row: int) -> None: ...
def review_rebase(self, row: int) -> None: ...
def review_restore(self, row: int) -> None: ...
def review_code_review(self, row: int, score: int) -> None: ...
def review_submit(self, row: int) -> None: ...
```

All follow the shape of the existing `set_automerge(row)`: resolve change,
validate `current_revision`, resolve instance, call the `gerrit.py` wrapper,
report status, refresh on success.

### Hints and prompts

- Add `[bold]r[/] review` to the leader hints string in
  `InputHandler.hints()`.
- Add a `review` branch to the `pending_sub_actions` prompt rendering (mirrors
  the `comment >` prompt).
- Extend `PROMPTS_FOR_LAST_KEY` as needed (e.g. `"r": "Review"`).

## Sub-Features

| ID           | Name                                     | Deps            |
|--------------|------------------------------------------|-----------------|
| EPIC001-001  | Review submenu scaffolding               | —               |
| EPIC001-002  | Abandon a change                         | 001             |
| EPIC001-003  | Rebase a change                          | 001             |
| EPIC001-004  | Restore an abandoned change              | 001             |
| EPIC001-005  | Set Code-Review score                    | 001             |
| EPIC001-006  | Submit a change                          | 001             |
| EPIC001-007  | Move `set automerge` into submenu        | 001             |

001 is the prerequisite for all others. 002–007 are independent and can be
implemented in any order (or in parallel).

## Implementation Order

1. **EPIC001-001** — scaffolding must land first.
2. **EPIC001-003** (rebase) and **EPIC001-004** (restore) are the simplest
   (no confirm, no extra input) — good candidates to validate the plumbing.
3. **EPIC001-002** (abandon) and **EPIC001-006** (submit) — introduce the
   confirmation field.
4. **EPIC001-005** (code-review) — introduces scored input.
5. **EPIC001-007** (automerge move) — last, since it removes the existing
   `<Space>` + `s` binding.

## Open Questions

1. **Key assignments** — proposed above but not final. In particular:
   - `R` (capital) for restore is unusual in this codebase; swap to another
     letter?
   - Should `<Space>` + `s` be kept as an alias after 007, or removed
     immediately?
2. **Code-Review prompt** — FEATURES.md asks for the "meaning of each value"
   shown during the prompt. Options:
   - Static hint string built into the `special_hint_func`.
   - Config-driven (per-instance meaning) — probably overkill for v1.
3. **Confirmation UX** — is a single `y/n` char sufficient, or should the
   prompt require typing the change number / a word like `yes`? (Gerrit
   itself uses `--abandon` without extra confirm, so `y/n` seems adequate.)
4. **Multi-index operations** — existing index actions accept
   `parse_idx_notation` (`1-3,5`). Should review ops support multi-index
   batches, or require a single change per invocation? Batch makes abandon
   / rebase more useful but complicates confirmation UX. **Initial take:
   single-index only for this EPIC; revisit later.**
