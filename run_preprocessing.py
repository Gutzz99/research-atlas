import json
import os
import logging
from dotenv import load_dotenv

from src.preprocessing.normalize import DataNormalizer
from src.preprocessing.validation import GraphDataValidator

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def process_pipeline(raw_path: str, processed_path: str):
    """Executes normalization and closed-graph pruning validation tasks."""
    if not os.path.exists(raw_path):
        raise FileNotFoundError(
            f"Raw dataset not found at {raw_path}. Run ingestion pipeline first."
        )

    logger.info(f"Loading raw dataset from {raw_path}...")
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 1. Normalize entities & relationships
    normalizer = DataNormalizer()
    papers, authors, topics, citations, authored, has_topic = normalizer.normalize_corpus(raw_data)

    # 2. Validate & enforce closed-graph constraints
    validator = GraphDataValidator()
    papers, authors, topics, citations, authored, has_topic = validator.validate_and_prune(
        papers, authors, topics, citations, authored, has_topic
    )

    # 3. Construct clean graph payload
    processed_payload = {
        "nodes": {
            "papers": papers,
            "authors": authors,
            "topics": topics
        },
        "edges": {
            "citations": citations,
            "authored": authored,
            "has_topic": has_topic
        }
    }

    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(processed_payload, f, ensure_ascii=False, indent=2)

    logger.info(f"Preprocessing complete. Clean graph data persisted at: {processed_path}")


if __name__ == "__main__":
    load_dotenv()
    
    raw_file = os.getenv("RAW_DATA_PATH", "data/raw/openalex_corpus_raw.json")
    processed_file = os.getenv("PROCESSED_DATA_PATH", "data/processed/graph_data_clean.json")

    process_pipeline(raw_file, processed_file)