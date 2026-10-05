"""
citation_graph.py — Advanced Citation Graph Analysis and Network Science Algorithms.

Implements PageRank, Personalized PageRank (RWR), Kleinberg's HITS (Hubs & Authorities),
Community Detection, Shortest Citation Lineage, Co-Citation, and Network Metrics.
"""

import networkx as nx
from typing import Dict, List, Optional, Set, Tuple


def build_citation_graph(citations: List[Tuple[int, int]]) -> nx.DiGraph:
    """Build a directed citation graph where edge is (citing_paper -> cited_paper)."""
    graph = nx.DiGraph()
    graph.add_edges_from(citations)
    return graph


def compute_pagerank(graph: nx.DiGraph, alpha: float = 0.85) -> Dict[int, float]:
    """Compute standard PageRank on the citation graph."""
    if not graph or graph.number_of_nodes() == 0:
        return {}
    try:
        return nx.pagerank(graph, alpha=alpha)
    except Exception:
        # Fallback uniform
        nodes = list(graph.nodes())
        return {n: 1.0 / len(nodes) for n in nodes}


def compute_personalized_pagerank(
    graph: nx.DiGraph, seed_nodes: List[int], alpha: float = 0.85
) -> Dict[int, float]:
    """
    Random Walk with Restart (Personalized PageRank).

    Biases the random surfer to restart at seed nodes (e.g., query matches or user history).
    """
    if not graph or graph.number_of_nodes() == 0:
        return {}

    valid_seeds = [s for s in seed_nodes if s in graph]
    if not valid_seeds:
        return compute_pagerank(graph, alpha=alpha)

    # Teleportation distribution vector
    personalization = {n: 0.0 for n in graph.nodes()}
    weight = 1.0 / len(valid_seeds)
    for s in valid_seeds:
        personalization[s] = weight

    try:
        return nx.pagerank(graph, alpha=alpha, personalization=personalization)
    except Exception:
        return compute_pagerank(graph, alpha=alpha)


def compute_hits(graph: nx.DiGraph, max_iter: int = 100) -> Tuple[Dict[int, float], Dict[int, float]]:
    """
    Compute Kleinberg's HITS algorithm: Hubs and Authorities.

    - Authorities: Highly cited, authoritative landmark papers.
    - Hubs: Comprehensive review or survey papers citing many authorities.
    """
    if not graph or graph.number_of_nodes() == 0:
        return {}, {}
    try:
        hubs, authorities = nx.hits(graph, max_iter=max_iter, normalized=True)
        # Eigenvector solvers can have sign ambiguity, ensure positive normalized scores
        h_norm = {k: abs(float(v)) for k, v in hubs.items()}
        a_norm = {k: abs(float(v)) for k, v in authorities.items()}
        h_sum = sum(h_norm.values()) or 1.0
        a_sum = sum(a_norm.values()) or 1.0
        return {k: v / h_sum for k, v in h_norm.items()}, {k: v / a_sum for k, v in a_norm.items()}
    except Exception:
        # Fallback to degree centrality
        in_deg = nx.in_degree_centrality(graph)
        out_deg = nx.out_degree_centrality(graph)
        return out_deg, in_deg


def get_citation_neighbors(graph: nx.DiGraph, paper_ids: List[int], depth: int = 1) -> Set[int]:
    """Retrieve n-hop citation neighborhood (both citing and cited papers)."""
    neighbors = set()
    for pid in paper_ids:
        if pid not in graph:
            continue

        current_layer = {pid}
        for _ in range(depth):
            next_layer = set()
            for node in current_layer:
                next_layer.update(graph.predecessors(node))
                next_layer.update(graph.successors(node))
            neighbors.update(next_layer)
            current_layer = next_layer

    return neighbors


def find_shortest_citation_path(
    graph: nx.DiGraph, source_id: int, target_id: int
) -> Optional[List[int]]:
    """
    Find shortest directed citation path from source to target paper.
    If no directed path exists, searches in the undirected projection.
    """
    if source_id not in graph or target_id not in graph:
        return None
    try:
        if nx.has_path(graph, source_id, target_id):
            return nx.shortest_path(graph, source=source_id, target=target_id)
        undirected = graph.to_undirected()
        if nx.has_path(undirected, source_id, target_id):
            return nx.shortest_path(undirected, source=source_id, target=target_id)
    except Exception:
        pass
    return None


def detect_communities(graph: nx.DiGraph) -> Dict[int, int]:
    """
    Detect thematic paper clusters/communities using modularity maximization.

    Returns:
        dict {paper_id: community_id (0-indexed)}
    """
    if not graph or graph.number_of_nodes() == 0:
        return {}

    undirected = graph.to_undirected()
    try:
        import networkx.algorithms.community as nx_comm
        communities = nx_comm.greedy_modularity_communities(undirected)
        node_to_comm = {}
        for comm_id, comm_set in enumerate(communities):
            for node in comm_set:
                node_to_comm[node] = comm_id
        return node_to_comm
    except Exception:
        # Fallback to connected components
        components = list(nx.connected_components(undirected))
        node_to_comm = {}
        for comm_id, comp in enumerate(components):
            for node in comp:
                node_to_comm[node] = comm_id
        return node_to_comm


def compute_citation_score(
    graph: nx.DiGraph, query_relevant_ids: List[int], all_paper_ids: List[int], use_personalized: bool = True
) -> Dict[int, float]:
    """
    Compute citation relevance score combining PageRank / Personalized PageRank
    and direct citation proximity to seed query papers.
    """
    if use_personalized and query_relevant_ids:
        pr_scores = compute_personalized_pagerank(graph, query_relevant_ids)
    else:
        pr_scores = compute_pagerank(graph)

    if not pr_scores:
        return {pid: 0.0 for pid in all_paper_ids}

    max_pr = max(pr_scores.values()) if pr_scores else 1.0
    if max_pr == 0:
        max_pr = 1.0

    scores = {}
    for pid in all_paper_ids:
        score = pr_scores.get(pid, 0.0) / max_pr

        if query_relevant_ids and pid in graph:
            if pid in query_relevant_ids:
                score += 0.5
            else:
                for qid in query_relevant_ids:
                    if qid in graph:
                        if graph.has_edge(pid, qid) or graph.has_edge(qid, pid):
                            score += 0.2
                            break
        scores[pid] = min(1.0, score)

    return scores


def compute_graph_analytics(graph: nx.DiGraph, all_paper_ids: Optional[List[int]] = None) -> Dict:
    """
    Calculate comprehensive Network Science and DSA graph metrics.
    """
    if not graph or graph.number_of_nodes() == 0:
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "density": 0.0,
            "avg_degree": 0.0,
            "top_pagerank": [],
            "top_authorities": [],
            "top_hubs": [],
            "communities_count": 0,
        }

    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    density = nx.density(graph)

    # PageRank
    pr = compute_pagerank(graph)
    sorted_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:10]

    # HITS
    hubs, auths = compute_hits(graph)
    sorted_auths = sorted(auths.items(), key=lambda x: x[1], reverse=True)[:10]
    sorted_hubs = sorted(hubs.items(), key=lambda x: x[1], reverse=True)[:10]

    # Communities
    communities = detect_communities(graph)
    comm_count = len(set(communities.values())) if communities else 0

    # In/Out degrees
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())
    avg_degree = sum(dict(graph.degree()).values()) / num_nodes if num_nodes > 0 else 0

    return {
        "total_nodes": num_nodes,
        "total_edges": num_edges,
        "density": round(density, 5),
        "avg_degree": round(avg_degree, 2),
        "communities_count": comm_count,
        "top_pagerank": [{"paper_id": k, "score": round(v, 4)} for k, v in sorted_pr],
        "top_authorities": [{"paper_id": k, "score": round(v, 4)} for k, v in sorted_auths],
        "top_hubs": [{"paper_id": k, "score": round(v, 4)} for k, v in sorted_hubs],
        "top_cited": [
            {"paper_id": k, "in_citations": v}
            for k, v in sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
    }
