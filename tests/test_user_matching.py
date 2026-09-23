"""Tests for user_matching module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from python_engine.user_matching import compute_user_interest_score

SAMPLE_USER = {
    "id": 1,
    "username": "alice",
    "interests": "machine learning, deep learning, neural networks",
}

SAMPLE_PAPERS = [
    {
        "id": 1,
        "title": "Deep Learning for Image Classification",
        "keywords": "deep learning, CNN, image classification",
        "abstract": "Neural network approach",
    },
    {
        "id": 2,
        "title": "Database Query Optimization",
        "keywords": "SQL, query optimization, indexing",
        "abstract": "Optimizing database queries",
    },
    {
        "id": 3,
        "title": "Machine Learning in Healthcare",
        "keywords": "machine learning, healthcare, prediction",
        "abstract": "ML models for health",
    },
]


def test_interest_matching():
    scores = compute_user_interest_score(SAMPLE_USER, SAMPLE_PAPERS)
    # Papers 1 and 3 should score higher than paper 2 for ML-interested user
    assert scores[1] > scores[2]
    assert scores[3] > scores[2]


def test_scores_normalized():
    scores = compute_user_interest_score(SAMPLE_USER, SAMPLE_PAPERS)
    for pid, score in scores.items():
        assert 0.0 <= score <= 1.0
