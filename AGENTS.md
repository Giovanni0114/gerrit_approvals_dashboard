# AGENTS.md — Gerrit Approvals Dashboard

## Project Overview

Single-file Python CLI tool (`gerrit_approvals.py`, ~280 lines) that displays a
live-updating terminal dashboard of Gerrit code review approvals using the
[Rich](https://github.com/Textualize/rich) library. Config-file driven, queries
Gerrit via SSH, hot-reloads on config change.

## Repository Layout

```
gerrit_approvals.py      # Entire application (single file)
approvals.json           # Runtime config (gitignored, user-specific)
approvals.schema.json    # JSON Schema for config file
pyproject.toml           # Project metadata + Ruff config
README.md / LICENSE      # Docs + MIT license
```

No subdirectories for source, tests, or docs. Keep new modules at the root.

## Build / Run / Lint / Test Commands

### Dependencies

```bash
pip install rich          # sole runtime dependency
pip install ruff          # linter (dev)
pip install pytest        # test runner (dev, if tests are added)
```

### Running the application

```bash
python gerrit_approvals.py                    # uses default approvals.json
python gerrit_approvals.py path/to/config.json
python gerrit_approvals.py --init             # generate example config
```

### Linting

```bash
ruff check .              # lint (pycodestyle, pyflakes, isort, bugbear, ruff)
ruff check --fix .        # lint and auto-fix
ruff format .             # format (ruff formatter)
ruff format --check .     # check formatting without modifying
```

Both `ruff check .` and `ruff format --check .` must pass before committing.

### Testing

No test suite exists yet. If you add tests:

```bash
pytest                          # run all tests
pytest tests/test_foo.py        # run a single test file
pytest tests/test_foo.py::test_bar   # run a single test function
pytest -x                       # stop on first failure
```

Place test files in a `tests/` directory with `test_` prefix. Use `pytest` as
the framework.

### No CI pipeline

There is no CI/CD configuration. Run lint and tests locally before pushing.

## Code Style Guidelines

### Formatter and Linter: Ruff

All style is enforced by Ruff. Configuration lives in `pyproject.toml`:

- **Line length**: 120 characters max
- **Lint rules**: `E` (pycodestyle), `F` (pyflakes), `I` (isort),
  `B` (flake8-bugbear), `RUF` (ruff-specific)
- **Formatter**: `ruff format` (black-compatible defaults)

Do not add `.flake8`, `.isort.cfg`, or black config files. Ruff handles all of
these.

### Imports

Sorted by `isort` rules via Ruff. Order: (1) standard library, (2) third-party,
(3) local. Separate groups with a blank line. Use `from X import Y` for specific
names; `import X` for modules used with their namespace.

```python
import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text
```

### Naming Conventions

- **Functions/variables**: `snake_case` (`load_config`, `query_approvals`,
  `status_msg`, `last_mtime`)
- **Classes**: `PascalCase` (`Change`)
- **Constants**: `UPPER_SNAKE_CASE` (`DEFAULT_INTERVAL`)
- **Private/internal**: prefix with `_` if not part of the module's public API

### Type Hints

Use modern Python 3.9+ type hint syntax (lowercase generics):

```python
def load_config(path: Path) -> tuple[list[Change], int]: ...
def query_approvals(commit_hash: str, host: str) -> dict: ...
results: dict[str, dict] = {}
```

Do **not** use `typing.List`, `typing.Dict`, `typing.Tuple`, etc. Use the
built-in types directly. Add type hints to all function signatures. Type hints
on local variables are optional but encouraged for complex types.

### Dataclasses and Error Handling

- Return error dicts (`{"error": "message"}`) from functions that may fail
  during data fetching, rather than raising exceptions. This keeps the main
  loop running when individual queries fail.
- Use specific exception types in `except` clauses — never bare `except:`.
- Guard against `subprocess.TimeoutExpired`, `json.JSONDecodeError`, `KeyError`,
  `OSError` as appropriate.
- For fatal config errors, print a message to the console and `sys.exit(1)`.

### String Formatting and Paths

- Use f-strings exclusively. No `.format()` or `%` formatting.
- Use `pathlib.Path` instead of `os.path`. Example: `path.read_text()`,
  `path.stat().st_mtime`, `path.exists()`.

### Functions

- Keep functions focused and short.
- Use default parameter values where sensible (`status_msg: str = ""`).
- Docstrings are not required for every function but are welcome for complex
  logic.

### Rich Library Usage

- Use `Rich` types (`Text`, `Table`, `Console`, `Live`) for all terminal output.
- Apply styles via Rich markup (`[red]...[/red]`) or `Text(style="...")`.
- Color-coded approval values: +2 bold green, +1 green, 0 dim, -1 yellow,
  -2 bold red.

## JSON Config Schema

The config file (`approvals.json`) is validated against `approvals.schema.json`
(JSON Schema draft-07). When modifying config structure, update both the schema
and `load_config()` / `generate_example_config()`. Key fields: `changes`
(required array), `interval` (optional int, min 1, default 30), `default_host`
(optional string). Each change has a required `hash` and optional `host`.

## Git Conventions

- Branch: `master`
- Keep commits small and descriptive
- `.gitignore` excludes `approvals.json` (user config) and `__pycache__/`
- Do not commit `approvals.json` — it contains user-specific Gerrit hosts and
  commit hashes
