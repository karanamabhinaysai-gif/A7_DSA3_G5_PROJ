from python_engine.export import to_bibtex, to_apa, to_mla, export_papers_bibtex


def test_to_bibtex():
    paper = {
        "title": "Attention Is All You Need",
        "authors": "A. Vaswani, N. Shazeer",
        "year": 2017,
        "venue": "NeurIPS",
        "doi": "10.1000/dl002",
    }
    bib = to_bibtex(paper)
    assert "@article" in bib
    assert "Attention Is All You Need" in bib
    assert "A. Vaswani" in bib
    assert "2017" in bib


def test_to_apa():
    paper = {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": "K. He, X. Zhang, S. Ren",
        "year": 2016,
        "venue": "CVPR",
        "doi": "10.1000/dl001",
    }
    apa = to_apa(paper)
    assert "K. He" in apa
    assert "(2016)" in apa
    assert "CVPR" in apa
    assert "https://doi.org/10.1000/dl001" in apa


def test_to_mla():
    paper = {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": "J. Devlin, M. Chang",
        "year": 2019,
        "venue": "NAACL",
    }
    mla = to_mla(paper)
    assert "J. Devlin" in mla
    assert '"BERT: Pre-training of Deep Bidirectional Transformers."' in mla
    assert "2019" in mla


def test_export_papers_bibtex():
    papers = [
        {"title": "Paper One", "authors": "Author A", "year": 2021, "venue": "ICML"},
        {"title": "Paper Two", "authors": "Author B", "year": 2022, "venue": "NeurIPS"},
    ]
    bib_text = export_papers_bibtex(papers)
    assert bib_text.count("@article") == 2
