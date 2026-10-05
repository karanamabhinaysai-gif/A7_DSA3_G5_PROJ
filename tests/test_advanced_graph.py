import pytest
import networkx as nx
from python_engine.citation_graph import (
    build_citation_graph,
    compute_hits,
    compute_personalized_pagerank,
    find_shortest_citation_path,
    detect_communities,
    compute_graph_analytics,
)


@pytest.fixture
def sample_graph():
    # 1 -> 2, 1 -> 3, 2 -> 4, 3 -> 4, 5 -> 6
    citations = [(1, 2), (1, 3), (2, 4), (3, 4), (5, 6)]
    return build_citation_graph(citations)


def test_compute_hits(sample_graph):
    hubs, auths = compute_hits(sample_graph)
    assert len(hubs) > 0
    assert len(auths) > 0
    # Paper 4 is cited by both 2 and 3, should have high authority
    assert auths[4] > auths[1]
    # Paper 1 cites 2 and 3, should have high hub score
    assert hubs[1] > hubs[4]


def test_personalized_pagerank(sample_graph):
    # Personalize for seed node 4
    ppr = compute_personalized_pagerank(sample_graph, seed_nodes=[4])
    assert len(ppr) == 6
    # Seed 4 should have significant score
    assert ppr[4] > 0


def test_find_shortest_citation_path(sample_graph):
    path = find_shortest_citation_path(sample_graph, 1, 4)
    assert path is not None
    assert path[0] == 1
    assert path[-1] == 4
    assert len(path) == 3  # 1 -> 2 -> 4 or 1 -> 3 -> 4


def test_detect_communities(sample_graph):
    communities = detect_communities(sample_graph)
    assert isinstance(communities, dict)
    assert len(communities) == 6
    # 5 and 6 should share community, distinct from 1,2,3,4
    assert communities[5] == communities[6]


def test_compute_graph_analytics(sample_graph):
    analytics = compute_graph_analytics(sample_graph)
    assert analytics["total_nodes"] == 6
    assert analytics["total_edges"] == 5
    assert "top_authorities" in analytics
    assert "top_pagerank" in analytics
    assert "communities_count" in analytics
