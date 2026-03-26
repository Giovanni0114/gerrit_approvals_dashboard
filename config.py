import json
from pathlib import Path

from models import Change

DEFAULT_INTERVAL = 30


def load_config(path: Path) -> tuple[list[Change], int, str | None]:
    data = json.loads(path.read_text())
    interval = int(data.get("interval", DEFAULT_INTERVAL))
    if interval < 1:
        raise ValueError(f"interval must be >= 1, got {interval}")
    default_host = data.get("default_host", None)
    changes = []
    for entry in data.get("changes", []):
        host = entry.get("host", default_host)
        commit_hash = entry["hash"]
        if not host:
            raise ValueError(f"Change '{commit_hash}' has no host and no default_host is set")
        changes.append(
            Change(
                host=host,
                hash=commit_hash,
                waiting=bool(entry.get("waiting", False)),
                disabled=bool(entry.get("disabled", False)),
            )
        )
    return changes, interval, default_host


def config_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def generate_example_config(path: Path) -> None:
    example = {
        "$schema": "./approvals.schema.json",
        "interval": 30,
        "changes": [
            {"host": "gerrit.example.com", "hash": "REPLACE_WITH_COMMIT_HASH"},
            {"host": "gerrit.example.com", "hash": "ANOTHER_HASH", "waiting": True},
        ],
    }
    path.write_text(json.dumps(example, indent=2) + "\n")


def update_config_field(path: Path, commit_hash: str, field: str, value: object) -> float:
    """Set field=value for the entry matching commit_hash. Returns new mtime.

    Only used for 'waiting' and 'disabled' fields (NOT 'deleted' which is in-memory only).
    """
    data = json.loads(path.read_text())
    for entry in data.get("changes", []):
        if entry.get("hash") == commit_hash:
            entry[field] = value
    path.write_text(json.dumps(data, indent=2) + "\n")
    return config_mtime(path)


def add_change_to_config(path: Path, commit_hash: str, host: str) -> float:
    """Append a new change entry to the config file. Returns new mtime."""
    data = json.loads(path.read_text())
    data.setdefault("changes", []).append({"hash": commit_hash, "host": host})
    path.write_text(json.dumps(data, indent=2) + "\n")
    return config_mtime(path)


def remove_changes_from_config(path: Path, hashes: set[str]) -> float:
    """Remove entries matching hashes from config file. Returns new mtime.

    Caller is responsible for also cleaning up in-memory caches (results, prev_approvals).
    """
    data = json.loads(path.read_text())
    data["changes"] = [e for e in data.get("changes", []) if e.get("hash") not in hashes]
    path.write_text(json.dumps(data, indent=2) + "\n")
    return config_mtime(path)
