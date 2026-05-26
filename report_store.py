"""Per-(workspace, user) org report store.

The store backs the `/setreport` flow: paste a prior grant or annual report,
keyed by `(team_id, user_id)`. The LOI drafter is grounded in this content
to write in the org's own voice. The file is git-ignored (`state/`) since
the content is private to each workspace.

This module deliberately has no Slack / Bolt dependency so it can be exercised
from any context — the Slack app, tests, the standalone MCP client, and
`verify.py` all import the same `get_report` / `set_report`.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

STATE_DIR = Path(__file__).parent / "state"
STATE_DIR.mkdir(exist_ok=True)
REPORT_STORE_PATH = STATE_DIR / "org_reports.json"
_STORE_LOCK = threading.Lock()


def _load_store() -> dict:
    if REPORT_STORE_PATH.exists():
        return json.loads(REPORT_STORE_PATH.read_text() or "{}")
    return {}


def _save_store(store: dict) -> None:
    REPORT_STORE_PATH.write_text(json.dumps(store, indent=2))


def _store_key(team_id: str, user_id: str) -> str:
    return f"{team_id}:{user_id}"


def get_report(team_id: str, user_id: str) -> str | None:
    """Return the stored report for this (workspace, user), or None if not set."""
    with _STORE_LOCK:
        return _load_store().get(_store_key(team_id, user_id))


def set_report(team_id: str, user_id: str, report: str) -> None:
    """Store the report for this (workspace, user). Trims whitespace."""
    with _STORE_LOCK:
        store = _load_store()
        store[_store_key(team_id, user_id)] = report.strip()
        _save_store(store)
