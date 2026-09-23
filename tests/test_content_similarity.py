import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from python_engine.content_similarity import build_tfidf_matrix, compute_query_similarity

# Create sample papers
SAMPLE_PAPERS = [
    {'id': 1, 'title': 'Deep Learning for Image Classification', 'abstract': 'This paper presents a deep neural network approach for image classification using convolutional layers.'},
    {'id': 2, 'title': 'Natural Language Processing with Transformers', 'abstract': 'We propose a transformer-based model for natural language understanding and text generation tasks.'},
    {'id': 3, 'title': 'Reinforcement Learning in Robotics', 'abstract': 'This work applies reinforcement learning algorithms to robotic control and navigation problems.'},
    {'id': 4, 'title': 'Graph Neural Networks for Social Networks', 'abstract': 'We study graph neural network architectures for analyzing social network structures and community detection.'},
    {'id': 5, 'title': 'Convolutional Neural Networks for Object Detection', 'abstract': 'A novel CNN architecture for real-time object detection in images and video streams.'},
]

def test_build_tfidf_matrix():
    matrix, vectorizer, paper_ids = build_tfidf_matrix(SAMPLE_PAPERS)
    assert matrix.shape[0] == 5  # 5 papers
    assert len(paper_ids) == 5
    assert matrix.shape[1] > 0  # some features

def test_query_similarity_relevant():
    matrix, vectorizer, paper_ids = build_tfidf_matrix(SAMPLE_PAPERS)
    scores = compute_query_similarity('deep learning image classification', matrix, vectorizer, paper_ids)
    # Paper 1 and 5 should score highest (image/CNN related)
    assert scores[1] > scores[2]  # image paper > robotics
    assert scores[1] > scores[4]  # image paper > graph networks

def test_query_similarity_nlp():
    matrix, vectorizer, paper_ids = build_tfidf_matrix(SAMPLE_PAPERS)
    scores = compute_query_similarity('natural language processing text', matrix, vectorizer, paper_ids)
    # Paper 2 should score highest
    assert scores[2] > scores[1]
    assert scores[2] > scores[3]

def test_all_scores_non_negative():
    matrix, vectorizer, paper_ids = build_tfidf_matrix(SAMPLE_PAPERS)
    scores = compute_query_similarity('machine learning', matrix, vectorizer, paper_ids)
    for pid, score in scores.items():
        assert score >= 0.0
