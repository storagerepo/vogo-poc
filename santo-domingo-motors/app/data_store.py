"""
data_store.py
--------------
A tiny file-backed "mock database" layer.

There is no real database / ORM / API for this POC. Every "table" is just a
JSON file living in /data. This module centralizes all reads & writes so the
rest of the codebase (tools, agents) never touches the filesystem directly.

Swap-out point for production:
    Replace the functions in this file with real API/DB calls
    (e.g. Santo Domingo Motors CRM, DMS, or Finance system) and nothing
    else in the codebase needs to change, since agents/tools only depend
    on this module's function signatures.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any

# Use environment variable if set, otherwise fallback to local 'mock_data'
_DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mock_data")
DATA_DIR = os.environ.get("DATA_DIR", _DEFAULT_DATA_DIR)

os.makedirs(DATA_DIR, exist_ok=True)

_LOCK = threading.Lock()


def _path(table: str) -> str:
    return os.path.join(DATA_DIR, f"{table}.json")


def read_table(table: str) -> Any:
    """Read a full JSON 'table' (list or dict) from disk."""
    path = _path(table)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mock table '{table}' not found at {path}")
    with _LOCK:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def write_table(table: str, data: Any) -> None:
    """Overwrite a full JSON 'table' on disk."""
    path = _path(table)
    with _LOCK:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def append_record(table: str, record: dict) -> dict:
    """Append a record to a list-shaped JSON table and persist it."""
    records = read_table(table)
    if not isinstance(records, list):
        raise TypeError(f"Table '{table}' is not list-shaped, cannot append a record")
    records.append(record)
    write_table(table, records)
    return record


def find_one(table: str, predicate) -> dict | None:
    records = read_table(table)
    for r in records:
        if predicate(r):
            return r
    return None


def find_all(table: str, predicate=None) -> list:
    records = read_table(table)
    if predicate is None:
        return records
    return [r for r in records if predicate(r)]
