import pytest
from python_engine.bm25 import BM25Okapi


@pytest.fixture
def sample_papers():
    return [
        {
            "id": 1,
            "title": "Deep Residual Learning for Image Recognition",
            "keywords": "deep learning, resnet, computer vision",
            "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework.",
        },
        {
            "id": 2,
            "title": "Attention Is All You Need",
            "keywords": "transformer, attention, NLP",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        },
        {
            "id": 3,
            "title": "BERT Pre-training of Deep Bidirectional Transformers",
            "keywords": "BERT, transformer, language model, NLP",
            "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations.",
        },
    ]


def test_bm25_fit_and_score(sample_papers):
    bm25 = BM25Okapi()
    bm25.fit(sample_papers)

    assert bm25.corpus_size == 3
    assert bm25.avgdl > 0
    assert len(bm25.paper_ids) == 3

    # Query matching Paper 1
    scores = bm25.compute_query_scores("residual networks computer vision")
    assert scores[1] > scores[2]
    assert scores[1] > scores[3]
    assert 0.0 <= scores[1] <= 1.0


def test_bm25_nlp_query(sample_papers):
    bm25 = BM25Okapi()
    bm25.fit(sample_papers)

    # Query matching Transformers / BERT
    scores = bm25.compute_query_scores("transformer language model")
    assert scores[2] > scores[1]
    assert scores[3] > scores[1]


def test_bm25_empty_query(sample_papers):
    bm25 = BM25Okapi()
    bm25.fit(sample_papers)

    scores = bm25.compute_query_scores("")
    assert all(score == 0.0 for score in scores.values())
