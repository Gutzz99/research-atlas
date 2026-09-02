import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class GraphDataValidator:
    """
    Validates structural integrity of normalized graph data before database ingestion.
    """

    @staticmethod
    def validate_and_prune(
        papers: List[Dict],
        authors: List[Dict],
        topics: List[Dict],
        citations: List[Dict],
        authored: List[Dict],
        has_topic: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
        """
        Prunes references pointing to non-existent nodes in the corpus (Closed Graph Constraint).
        """
        valid_paper_ids = {p["id"] for p in papers}
        valid_author_ids = {a["id"] for a in authors}
        valid_topic_ids = {t["id"] for t in topics}

        # Prune Citation Edges (Hanya pertahankan jika kedua paper berada dalam corpus)
        valid_citations = [
            c for c in citations 
            if c["source_id"] in valid_paper_ids and c["target_id"] in valid_paper_ids
        ]

        # Prune Authored Edges
        valid_authored = [
            a for a in authored 
            if a["author_id"] in valid_author_ids and a["paper_id"] in valid_paper_ids
        ]

        # Prune Topic Edges
        valid_has_topic = [
            t for t in has_topic 
            if t["paper_id"] in valid_paper_ids and t["topic_id"] in valid_topic_ids
        ]

        # Hitung rasio ketersambungan (Connectedness)
        citation_density = len(valid_citations) / max(len(papers), 1)
        logger.info(f"Validation metrics:")
        logger.info(f" - Citation Edges: {len(citations)} raw -> {len(valid_citations)} valid closed-graph edges.")
        logger.info(f" - Graph Citation Ratio: {citation_density:.2f} edges/paper.")

        return papers, authors, topics, valid_citations, valid_authored, valid_has_topic