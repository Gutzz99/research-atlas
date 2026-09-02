import os
import time
import logging
from typing import List, Dict, Any, Optional
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class OpenAlexIngestor:
    """
    Ingestor client for OpenAlex API using Snowball Sampling methodology.
    Extracts structured bibliographic data optimized for Neo4j Graph Construction.
    """
    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, email: str, max_retries: int = 3, backoff_factor: float = 1.5):
        self.email = email
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.headers = {"User-Agent": f"ResearchAtlas/0.1 (mailto:{self.email})"}
        
        # Fields optimization to reduce JSON payload size
        self.select_fields = [
            "id", "title", "publication_year", "publication_date", 
            "doi", "cited_by_count", "referenced_works", 
            "authorships", "concepts", "primary_topic"
        ]

    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Executes HTTP GET with exponential backoff retry logic."""
        params["mailto"] = self.email
        if "select" not in params:
            params["select"] = ",".join(self.select_fields)

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(self.BASE_URL, params=params, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    sleep_time = self.backoff_factor ** attempt
                    logger.warning(f"Rate limited (429). Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"API Error {response.status_code}: {response.text}")
                    break
            except requests.RequestException as e:
                logger.warning(f"Request failed (Attempt {attempt}/{self.max_retries}): {e}")
                time.sleep(self.backoff_factor ** attempt)
        
        return None

    def fetch_seed_works(self, start_year: int = 2015, end_year: int = 2026, target_count: int = 2000) -> List[Dict[str, Any]]:
        """
        Fetch top cited seed papers within specified publication years using Cursor Pagination.
        """
        logger.info(f"Fetching top {target_count} seed works ({start_year}-{end_year})...")
        results = []
        cursor = "*"
        per_page = 200

        filter_param = f"from_publication_date:{start_year}-01-01,to_publication_date:{end_year}-12-31,has_doi:true"
        
        while len(results) < target_count and cursor:
            params = {
                "filter": filter_param,
                "sort": "cited_by_count:desc",
                "per-page": per_page,
                "cursor": cursor
            }
            
            data = self._make_request(params)
            if not data or "results" not in data:
                break

            fetched = data.get("results", [])
            results.extend(fetched)
            logger.info(f"Fetched {len(results)} / {target_count} seed works...")

            cursor = data.get("meta", {}).get("next_cursor", None)
            time.sleep(0.1)  # Respectful delay

        return results[:target_count]

    def fetch_works_by_ids(self, openalex_ids: List[str], chunk_size: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch specific works by OpenAlex IDs in batched filter requests (1-hop expansion).
        """
        logger.info(f"Fetching {len(openalex_ids)} referenced works in chunks...")
        all_works = []
        
        # Clean IDs (ensure full URI format if needed)
        clean_ids = [id_str if id_str.startswith("https://openalex.org/") else f"https://openalex.org/{id_str}" for id_str in openalex_ids]

        for i in range(0, len(clean_ids), chunk_size):
            chunk = clean_ids[i:i + chunk_size]
            pipe_separated_ids = "|".join(chunk)
            
            params = {
                "filter": f"openalex:{pipe_separated_ids}",
                "per-page": chunk_size
            }
            
            data = self._make_request(params)
            if data and "results" in data:
                all_works.extend(data["results"])

            logger.info(f"Processed referenced works: {len(all_works)} / {len(clean_ids)}")
            time.sleep(0.1)

        return all_works

    def run_snowball_ingestion(self, seed_target: int = 2000, max_total_works: int = 20000) -> List[Dict[str, Any]]:
        """
        Executes complete Snowball Sampling Ingestion pipeline.
        Step 1: Fetch top seed works.
        Step 2: Collect referenced works IDs.
        Step 3: Fetch referenced works to form dense subgraph.
        """
        corpus_dict: Dict[str, Dict[str, Any]] = {}

        # 1. Fetch Seeds
        seeds = self.fetch_seed_works(target_count=seed_target)
        for work in seeds:
            corpus_dict[work["id"]] = work

        # 2. Extract referenced work IDs from seeds
        referenced_ids = set()
        for work in seeds:
            for ref in work.get("referenced_works", []):
                if ref not in corpus_dict:
                    referenced_ids.add(ref)

        logger.info(f"Discovered {len(referenced_ids)} unique reference candidates.")

        # 3. Limit references to fit target corpus size
        remaining_slots = max_total_works - len(corpus_dict)
        ref_ids_to_fetch = list(referenced_ids)[:remaining_slots]

        # 4. Fetch Referenced Works
        referenced_works = self.fetch_works_by_ids(ref_ids_to_fetch)
        for work in referenced_works:
            corpus_dict[work["id"]] = work

        logger.info(f"Ingestion complete. Total unique works collected: {len(corpus_dict)}")
        return list(corpus_dict.values())