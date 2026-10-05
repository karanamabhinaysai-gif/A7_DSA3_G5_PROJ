"""
bibliometrics.py — Bibliometric Network Analysis (Co-Citation & Bibliographic Coupling).

Implements fundamental scientometric graph algorithms:
- Co-Citation Analysis: measures semantic similarity by frequency of co-occurring in reference lists.
- Bibliographic Coupling: measures similarity by shared backward citations.
- In-degree citation velocity and influence scoring.
"""

from collections import defaultdict
from typing import Dict, List, Tuple
import networkx as nx


def compute_cocitation_matrix(graph: nx.DiGraph, top_n: int = 15) -> List[Dict]:
    """
    Compute co-citation pairs: papers frequently cited together by the same citing papers.
    Returns list of {paper_a, paper_b, cocitation_count}.
    """
    citing_to_cited = defaultdict(set)
    for citing, cited in graph.edges():
        citing_to_cited[citing].add(cited)

    cocitation_counts = defaultdict(int)

    for citing, cited_set in citing_to_cited.items():
        cited_list = sorted(list(cited_set))
        for i in range(len(cited_list)):
            for j in range(i + 1, len(cited_list)):
                pair = (cited_list[i], cited_list[j])
                cocitation_counts[pair] += 1

    sorted_pairs = sorted(cocitation_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [
        {"paper_a": p[0], "paper_b": p[1], "cocitation_frequency": count}
        for p, count in sorted_pairs if count > 0
    ]


def compute_bibliographic_coupling(graph: nx.DiGraph, top_n: int = 15) -> List[Dict]:
    """
    Compute bibliographic coupling: papers that cite the same common references.
    Returns list of {paper_a, paper_b, shared_references_count}.
    """
    cited_to_citing = defaultdict(set)
    for citing, cited in graph.edges():
        cited_to_citing[cited].add(citing)

    coupling_counts = defaultdict(int)

    for cited, citing_set in cited_to_citing.items():
        citing_list = sorted(list(citing_set))
        for i in range(len(citing_list)):
            for j in range(i + 1, len(citing_list)):
                pair = (citing_list[i], citing_list[j])
                coupling_counts[pair] += 1

    sorted_pairs = sorted(coupling_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [
        {"paper_a": p[0], "paper_b": p[1], "shared_references": count}
        for p, count in sorted_pairs if count > 0
    ]


def compute_paper_influence_metrics(graph: nx.DiGraph, papers: List[Dict]) -> List[Dict]:
    """
    Compute citation velocity, in-degree centrality, and influence rank for papers.
    """
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())

    results = []
    current_year = 2026

    for p in papers:
        pid = p["id"]
        in_cites = in_degrees.get(pid, 0)
        out_cites = out_degrees.get(pid, 0)
        age = max(1, current_year - (p.get("year") or 2020))
        velocity = in_cites / age  # Citations per year

        results.append({
            "paper_id": pid,
            "title": p.get("title", ""),
            "authors": p.get("authors", ""),
            "year": p.get("year", 2020),
            "citations_count": in_cites,
            "references_count": out_cites,
            "citation_velocity": round(velocity, 2),
            "url": p.get("url", ""),
        })

    results.sort(key=lambda x: (x["citations_count"], x["citation_velocity"]), reverse=True)
    return results[:20]
