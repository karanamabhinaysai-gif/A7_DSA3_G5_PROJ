def compute_final_ranking(content_scores, citation_scores, user_scores, weights=None, top_k=10):
    if weights is None:
        weights = {'content': 0.5, 'citation': 0.3, 'user_interest': 0.2}
        
    all_paper_ids = set(content_scores.keys()) | set(citation_scores.keys()) | set(user_scores.keys())
    
    results = []
    for pid in all_paper_ids:
        c_score = content_scores.get(pid, 0.0)
        cit_score = citation_scores.get(pid, 0.0)
        u_score = user_scores.get(pid, 0.0)
        
        final_score = (weights['content'] * c_score + 
                       weights['citation'] * cit_score + 
                       weights['user_interest'] * u_score)
                       
        breakdown = {
            'content_score': c_score,
            'citation_score': cit_score,
            'user_score': u_score
        }
        
        results.append((pid, final_score, breakdown))
        
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
