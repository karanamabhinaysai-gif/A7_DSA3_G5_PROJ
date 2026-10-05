"""
arxiv_service.py — Live arXiv Search and Paper Ingestion.

Queries the arXiv API (Atom feed) to search real research papers,
parses metadata, and prepares them for database insertion and citation linking.
"""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def search_arxiv(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search arXiv for research papers matching query.

    Returns list of dicts with:
        title, abstract, authors, year, keywords, venue, doi, arxiv_id, pdf_url
    """
    if not query:
        return []

    encoded_query = urllib.parse.quote(query)
    url = f"https://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SmartResearchPaperRecommender/2.0 (Academic/PBL Project)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        papers = []

        for entry in root.findall("atom:entry", ATOM_NS):
            title_elem = entry.find("atom:title", ATOM_NS)
            title = " ".join(title_elem.text.split()) if title_elem is not None and title_elem.text else "Untitled"

            summary_elem = entry.find("atom:summary", ATOM_NS)
            abstract = " ".join(summary_elem.text.split()) if summary_elem is not None and summary_elem.text else ""

            # Authors
            authors_list = []
            for author_elem in entry.findall("atom:author", ATOM_NS):
                name = author_elem.find("atom:name", ATOM_NS)
                if name is not None and name.text:
                    authors_list.append(name.text.strip())
            authors = ", ".join(authors_list) if authors_list else "Unknown"

            # Published year
            published_elem = entry.find("atom:published", ATOM_NS)
            year = 2024
            if published_elem is not None and published_elem.text:
                try:
                    year = int(published_elem.text[:4])
                except Exception:
                    year = 2024

            # Arxiv ID
            id_elem = entry.find("atom:id", ATOM_NS)
            arxiv_id = ""
            if id_elem is not None and id_elem.text:
                arxiv_id = id_elem.text.split("/abs/")[-1]

            # Primary Category / Keywords
            categories = []
            for cat in entry.findall("atom:category", ATOM_NS):
                term = cat.get("term")
                if term:
                    categories.append(term)
            keywords = ", ".join(categories) if categories else "computer science"

            # PDF link
            pdf_url = ""
            for link in entry.findall("atom:link", ATOM_NS):
                if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                    break
            if not pdf_url and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            doi = f"10.48550/arXiv.{arxiv_id}" if arxiv_id else ""

            papers.append({
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": year,
                "keywords": keywords,
                "venue": f"arXiv:{categories[0] if categories else 'cs'}",
                "doi": doi,
                "arxiv_id": arxiv_id,
                "pdf_url": pdf_url,
            })

        return papers

    except Exception as e:
        return [{"error": f"arXiv query failed: {str(e)}"}]
