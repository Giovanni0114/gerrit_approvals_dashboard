# EPIC001-007 — Move `set automerge` into the Review Submenu

## Requirements

1. Register automerge as a review sub-action in `REVIEW_SUBACTIONS`:
   ```python
   "m": SubAction(set_automerge_action, []),
   ```
   Where `set_automerge_action` is the existing `set_automerge` handler
   from `input_handler.py` (renamed only if needed to fit the review
   sub-action naming). Reuses `AppContext.set_automerge` — no change to
   `app.py`.
2. Remove `"s": LeafAction(set_automerge, ...)` from `LEADER_ACTIONS`.
3. Remove the `s` entry in `PROMPTS_FOR_LAST_KEY` *only if* it was used
   solely for this action. (It is — `"s": "Set Automerge +1"` goes away.)
4. Update `InputHandler.hints()`:
   - Remove `[bold]s[/] automerge` from the leader hint string.
   - Review submenu hint (rendered from `REVIEW_SUBACTIONS`) will include
     `m automerge`.
5. No confirmation — automerge is reversible (setting it again or a
   code-review block supersedes).
6. Keep the `a` / `b` / `R` / `c` / `s` / `m` key layout consistent with
   the EPIC top-level spec.

## Transition / deprecation

FEATURES.md flags the old binding as optionally kept as an alias during a
transition period. **Decision (pending confirmation): remove immediately.**
The dashboard is a personal tool with a single user; keeping dual bindings
adds code and documentation drift for little benefit. Revisit if there is
external adoption.

If a transition alias is desired, keep the `"s"` entry in `LEADER_ACTIONS`
but change the prompt / hint to mention it is deprecated ("Use Space + r +
idx + m instead").

## Acceptance Criteria

- `<Space>` + `s` + `<idx>` no longer invokes automerge (returns the
  `key not allowed in sequence` status or similar harmless error).
- `<Space>` + `r` + `<idx>` + `m` invokes automerge and reports success.
- No behavioural change to the SSH command sent or the approval check
  (`Automerge` label already present → yellow "already exists" status).
- Leader hint line no longer contains `s automerge`.
- Review submenu includes `m automerge`.
- `App.set_automerge` is unchanged; only the keybind path changes.

## Out of Scope

- Changing the `Automerge=+1` default — remains fixed.
- Supporting `Automerge=-1` or other label values.
- Removing the `set_automerge` function / test names — only the binding
  moves.
