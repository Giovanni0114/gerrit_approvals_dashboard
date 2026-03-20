# Gerrit Approvals Dashboard

Are you tired with checking over several gerrit changes waiting for CI or
coworkers to approve your changes?

Terminal dashboard for monitoring Gerrit code review approvals, built with
[Rich](https://github.com/Textualize/rich).

## Features

- Live-updating table with configurable refresh interval
- Color-coded approval values (+2 green, +1 light green, 0 dim, -1 yellow, -2 red)
- Clickable Gerrit change numbers (OSC 8 terminal hyperlinks)
- Config-file driven

## Requirements

```
pip install rich
```

## Usage

Reads changes from a JSON file and auto-reloads when the file is modified:

```bash
python gerrit_approvals.py <config file default: approvals.json>
```

Generate an example config:

```bash
python gerrit_approvals.py --init
```

Default config path is `approvals.json`.


## Config file format

```json
{
  "$schema": "./approvals.schema.json",
  "default_host": "gerrit.example.com",
  "interval": 30,
  "changes": [
    {
      "hash": "abc123def456"
    },
    {
      "host": "other-gerrit.example.com",
      "hash": "789abc012def"
    }
  ]
}
```

| Field | Required | Description | Default |
|-------|----------|-------------|---------|
| `interval` | No | Refresh interval in seconds | `30` |
| `default_host` | No | Default host to be used when none is specified | -- |
| `changes` | Yes | Array of changes to track | -- |
| `changes[].host` | Yes | Gerrit SSH host | -- |
| `changes[].hash` | Yes | Git commit hash or change-id | -- |


A JSON schema is provided in `approvals.schema.json`.

## How it works

The dashboard queries Gerrit via SSH:

```
ssh <host> gerrit query --format=json --all-approvals <hash>
```

Results are parsed and displayed in a Rich Live table. The config-file variant
watches the config for modifications (via `mtime` polling) and reloads
automatically - no restart needed.

## Terminal notes

Clickable links use OSC 8 hyperlink sequences. If running inside **tmux**, add
this to your `~/.tmux.conf`:

```
set -ga terminal-features ",*:hyperlinks"
```
