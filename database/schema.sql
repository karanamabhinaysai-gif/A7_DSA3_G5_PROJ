-- ============================================================
-- Smart Research Paper Recommendation System — Database Schema
-- ============================================================

-- Papers table: stores research paper metadata
CREATE TABLE IF NOT EXISTS papers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    abstract    TEXT,
    authors     TEXT,
    year        INTEGER,
    keywords    TEXT,
    venue       TEXT,
    doi         TEXT
);

-- Users table: stores user accounts and interest profiles
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    interests     TEXT    DEFAULT ''
);

-- Citations table: directed edges (citing_paper → cited_paper)
CREATE TABLE IF NOT EXISTS citations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper_id INTEGER NOT NULL,
    cited_paper_id  INTEGER NOT NULL,
    FOREIGN KEY (citing_paper_id) REFERENCES papers(id),
    FOREIGN KEY (cited_paper_id)  REFERENCES papers(id),
    UNIQUE(citing_paper_id, cited_paper_id)
);

-- User reading / interaction history
CREATE TABLE IF NOT EXISTS user_history (
    id        INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER  NOT NULL,
    paper_id  INTEGER  NOT NULL,
    action    TEXT     DEFAULT 'viewed',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)  REFERENCES users(id),
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited  ON citations(cited_paper_id);
CREATE INDEX IF NOT EXISTS idx_history_user     ON user_history(user_id);
CREATE INDEX IF NOT EXISTS idx_papers_year      ON papers(year);
