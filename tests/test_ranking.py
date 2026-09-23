"""Tests for ranking module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from python_engine.ranking import compute_final_ranking


def test_default_weights():
    content = {1: 0.9, 2: 0.3, 3: 0.5}
    citation = {1: 0.5, 2: 0.8, 3: 0.2}
    user = {1: 0.7, 2: 0.4, 3: 0.9}
    results = compute_final_ranking(content, citation, user, top_k=3)
    assert len(results) == 3
    # Results should be sorted by score descending
    scores = [r[1] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_custom_weights():
    content = {1: 1.0, 2: 0.0}
    citation = {1: 0.0, 2: 1.0}
    user = {1: 0.0, 2: 0.0}
    # With content weight = 1.0, paper 1 should win
    results = compute_final_ranking(
        content, citation, user,
        weights={"content": 1.0, "citation": 0.0, "user_interest": 0.0},
        top_k=2,
    )
    assert results[0][0] == 1


def test_top_k_limit():
    content = {i: 0.5 for i in range(20)}
    citation = {i: 0.5 for i in range(20)}
    user = {i: 0.5 for i in range(20)}
    results = compute_final_ranking(content, citation, user, top_k=5)
    assert len(results) == 5


def test_score_breakdown():
    content = {1: 0.8}
    citation = {1: 0.6}
    user = {1: 0.4}
    results = compute_final_ranking(content, citation, user, top_k=1)
    paper_id, final_score, breakdown = results[0]
    assert "content_score" in breakdown
    assert "citation_score" in breakdown
    assert "user_score" in breakdown
