"""SQLite persistence for saved syllabus reviews."""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3

DB_PATH = os.environ.get(
    "SYLLABUS_FORGE_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "syllabus_forge.db"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    title TEXT NOT NULL,
    profile TEXT NOT NULL,
    brief TEXT NOT NULL,
    result_json TEXT NOT NULL,
    score REAL NOT NULL,
    verdict TEXT NOT NULL,
    rating INTEGER,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
"""


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript(SCHEMA)


def save_run(title: str, profile: str, brief: str, result: dict,
             rating=None, notes="") -> int:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO runs (created_at, title, profile, brief, result_json, score, "
            "verdict, rating, notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                dt.datetime.now().isoformat(timespec="seconds"),
                title or "Untitled course",
                profile or "general",
                brief or "",
                json.dumps(result),
                float(result.get("score", {}).get("overall", 0)),
                result.get("score", {}).get("verdict", ""),
                rating,
                notes or "",
            ),
        )
        return cur.lastrowid


def list_runs(limit: int = 50):
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, title, profile, score, verdict, rating, notes "
            "FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_run(run_id: int):
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["result"] = json.loads(data.pop("result_json"))
        return data


def update_run(run_id: int, rating=None, notes=None):
    init_db()
    conn = _connect()
    try:
        if rating is not None:
            conn.execute("UPDATE runs SET rating = ? WHERE id = ?", (rating, run_id))
        if notes is not None:
            conn.execute("UPDATE runs SET notes = ? WHERE id = ?", (notes, run_id))
        conn.commit()
    finally:
        conn.close()
    return get_run(run_id)


def delete_run(run_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        return cur.rowcount > 0
