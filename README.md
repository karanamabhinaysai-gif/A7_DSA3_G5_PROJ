# Smart Research Paper Recommendation System

An intelligent recommendation system that delivers **personalized research paper recommendations** by combining text analysis, citation-network algorithms, and user-interest profiling.

**Course Project — KL University, Dept. of Computer Science & Engineering, Section A7**

## Team Members

| Name         | Roll No.     | Role                        |
|--------------|--------------|-----------------------------|
| Abhinay Sai  | 2510030103   | Project Lead & Integration  |
| K V Srinath  | 2510030106   | Backend & Database          |
| Poli Naidu   | 2510030160   | ML & NLP Engine             |
| Chandu       | 2510030083   | Graph Algorithms & QA       |

---

## Features

- **Multi-Signal Recommendations** — fuses content similarity, citation analysis, and user interests
- **TF-IDF + Cosine Similarity** — content-based relevance scoring on paper abstracts
- **Citation Graph Analysis** — NetworkX-powered PageRank and citation-neighbor discovery
- **User Interest Matching** — profile-based personalization with reading-history boost
- **Weighted Fusion Ranking** — configurable weights produce a unified Top-K list
- **Java Swing UI** — login, search, results display, and profile management
- **SQLite Storage** — lightweight, portable database for papers, users, and citations

## Architecture

```
┌─────────────────────┐
│    Java Swing UI     │  (Login, Search, Results, Profile)
│    ───────────────   │
│    PythonBridge.java │──── calls ────┐
└─────────┬───────────┘               │
          │ JDBC                      ▼
          ▼                ┌─────────────────────┐
  ┌──────────────┐         │  Python Rec. Engine  │
  │  SQLite DB   │◄────────│  (main.py CLI)       │
  │  papers.db   │         │                      │
  └──────────────┘         │  ┌─ content_sim ──┐  │
                           │  ├─ citation_graph│  │
                           │  ├─ user_matching │  │
                           │  └─ ranking ──────┘  │
                           └─────────────────────┘
```

## Tech Stack

| Layer      | Technology                            |
|------------|---------------------------------------|
| Frontend   | Java Swing                            |
| Backend    | Java + Python bridge                  |
| ML/NLP     | scikit-learn (TF-IDF, cosine sim)     |
| Graphs     | NetworkX (PageRank, citation graph)   |
| Database   | SQLite                                |
| Build      | Maven (Java), pip (Python)            |

## Setup Instructions

### Prerequisites
- **Python 3.8+** with pip
- **Java 11+** (JDK)
- **Maven** (for Java build)

### 1. Install Python Dependencies

```bash
cd Smart-Research-Paper-Recommendation-System
pip install -r requirements.txt
```

### 2. Seed the Database

```bash
python data/seed_data.py
```

This creates `database/papers.db` with sample papers, citations, and users.

### 3. Build the Java UI

```bash
cd java_ui
mvn clean package
```

### 4. Run the Application

```bash
java -jar java_ui/target/smart-research-paper-recommendation-1.0-SNAPSHOT-jar-with-dependencies.jar
```

Or run directly:

```bash
cd java_ui
mvn exec:java -Dexec.mainClass="com.srps.App"
```

### Test Accounts (after seeding)

| Username | Password   | Interests                                      |
|----------|------------|-------------------------------------------------|
| alice    | alice123   | machine learning, deep learning, neural networks|
| bob      | bob123     | NLP, information retrieval, text mining          |
| charlie  | charlie123 | computer vision, image recognition, deep learning|

### 5. Run Python Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
Smart-Research-Paper-Recommendation-System/
├── README.md
├── requirements.txt
├── database/
│   └── schema.sql
├── data/
│   └── seed_data.py
├── python_engine/
│   ├── __init__.py
│   ├── main.py
│   ├── db.py
│   ├── keyword_extractor.py
│   ├── content_similarity.py
│   ├── citation_graph.py
│   ├── user_matching.py
│   └── ranking.py
├── java_ui/
│   ├── pom.xml
│   └── src/main/java/com/srps/
│       ├── App.java
│       ├── ui/        (LoginFrame, MainFrame, ResultsPanel, ProfilePanel)
│       ├── model/     (Paper, User, Recommendation)
│       ├── db/        (DatabaseManager)
│       └── engine/    (PythonBridge)
└── tests/
    ├── test_content_similarity.py
    ├── test_citation_graph.py
    ├── test_ranking.py
    └── test_user_matching.py
```

## License

This project is developed as a course (PBL) project for academic purposes.
