"""
db.py — SQLite database helper functions and CRUD operations.

Provides access to papers, users, citations, bookmarks, and user history tables.
"""

import sqlite3
from typing import Dict, List, Optional, Tuple


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open an SQLite connection with Row factory for dict-like access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db_extensions(conn)
    return conn


import urllib.parse

KNOWN_PAPER_LINKS = {
    # Deep Learning & NLP
    "Attention Is All You Need": {
        "url": "https://arxiv.org/abs/1706.03762",
        "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
    },
    "Deep Residual Learning for Image Recognition": {
        "url": "https://arxiv.org/abs/1512.03385",
        "pdf_url": "https://arxiv.org/pdf/1512.03385.pdf",
    },
    "BERT: Pre-training of Deep Bidirectional Transformers": {
        "url": "https://arxiv.org/abs/1810.04805",
        "pdf_url": "https://arxiv.org/pdf/1810.04805.pdf",
    },
    "Generative Adversarial Networks": {
        "url": "https://arxiv.org/abs/1406.2661",
        "pdf_url": "https://arxiv.org/pdf/1406.2661.pdf",
    },
    "Self-Supervised Learning": {
        "url": "https://arxiv.org/abs/2103.01988",
        "pdf_url": "https://arxiv.org/pdf/2103.01988.pdf",
    },
    "Neural Architecture Search with Reinforcement Learning": {
        "url": "https://arxiv.org/abs/1611.01578",
        "pdf_url": "https://arxiv.org/pdf/1611.01578.pdf",
    },
    "Object Detection with YOLO": {
        "url": "https://arxiv.org/abs/1506.02640",
        "pdf_url": "https://arxiv.org/pdf/1506.02640.pdf",
    },
    "Semantic Segmentation Using Fully Convolutional Networks": {
        "url": "https://arxiv.org/abs/1411.4038",
        "pdf_url": "https://arxiv.org/pdf/1411.4038.pdf",
    },
    "3D Object Recognition from Point Clouds": {
        "url": "https://arxiv.org/abs/1612.00593",
        "pdf_url": "https://arxiv.org/pdf/1612.00593.pdf",
    },
    "Vision Transformers for Image Classification": {
        "url": "https://arxiv.org/abs/2010.11929",
        "pdf_url": "https://arxiv.org/pdf/2010.11929.pdf",
    },
    "Gradient Boosting Machines": {
        "url": "https://arxiv.org/abs/1603.02754",
        "pdf_url": "https://arxiv.org/pdf/1603.02754.pdf",
    },
    "Transfer Learning in Practice": {
        "url": "https://arxiv.org/abs/1911.02685",
        "pdf_url": "https://arxiv.org/pdf/1911.02685.pdf",
    },
    "Federated Learning": {
        "url": "https://arxiv.org/abs/1908.07873",
        "pdf_url": "https://arxiv.org/pdf/1908.07873.pdf",
    },
    "MapReduce": {
        "url": "https://dl.acm.org/doi/10.1145/1327452.1327492",
        "pdf_url": "https://static.googleusercontent.com/media/research.google.com/en//archive/mapreduce-osdi04.pdf",
    },
    "Consensus Algorithms in Distributed Systems": {
        "url": "https://www.usenix.org/system/files/conference/atc14/atc14-paper-ongaro.pdf",
        "pdf_url": "https://www.usenix.org/system/files/conference/atc14/atc14-paper-ongaro.pdf",
    },
    "Container Orchestration with Kubernetes": {
        "url": "https://dl.acm.org/doi/10.1145/2898444.2898462",
        "pdf_url": "",
    },
}


def resolve_paper_links(paper: Optional[Dict]) -> Dict:
    """Enrich paper with direct paper link, PDF link, Google Scholar, and Semantic Scholar links."""
    if not paper or not isinstance(paper, dict):
        return paper

    title = paper.get("title", "")
    doi = paper.get("doi", "") or ""
    stored_url = paper.get("url") or ""
    stored_pdf = paper.get("pdf_url") or ""

    # Check known mapping
    for key, meta in KNOWN_PAPER_LINKS.items():
        if key.lower() in title.lower():
            if not stored_url:
                stored_url = meta.get("url", "")
            if not stored_pdf:
                stored_pdf = meta.get("pdf_url", "")
            break

    encoded_title = urllib.parse.quote(title)
    scholar_url = f"https://scholar.google.com/scholar?q={encoded_title}"
    semantic_url = f"https://www.semanticscholar.org/search?q={encoded_title}"
    arxiv_search = f"https://arxiv.org/search/?query={encoded_title}&searchtype=all"

    # If DOI is an arXiv DOI
    if doi and "arxiv" in doi.lower():
        arxiv_id = doi.split("arXiv.")[-1].split("arxiv.")[-1]
        if not stored_url:
            stored_url = f"https://arxiv.org/abs/{arxiv_id}"
        if not stored_pdf:
            stored_pdf = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    elif doi and not doi.startswith("10.1000/"):
        if not stored_url:
            stored_url = f"https://doi.org/{doi}"

    # Best available primary link (falls back to Google Scholar if no direct URL exists)
    primary_url = stored_url if stored_url else scholar_url

    paper["url"] = primary_url
    paper["pdf_url"] = stored_pdf
    paper["scholar_url"] = scholar_url
    paper["semantic_scholar_url"] = semantic_url
    paper["arxiv_search_url"] = arxiv_search
    return paper


def _row_to_dict(row: sqlite3.Row) -> Optional[Dict]:
    """Convert an sqlite3.Row to a plain dictionary and enrich with paper links."""
    if row is None:
        return None
    d = dict(row)
    if "title" in d:
        d = resolve_paper_links(d)
    return d


def init_db_extensions(conn: sqlite3.Connection) -> None:
    """Ensure additional tables like bookmarks and columns exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            paper_id  INTEGER NOT NULL,
            status    TEXT DEFAULT 'to_read',
            notes     TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            UNIQUE(user_id, paper_id)
        );
        """
    )
    try:
        conn.execute("ALTER TABLE papers ADD COLUMN url TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE papers ADD COLUMN pdf_url TEXT DEFAULT ''")
    except Exception:
        pass
    conn.commit()



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


def get_paper_by_title(conn: sqlite3.Connection, title: str) -> Optional[Dict]:
    """Return a single paper by exact or close title match."""
    cursor = conn.execute(
        "SELECT id, title, abstract, authors, year, keywords, venue, doi "
        "FROM papers WHERE lower(title) = lower(?)",
        (title.strip(),),
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


def insert_paper(
    conn: sqlite3.Connection,
    title: str,
    abstract: str = "",
    authors: str = "",
    year: int = 2024,
    keywords: str = "",
    venue: str = "",
    doi: str = "",
) -> int:
    """Insert a new paper into the papers table and return its ID."""
    cursor = conn.execute(
        """
        INSERT INTO papers (title, abstract, authors, year, keywords, venue, doi)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, abstract, authors, year, keywords, venue, doi),
    )
    conn.commit()
    return cursor.lastrowid


def get_citations(conn: sqlite3.Connection) -> List[Tuple[int, int]]:
    """Return all citations as (citing_paper_id, cited_paper_id) tuples."""
    cursor = conn.execute(
        "SELECT citing_paper_id, cited_paper_id FROM citations"
    )
    return [(r["citing_paper_id"], r["cited_paper_id"]) for r in cursor.fetchall()]


def insert_citation(conn: sqlite3.Connection, citing_paper_id: int, cited_paper_id: int) -> bool:
    """Insert a citation edge if it doesn't already exist."""
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO citations (citing_paper_id, cited_paper_id)
            VALUES (?, ?)
            """,
            (citing_paper_id, cited_paper_id),
        )
        conn.commit()
        return True
    except Exception:
        return False


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


def create_user(
    conn: sqlite3.Connection, username: str, password_hash: str, interests: str = ""
) -> int:
    """Create a new user account and return the new user ID."""
    cursor = conn.execute(
        "INSERT INTO users (username, password_hash, interests) VALUES (?, ?, ?)",
        (username.strip(), password_hash, interests.strip()),
    )
    conn.commit()
    return cursor.lastrowid



def update_user_interests(conn: sqlite3.Connection, user_id: int, interests: str) -> None:
    """Update user's interest profile."""
    conn.execute(
        "UPDATE users SET interests = ? WHERE id = ?",
        (interests, user_id),
    )
    conn.commit()


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


def get_bookmarks(conn: sqlite3.Connection, user_id: int) -> List[Dict]:
    """Return bookmarked papers for a user."""
    cursor = conn.execute(
        """
        SELECT b.id as bookmark_id, b.status, b.notes, b.created_at,
               p.id as paper_id, p.title, p.authors, p.year, p.venue, p.doi
        FROM bookmarks b
        JOIN papers p ON b.paper_id = p.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
        """,
        (user_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def add_bookmark(
    conn: sqlite3.Connection, user_id: int, paper_id: int, status: str = "to_read", notes: str = ""
) -> bool:
    """Add or update a paper in the user's bookmarks."""
    try:
        conn.execute(
            """
            INSERT INTO bookmarks (user_id, paper_id, status, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, paper_id) DO UPDATE SET
                status = excluded.status,
                notes = excluded.notes
            """,
            (user_id, paper_id, status, notes),
        )
        conn.commit()
        return True
    except Exception:
        return False


def remove_bookmark(conn: sqlite3.Connection, user_id: int, paper_id: int) -> bool:
    """Remove a paper from the user's bookmarks."""
    cursor = conn.execute(
        "DELETE FROM bookmarks WHERE user_id = ? AND paper_id = ?",
        (user_id, paper_id),
    )
    conn.commit()
    return cursor.rowcount > 0
