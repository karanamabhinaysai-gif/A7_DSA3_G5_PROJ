"""Tests for citation_graph module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from python_engine.citation_graph import (
    build_citation_graph,
    compute_pagerank,
    get_citation_neighbors,
    compute_citation_score,
)

SAMPLE_CITATIONS = [
    (2, 1),  # paper 2 cites paper 1
    (3, 1),  # paper 3 cites paper 1
    (4, 2),  # paper 4 cites paper 2
    (5, 1),  # paper 5 cites paper 1
    (5, 3),  # paper 5 cites paper 3
]


def test_build_graph():
    graph = build_citation_graph(SAMPLE_CITATIONS)
    assert graph.number_of_nodes() == 5
    assert graph.number_of_edges() == 5


def test_pagerank():
    graph = build_citation_graph(SAMPLE_CITATIONS)
    pr = compute_pagerank(graph)
    # Paper 1 is most cited, should have highest pagerank
    assert pr[1] > pr[4]
    assert pr[1] > pr[5]


def test_citation_neighbors():
    graph = build_citation_graph(SAMPLE_CITATIONS)
    neighbors = get_citation_neighbors(graph, [1], depth=1)
    # Papers 2, 3, 5 cite paper 1
    assert 2 in neighbors
    assert 3 in neighbors
    assert 5 in neighbors


def test_citation_score():
    graph = build_citation_graph(SAMPLE_CITATIONS)
    scores = compute_citation_score(graph, [1], [1, 2, 3, 4, 5])
    for pid, score in scores.items():
        assert 0.0 <= score <= 1.0
