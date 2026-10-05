import pytest
from python_engine.paper_analyzer import analyze_paper_text


def test_analyze_paper_text():
    sample_papers = [
        {
            "id": 1,
            "title": "Deep Residual Learning for Image Recognition",
            "abstract": "We introduce residual connections to train deeper convolutional neural networks for vision.",
            "year": 2016,
            "authors": "He et al.",
            "venue": "CVPR",
        },
        {
            "id": 2,
            "title": "Vision Transformers for Image Classification",
            "abstract": "Applying transformers directly to image patches for visual recognition.",
            "year": 2021,
            "authors": "Dosovitskiy et al.",
            "venue": "ICLR",
        },
    ]

    text = "We propose an improved convolutional residual architecture for image classification and object detection."
    res = analyze_paper_text(text, sample_papers, top_citations=2)

    assert "primary_domain" in res
    assert res["primary_domain"] == "Computer Vision"
    assert len(res["extracted_keywords"]) > 0
    assert len(res["recommended_foundational_citations"]) > 0
    assert res["recommended_foundational_citations"][0]["id"] == 1
