import json
import sqlite3
import time
import uuid
from contextlib import contextmanager

DB_PATH = "osint_cases.db"


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                name TEXT,
                purpose TEXT,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id TEXT PRIMARY KEY,
                case_id TEXT,
                target TEXT,
                target_type TEXT,
                created_at REAL,
                results TEXT,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            )
        """)


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_case(name: str, purpose: str) -> str:
    """purpose is the scope/consent note — logged locally for accountability."""
    case_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO cases (id, name, purpose, created_at) VALUES (?, ?, ?, ?)",
            (case_id, name, purpose, time.time()),
        )
    return case_id


def add_search(case_id: str, target: str, target_type: str, results: dict) -> str:
    search_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO searches (id, case_id, target, target_type, created_at, results) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (search_id, case_id, target, target_type, time.time(), json.dumps(results)),
        )
    return search_id


def get_case(case_id: str):
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        case = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not case:
            return None
        searches = conn.execute("SELECT * FROM searches WHERE case_id = ?", (case_id,)).fetchall()
        return {
            "id": case["id"],
            "name": case["name"],
            "purpose": case["purpose"],
            "created_at": case["created_at"],
            "searches": [
                {
                    "id": s["id"],
                    "target": s["target"],
                    "target_type": s["target_type"],
                    "created_at": s["created_at"],
                    "results": json.loads(s["results"]),
                }
                for s in searches
            ],
        }


def list_cases() -> list:
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        return [{"id": r["id"], "name": r["name"], "created_at": r["created_at"]} for r in rows]
