from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def build_tfidf_matrix(papers):
    paper_ids = [p['id'] for p in papers]
    corpus = [f"{p.get('title', '')} {p.get('abstract', '')}" for p in papers]
    
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    return tfidf_matrix, vectorizer, paper_ids

def compute_query_similarity(query, tfidf_matrix, vectorizer, paper_ids):
    if not query:
        return {pid: 0.0 for pid in paper_ids}
    
    query_vec = vectorizer.transform([query])
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    
    return {pid: float(score) for pid, score in zip(paper_ids, sim_scores)}

def compute_paper_similarity(paper_id, tfidf_matrix, paper_ids):
    try:
        idx = paper_ids.index(paper_id)
    except ValueError:
        return {pid: 0.0 for pid in paper_ids}
    
    paper_vec = tfidf_matrix[idx]
    sim_scores = cosine_similarity(paper_vec, tfidf_matrix).flatten()
    
    return {pid: float(score) for pid, score in zip(paper_ids, sim_scores)}
