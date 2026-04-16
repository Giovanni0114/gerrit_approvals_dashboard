# 017 — SSH data cache

## Problem

`changes.json` mixes user-authored state (number, instance, flags, comments) with
Gerrit-fetched data (`hash`, `submitted`). This causes several issues:

1. **Slow startup** — every launch requires a full SSH round-trip before the
   dashboard can show anything useful, even though the data from the last session
   is almost certainly still valid.
2. **Unnecessary SSH traffic for disabled changes** — `query_disabled_once()`
   queries every disabled change on startup, even if the data was fetched seconds
   ago in a previous session.
3. **Muddled persistence** — the `hash` field in `changes.json` is a Gerrit
   artifact, not user intent. The `submitted` flag is derived from SSH data, not
   toggled by the user. Both leak implementation detail into the user-facing file.

## Solution

Introduce a new `cache.json` file that stores everything returned by SSH queries,
keyed by `(number, instance)`. `changes.json` becomes purely user state.

## Data separation

### `changes.json` (user state) — keeps

| Field      | Type       | Notes                                |
|------------|------------|--------------------------------------|
| `number`   | `int`      | Primary identifier                   |
| `instance` | `str`      | Gerrit instance name                 |
| `comments` | `list[str]`| User-written notes                   |
| `waiting`  | `bool`     | User-toggled flag                    |
| `disabled` | `bool`     | User-toggled flag                    |
| `deleted`  | `bool`     | User-toggled flag                    |

### `changes.json` — removes

| Field       | Moves to   | Reason                              |
|-------------|------------|-------------------------------------|
| `hash`      | cache      | SSH-derived (`currentPatchSet.revision`) |
| `submitted` | cache      | SSH-derived (detected from `SUBM` approval) |

### `cache.json` (SSH data) — new file

Top-level JSON object. Keys are `"<number>:<instance>"` strings.

```json
{
  "12345:default": {
    "subject": "Fix widget rendering",
    "project": "platform/ui",
    "url": "https://gerrit.example.com/c/12345",
    "current_revision": "abc123def456...",
    "submitted": false,
    "approvals": [
      {"label": "Code-Review", "value": "+2", "by": "Alice"},
      {"label": "Verified", "value": "+1", "by": "Jenkins"}
    ]
  }
}
```

The `error` field from `TrackedChange` is **not cached** — errors are transient
and should be re-evaluated on each query.

## New module: `cache.py`

```
class SshCache:
    path: Path
    _entries: dict[str, CacheEntry]
```

### `CacheEntry` dataclass

```python
@dataclass
class CacheEntry:
    subject: str | None
    project: str | None
    url: str | None
    current_revision: str | None
    submitted: bool
    approvals: list[ApprovalEntry]
```

### Key methods

| Method                                      | Description                                                |
|---------------------------------------------|------------------------------------------------------------|
| `__init__(path: Path)`                      | Set path, init empty dict. Does NOT load (explicit `load()` required). |
| `load()`                                    | Read `cache.json` from disk into `_entries`.               |
| `save()`                                    | Write `_entries` to disk as JSON.                          |
| `get(number: int, instance: str) -> CacheEntry \| None` | Lookup by composite key.                    |
| `put(number: int, instance: str, entry: CacheEntry)` | Insert or overwrite entry.                      |
| `evict(keep: set[tuple[int, str]])`         | Remove all keys not in `keep`. Called on startup to prune stale entries. |
| `has(number: int, instance: str) -> bool`   | Check existence without returning data.                    |

### Key format

Internal key: `f"{number}:{instance}"` — simple, readable, unique since
`(number, instance)` is already the logical identity of a tracked change.

## Hydration

"Hydration" means populating `TrackedChange` SSH fields from cached data,
without making an SSH call.

```python
def hydrate(change: TrackedChange, entry: CacheEntry) -> None:
    change.subject = entry.subject
    change.project = entry.project
    change.url = entry.url
    change.current_revision = entry.current_revision
    change.submitted = entry.submitted
    change.approvals = list(entry.approvals)
```

This is a standalone function (in `cache.py`), not a method on either class —
it bridges the two concerns without coupling them.

## Changes to existing modules

### `changes.py`

#### `load_changes()`

- Stop reading `hash` → `current_revision`. Remove the `commit_hash` variable
  and the `current_revision=commit_hash` assignment (and the TODO comment).
- Stop reading `submitted`.

#### `save_changes()`

- Stop writing `hash` (the `if ch.current_revision:` block).
- Stop writing `submitted` (the `if ch.submitted:` block).

### `app.py`

#### `__init__`

- Create `SshCache` instance. Path: sibling of `changes.json`, i.e.
  `self.changes.path.parent / "cache.json"`.
- Call `cache.load()`.
- Evict stale entries: `cache.evict({(ch.number, ch.instance) for ch in self.changes.get_all()})`.
- Hydrate all changes from cache.

#### `_store_result()`

After writing fields to `TrackedChange` (existing logic), also write to cache:

```python
entry = CacheEntry(
    subject=ch.subject,
    project=ch.project,
    url=ch.url,
    current_revision=ch.current_revision,
    submitted=ch.submitted,
    approvals=list(ch.approvals),
)
cache.put(ch.number, ch.instance, entry)
```

The cache is saved to disk at the end of `_do_query()`, after all results are
stored — one write per refresh cycle, not one per change.

#### `_do_query()`

After the `ThreadPoolExecutor` block and before `save_changes()`, add
`self.cache.save()`.

#### `query_disabled_once()`

Change from "query all disabled" to "query disabled that have no cache entry":

```python
def query_disabled_once(self) -> None:
    uncached = [
        ch for ch in self.changes.get_disabled()
        if not self.cache.has(ch.number, ch.instance)
    ]
    self._do_query(uncached)
```

#### Startup sequence (`run()`)

Current:
1. `query_active_changes()`
2. `query_disabled_once()`

After:
1. (cache already loaded and hydrated in `__init__`)
2. `query_active_changes()` — refresh running changes with live SSH data
3. `query_disabled_once()` — only queries disabled changes missing from cache

The dashboard renders immediately after `__init__` with cached data visible,
then updates in-place once SSH queries complete.

#### `reload_config(force=True)`

When changes are reloaded from disk (e.g. after external edit), re-hydrate
from cache so SSH fields aren't lost:

```python
for ch in self.changes.get_all():
    entry = self.cache.get(ch.number, ch.instance)
    if entry:
        hydrate(ch, entry)
```

#### `fetch_open_changes()`

New changes fetched from `query_open_changes()` go through `_store_result()`
which already writes to cache. No additional changes needed beyond what
`_store_result()` already does.

#### `add_change()`

A manually added change has no SSH data yet. No cache entry is created.
It will be populated on the next refresh cycle.

#### `quit()`

No change needed. Cache is saved after each refresh cycle already. The cache
file persists across sessions by design.

### `models.py`

No changes. `TrackedChange` keeps all its fields — they're still needed at
runtime. The change is about *where* those fields are persisted, not whether
they exist in memory.

### `config.py`

Add optional `cache_file` setting to `[config]` section:

```toml
cache_file = "./cache.json"   # default: "cache.json" next to changes_file
```

Follows the same pattern as `changes_file` — relative to config file, with
a sensible default.

## Startup flow (before → after)

### Before

```
load config.toml
load changes.json  →  TrackedChange with number, instance, flags, comments, stale hash
SSH query all running changes  →  populate subject, project, url, approvals, etc.
SSH query all disabled changes →  populate disabled changes too
render dashboard
```

Dashboard is blank until SSH completes.

### After

```
load config.toml
load changes.json  →  TrackedChange with number, instance, flags, comments (no hash)
load cache.json    →  hydrate all TrackedChanges with last-known SSH data
render dashboard   →  immediately shows cached data
SSH query running changes  →  update live data, overwrite cache
SSH query uncached disabled changes  →  only the ones missing from cache
render dashboard   →  updated with fresh data
```

Dashboard shows useful data immediately.

## Edge cases

### First run (no cache file)

`SshCache.load()` treats a missing file as an empty cache. All changes go
through SSH as today. After the first refresh cycle, cache is written.

### Cache file is corrupt

`SshCache.load()` logs a warning and starts with an empty cache. Same
recovery path as first run.

### Change removed from `changes.json` externally

On next `reload_config()`, the eviction step removes orphaned cache entries.

### Multiple changes with same number on different instances

The composite key `"<number>:<instance>"` handles this — each combination
is a distinct cache entry.

### `submitted` flag consistency

`submitted` is now *only* in cache. When changes.json is loaded, `submitted`
defaults to `False` on the `TrackedChange`. Hydration from cache restores it.
If cache is missing, the change appears as non-submitted until the next SSH
query detects it — acceptable since submitted changes are typically deleted
soon after.

## Files changed

| File         | Change                                                   |
|--------------|----------------------------------------------------------|
| `cache.py`   | **New.** `SshCache`, `CacheEntry`, `hydrate()`.         |
| `changes.py` | Remove `hash` and `submitted` from `load/save_changes`. |
| `app.py`     | Init cache, hydrate on startup, write cache in `_do_query`, filter `query_disabled_once`. |
| `config.py`  | Add optional `cache_file` config key.                    |
| `models.py`  | No changes.                                              |

## Out of scope

- **Auto-save / dirty tracking for `changes.json`** — that is feature 018,
  which depends on this feature.
- **LRU / TTL eviction** — the cache is small (one entry per tracked change)
  and fully evicted on startup based on `changes.json`. No time-based
  expiration needed.
- **Cache for `query_open_changes` results** — that query returns a list of
  changes for an email, not data for a specific change. Different access
  pattern, different feature.
