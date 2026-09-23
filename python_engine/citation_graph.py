import networkx as nx

def build_citation_graph(citations):
    graph = nx.DiGraph()
    graph.add_edges_from(citations)
    return graph

def compute_pagerank(graph):
    if not graph:
        return {}
    return nx.pagerank(graph)

def get_citation_neighbors(graph, paper_ids, depth=1):
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

def compute_citation_score(graph, query_relevant_ids, all_paper_ids):
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
