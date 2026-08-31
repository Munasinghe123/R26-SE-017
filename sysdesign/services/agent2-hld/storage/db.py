"""
HLA Agent — SQLite Storage
Logs all runs, candidates, and scores for historical comparison.
"""

import sqlite3
import json
import uuid
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


def _get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create database tables if they don't exist, and migrate missing columns."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            project TEXT NOT NULL,
            input_json TEXT,
            status TEXT DEFAULT 'running',
            total_candidates INTEGER DEFAULT 0,
            winner_model TEXT,
            winner_cas REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            model TEXT NOT NULL,
            candidate_num INTEGER NOT NULL,
            architecture_style TEXT,
            detected_style TEXT,
            architecture_json TEXT,
            rts REAL, qac REAL, ci REAL, cos REAL, ssm1 REAL, ssm2 REAL,
            cas REAL,
            verdict TEXT,
            rank INTEGER,
            FOREIGN KEY (run_id) REFERENCES runs(run_id)
        )
    """)

    conn.commit()

    # ── Schema migration: add any columns missing from older DB files ────────
    # SQLite does not support IF NOT EXISTS in ALTER TABLE, so we check first.
    existing_cols = {
        row[1] for row in cursor.execute("PRAGMA table_info(candidates)").fetchall()
    }
    migrations = {
        "detected_style":    "TEXT DEFAULT ''",
        "architecture_style":"TEXT DEFAULT ''",
        "rts":               "REAL DEFAULT 0",
        "qac":               "REAL DEFAULT 0",
        "ci":                "REAL DEFAULT 0",
        "cos":               "REAL DEFAULT 0",
        "ssm1":              "REAL DEFAULT 0",
        "ssm2":              "REAL DEFAULT 0",
        "cas":               "REAL DEFAULT 0",
        "verdict":           "TEXT DEFAULT ''",
        "rank":              "INTEGER DEFAULT 0",
    }
    for col, col_def in migrations.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE candidates ADD COLUMN {col} {col_def}")
            logger.info(f"DB migration: added column candidates.{col}")

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


def create_run(project: str, input_json: dict, run_id: str = None) -> str:
    """Create a new run entry. Returns run_id."""
    run_id = run_id or str(uuid.uuid4())
    conn = _get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO runs (run_id, timestamp, project, input_json) VALUES (?, ?, ?, ?)",
        (run_id, datetime.now().isoformat(), project, json.dumps(input_json))
    )
    conn.commit()
    conn.close()
    return run_id


def insert_run(run_id: str, project: str, input_json_str: str):
    """Insert a new run entry by run_id (alias used by main.py)."""
    conn = _get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO runs (run_id, timestamp, project, input_json) VALUES (?, ?, ?, ?)",
        (run_id, datetime.now().isoformat(), project, input_json_str)
    )
    conn.commit()
    conn.close()


def update_run(run_id: str, **kwargs):
    """Update run fields."""
    conn = _get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [run_id]
    conn.execute(f"UPDATE runs SET {sets} WHERE run_id = ?", vals)
    conn.commit()
    conn.close()


def insert_candidate(run_id: str, model: str, candidate_num: int,
                     architecture: dict, scores: dict, rank: int):
    """Insert a scored candidate into the database. Returns the row ID."""
    conn = _get_connection()
    cursor = conn.execute("""
        INSERT INTO candidates
        (run_id, model, candidate_num, architecture_style, detected_style, architecture_json,
         rts, qac, ci, cos, ssm1, ssm2, cas, verdict, rank)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, model, candidate_num,
        architecture.get("architecture_style", ""),
        scores.get("detected_style", ""),
        json.dumps(architecture),
        scores.get("RTS", 0), scores.get("QAC", 0), scores.get("CI", 0),
        scores.get("CoS", 0), scores.get("SSM1", 0), scores.get("SSM2", 0),
        scores.get("CAS", 0),
        scores.get("verdict", ""), rank,
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_run(run_id: str) -> dict:
    """Get a single run by ID."""
    conn = _get_connection()
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_candidates(run_id: str) -> list[dict]:
    """Get all candidates for a run, sorted by rank."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM candidates WHERE run_id = ? ORDER BY rank", (run_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_runs() -> list[dict]:
    """Get all runs, most recent first."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_candidate(candidate_id: int) -> dict:
    """Get a single candidate by its ID."""
    conn = _get_connection()
    row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# Initialize DB on import
init_db()
