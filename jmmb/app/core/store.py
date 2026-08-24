"""
core/store.py

A deliberately tiny JSON read/write helper that plays the role of a
"database" for this POC. Each file under data/ is treated like a table:
either a JSON array of records, or (for loans.json) an object containing
a couple of named collections.

No ORM, no SQL, no schema migrations — just enough persistence for demo
tool calls to feel stateful across a conversation and across runs.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.config import DATA_DIR

_lock = threading.Lock()


def _path(filename: str) -> Path:
    return DATA_DIR / filename


def read(filename: str) -> Any:
    """Load a JSON mock-data file. Returns [] if the file is missing/empty."""
    path = _path(filename)
    if not path.exists():
        return []
    with _lock:
        text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return json.loads(text)


def write(filename: str, data: Any) -> None:
    """Overwrite a JSON mock-data file with `data`."""
    path = _path(filename)
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def append_record(filename: str, record: dict, *, collection_key: str | None = None) -> dict:
    """
    Append `record` to a JSON file that stores a top-level list, or to a
    named sub-collection when the file's top-level shape is an object
    (e.g. loans.json -> {"loan_products": [...], "leads": [...]}).
    """
    data = read(filename)
    if collection_key is not None:
        data.setdefault(collection_key, [])
        data[collection_key].append(record)
    else:
        if not isinstance(data, list):
            raise ValueError(f"{filename} does not hold a top-level list; pass collection_key")
        data.append(record)
    write(filename, data)
    return record


def find_all(filename: str, *, collection_key: str | None = None) -> list[dict]:
    data = read(filename)
    if collection_key is not None:
        return data.get(collection_key, [])
    return data


def find_one(filename: str, predicate, *, collection_key: str | None = None) -> dict | None:
    for record in find_all(filename, collection_key=collection_key):
        if predicate(record):
            return record
    return None
