"""
db.py — SQLite database helper functions.

Provides convenient access to papers, users, citations, and history tables.
"""

import sqlite3
from typing import Dict, List, Optional, Tuple


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open an SQLite connection with Row factory for dict-like access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert an sqlite3.Row to a plain dictionary."""
    if row is None:
        return None
    return dict(row)


def get_all_papers(conn: sqlite3.Connection) -> List[Dict]:
    """Return all papers as a list of dictionaries."""
    cursor = conn.execute(
        "SELECT id, title, abstract, authors, year, keywords, venue, doi FROM papers"
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def get_paper_by_id(conn: sqlite3.Connection, paper_id: int) -> Optional[Dict]:
    """Return a single paper by its ID, or None."""
    cursor = conn.execute(
        "SELECT id, title, abstract, authors, year, keywords, venue, doi "
        "FROM papers WHERE id = ?",
        (paper_id,),
    )
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def search_papers(conn: sqlite3.Connection, query: str) -> List[Dict]:
    """Search papers by title, abstract, or keywords using LIKE."""
    pattern = f"%{query}%"
    cursor = conn.execute(
        "SELECT id, title, abstract, authors, year, keywords, venue, doi "
        "FROM papers WHERE title LIKE ? OR abstract LIKE ? OR keywords LIKE ?",
        (pattern, pattern, pattern),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def get_citations(conn: sqlite3.Connection) -> List[Tuple[int, int]]:
    """Return all citations as (citing_paper_id, cited_paper_id) tuples."""
    cursor = conn.execute(
        "SELECT citing_paper_id, cited_paper_id FROM citations"
    )
    return [(r["citing_paper_id"], r["cited_paper_id"]) for r in cursor.fetchall()]


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[Dict]:
    """Return a user by ID, or None."""
    cursor = conn.execute(
        "SELECT id, username, password_hash, interests FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[Dict]:
    """Return a user by username, or None."""
    cursor = conn.execute(
        "SELECT id, username, password_hash, interests FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def get_user_history(conn: sqlite3.Connection, user_id: int) -> List[int]:
    """Return list of paper IDs the user has interacted with."""
    cursor = conn.execute(
        "SELECT DISTINCT paper_id FROM user_history WHERE user_id = ? "
        "ORDER BY timestamp DESC",
        (user_id,),
    )
    return [r["paper_id"] for r in cursor.fetchall()]


def add_user_history(
    conn: sqlite3.Connection, user_id: int, paper_id: int, action: str = "viewed"
) -> None:
    """Insert a user history record."""
    conn.execute(
        "INSERT INTO user_history (user_id, paper_id, action) VALUES (?, ?, ?)",
        (user_id, paper_id, action),
    )
    conn.commit()
