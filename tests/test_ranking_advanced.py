import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from python_engine.ranking import (
    compute_reciprocal_rank_fusion,
    compute_mmr_ranking,
    compute_recency_scores,
)


def test_reciprocal_rank_fusion():
    list1 = [1, 2, 3, 4]
    list2 = [2, 1, 4, 3]
    list3 = [2, 3, 1, 4]

    results = compute_reciprocal_rank_fusion([list1, list2, list3], k=60, top_k=4)
    assert len(results) == 4
    # Paper 2 is ranked #1 in two lists, should come out top
    top_paper, top_score = results[0]
    assert top_paper == 2


def test_compute_mmr_ranking():
    docs = [
        "deep neural networks deep learning image classification",
        "deep learning convolutional neural networks image recognition",
        "quantum computing qubit quantum entanglement algorithm",
        "natural language processing bert transformers language model",
    ]
    paper_ids = [1, 2, 3, 4]
    vec = TfidfVectorizer()
    matrix = vec.fit_transform(docs)

    # Candidate relevance scores: Paper 1 & 2 have high score, 3 & 4 have moderate
    candidate_scores = {1: 0.95, 2: 0.94, 3: 0.70, 4: 0.65}

    # Under pure relevance, 1 and 2 would be first 2.
    # Under MMR with lambda=0.5, diversity will penalize paper 2 because it is almost identical to paper 1!
    mmr_res = compute_mmr_ranking(
        candidate_scores, matrix, paper_ids, lambda_param=0.3, top_k=3
    )

    assert len(mmr_res) == 3
    selected_pids = [pid for pid, _ in mmr_res]
    assert selected_pids[0] == 1
    # Check that diverse paper (e.g. 3) was selected
    assert 3 in selected_pids


def test_compute_recency_scores():
    papers = [
        {"id": 1, "year": 2026},
        {"id": 2, "year": 2021},
        {"id": 3, "year": 2016},
    ]
    scores = compute_recency_scores(papers, current_year=2026, half_life_years=5.0)
    assert scores[1] > scores[2]
    assert scores[2] > scores[3]
    assert pytest.approx(scores[1], 0.01) == 1.0
