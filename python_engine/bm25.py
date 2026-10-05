"""
bm25.py — Okapi BM25 Ranking Algorithm for Information Retrieval.

Implements the BM25 probabilistic relevance framework with document length
normalization and query term frequency weighting.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Optional


class BM25Okapi:
    """
    Okapi BM25 implementation for scoring and ranking research papers.

    Parameters:
        k1 (float): Term frequency saturation parameter. Controls how quickly
                    additional occurrences of a term saturate the score (default 1.5).
        b (float): Document length normalization parameter (0.0 to 1.0).
                   1.0 fully penalizes long documents, 0.0 ignores length (default 0.75).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_lengths: List[int] = []
        self.doc_term_freqs: List[Counter] = []
        self.paper_ids: List[int] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Convert text into lowercase word tokens."""
        if not text:
            return []
        return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())

    def fit(self, papers: List[Dict], title_weight: float = 2.0, keyword_weight: float = 1.5):
        """
        Fit the BM25 model on a corpus of papers.

        Applies field weighting by repeating tokens in title and keywords.
        """
        self.paper_ids = [p["id"] for p in papers]
        self.corpus_size = len(papers)
        self.doc_lengths = []
        self.doc_term_freqs = []
        self.doc_freqs = {}

        if self.corpus_size == 0:
            self.avgdl = 0.0
            return self

        total_length = 0

        for p in papers:
            title_tokens = self.tokenize(p.get("title", ""))
            kw_tokens = self.tokenize(p.get("keywords", ""))
            abstract_tokens = self.tokenize(p.get("abstract", ""))

            # Field-weighted token list
            doc_tokens = (
                title_tokens * int(title_weight)
                + kw_tokens * int(keyword_weight)
                + abstract_tokens
            )

            length = len(doc_tokens)
            self.doc_lengths.append(length)
            total_length += length

            tf = Counter(doc_tokens)
            self.doc_term_freqs.append(tf)

            for term in set(doc_tokens):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avgdl = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Precompute Robertson-Spärck Jones IDF
        self.idf = {}
        for term, df in self.doc_freqs.items():
            # Standard BM25 IDF formulation: ln((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

        return self

    def score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """Compute the BM25 score of a single document for the query tokens."""
        score = 0.0
        doc_len = self.doc_lengths[doc_idx]
        tf_dict = self.doc_term_freqs[doc_idx]
        denom_part = self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl if self.avgdl > 0 else 1.0))

        for q in query_tokens:
            if q not in tf_dict:
                continue
            f = tf_dict[q]
            idf = self.idf.get(q, 0.0)
            numerator = f * (self.k1 + 1.0)
            denominator = f + denom_part
            score += idf * (numerator / denominator)

        return score

    def compute_query_scores(self, query: str) -> Dict[int, float]:
        """
        Compute normalized BM25 relevance scores for all papers.

        Returns:
            dict {paper_id: score} with scores normalized to [0, 1].
        """
        if not query or self.corpus_size == 0:
            return {pid: 0.0 for pid in self.paper_ids}

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return {pid: 0.0 for pid in self.paper_ids}

        raw_scores = {}
        max_score = 0.0

        for idx, pid in enumerate(self.paper_ids):
            s = self.score_document(query_tokens, idx)
            raw_scores[pid] = s
            if s > max_score:
                max_score = s

        if max_score > 0:
            return {pid: round(raw_scores[pid] / max_score, 4) for pid in self.paper_ids}
        return {pid: 0.0 for pid in self.paper_ids}
