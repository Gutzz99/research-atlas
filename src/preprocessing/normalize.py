import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class DataNormalizer:
    """
    Transforms raw OpenAlex JSON responses into clean, normalized dictionary 
    records ready for Graph Ingestion (Neo4j).
    """

    @staticmethod
    def _clean_openalex_id(full_id: str) -> str:
        """Extracts short ID from OpenAlex URI (e.g., 'https://openalex.org/W123' -> 'W123')."""
        if not full_id:
            return ""
        return full_id.split("/")[-1]

    def normalize_corpus(self, raw_works: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
        """
        Normalizes raw work JSONs into entities and relationships.
        Returns:
            papers, authors, topics, citations_rel, authored_rel, topic_rel
        """
        papers_dict = {}
        authors_dict = {}
        topics_dict = {}

        citation_edges = set()
        authored_edges = set()
        topic_edges = set()

        for work in raw_works:
            paper_id = self._clean_openalex_id(work.get("id"))
            if not paper_id or not work.get("title"):
                continue

            # 1. Paper Entity
            papers_dict[paper_id] = {
                "id": paper_id,
                "title": work.get("title", "").strip(),
                "year": work.get("publication_year"),
                "publication_date": work.get("publication_date"),
                "doi": work.get("doi"),
                "cited_by_count": work.get("cited_by_count", 0),
                "url": work.get("doi") or work.get("id")
            }

            # 2. Citation Relationships (:Paper)-[:CITES]->(:Paper)
            for ref in work.get("referenced_works", []):
                ref_id = self._clean_openalex_id(ref)
                if ref_id:
                    citation_edges.add((paper_id, ref_id))

            # 3. Authors & (:Author)-[:AUTHORED]->(:Paper)
            for authorship in work.get("authorships", []):
                author_raw = authorship.get("author", {})
                author_id = self._clean_openalex_id(author_raw.get("id"))
                author_name = author_raw.get("display_name")

                if author_id and author_name:
                    authors_dict[author_id] = {
                        "id": author_id,
                        "name": author_name.strip()
                    }
                    authored_edges.add((author_id, paper_id))

            # 4. Topics & (:Paper)-[:HAS_TOPIC]->(:Topic)
            primary_topic = work.get("primary_topic")
            if primary_topic:
                topic_id = self._clean_openalex_id(primary_topic.get("id"))
                topic_name = primary_topic.get("display_name")

                if topic_id and topic_name:
                    topics_dict[topic_id] = {
                        "id": topic_id,
                        "name": topic_name.strip()
                    }
                    topic_edges.add((paper_id, topic_id))

        # Format relasi ke bentuk dictionary
        citations = [{"source_id": src, "target_id": tgt} for src, tgt in citation_edges]
        authored = [{"author_id": src, "paper_id": tgt} for src, tgt in authored_edges]
        has_topic = [{"paper_id": src, "topic_id": tgt} for src, tgt in topic_edges]

        logger.info(
            f"Normalization complete: {len(papers_dict)} Papers, "
            f"{len(authors_dict)} Authors, {len(topics_dict)} Topics."
        )

        return (
            list(papers_dict.values()),
            list(authors_dict.values()),
            list(topics_dict.values()),
            citations,
            authored,
            has_topic
        )