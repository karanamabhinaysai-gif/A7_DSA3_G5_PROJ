import pytest
import networkx as nx
from python_engine.bibliometrics import (
    compute_cocitation_matrix,
    compute_bibliographic_coupling,
    compute_paper_influence_metrics,
)


def test_bibliometrics():
    # 1 cites 2 and 3; 4 cites 2 and 3; 2 cites 5; 3 cites 5
    graph = nx.DiGraph()
    graph.add_edges_from([(1, 2), (1, 3), (4, 2), (4, 3), (2, 5), (3, 5)])

    # Co-citation: 2 and 3 are co-cited by both 1 and 4 -> frequency should be 2
    cocit = compute_cocitation_matrix(graph, top_n=5)
    assert len(cocit) > 0
    top_pair = cocit[0]
    assert (top_pair["paper_a"], top_pair["paper_b"]) == (2, 3)
    assert top_pair["cocitation_frequency"] == 2

    # Bibliographic coupling: 1 and 4 both cite 2 and 3 -> shared_references = 2
    coupling = compute_bibliographic_coupling(graph, top_n=5)
    assert len(coupling) > 0
    top_coupling = coupling[0]
    assert (top_coupling["paper_a"], top_coupling["paper_b"]) == (1, 4)
    assert top_coupling["shared_references"] == 2

    # Influence metrics
    papers = [
        {"id": 2, "title": "Paper 2", "year": 2020},
        {"id": 3, "title": "Paper 3", "year": 2020},
    ]
    influence = compute_paper_influence_metrics(graph, papers)
    assert len(influence) == 2
    assert influence[0]["citations_count"] == 2
