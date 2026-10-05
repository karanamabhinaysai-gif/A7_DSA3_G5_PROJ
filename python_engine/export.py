"""
export.py — Export research paper citations to BibTeX, APA, MLA, and Chicago formats.
"""

import re
from typing import Dict, List


def _clean_citekey(title: str, year: int) -> str:
    """Generate a clean citation key like 'vaswani2019attention'."""
    first_word = re.sub(r"[^a-zA-Z]", "", title.split()[0] if title else "paper").lower()
    return f"{first_word}{year or 'undated'}"


def to_bibtex(paper: Dict) -> str:
    """Generate BibTeX entry for a paper."""
    title = paper.get("title", "Untitled")
    authors = paper.get("authors", "Unknown")
    year = paper.get("year", 2020)
    venue = paper.get("venue", "Conference/Journal")
    doi = paper.get("doi", "")
    key = _clean_citekey(title, year)

    bib = [
        f"@article{{{key},",
        f"  title = {{{{{title}}}}},",
        f"  author = {{{authors}}},",
        f"  year = {{{year}}},",
        f"  journal = {{{venue}}},",
    ]
    if doi:
        bib.append(f"  doi = {{{doi}}},")
    bib.append("}")
    return "\n".join(bib)


def to_apa(paper: Dict) -> str:
    """Generate APA 7th edition citation."""
    authors = paper.get("authors", "Unknown Author")
    year = paper.get("year", "n.d.")
    title = paper.get("title", "Untitled")
    venue = paper.get("venue", "")
    doi = paper.get("doi", "")

    apa = f"{authors} ({year}). {title}."
    if venue:
        apa += f" *{venue}*."
    if doi:
        apa += f" https://doi.org/{doi}"
    return apa


def to_mla(paper: Dict) -> str:
    """Generate MLA 9th edition citation."""
    authors = paper.get("authors", "Unknown Author")
    title = paper.get("title", "Untitled")
    venue = paper.get("venue", "")
    year = paper.get("year", "")

    mla = f'{authors}. "{title}."'
    if venue:
        mla += f" *{venue}*,"
    if year:
        mla += f" {year}."
    return mla


def export_papers_bibtex(papers: List[Dict]) -> str:
    """Export multiple papers to BibTeX string."""
    return "\n\n".join(to_bibtex(p) for p in papers)
