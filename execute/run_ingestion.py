import json
import os
import logging
from dotenv import load_dotenv
from src.ingestion.openalex import OpenAlexIngestor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Read configuration from environment or fallback to defaults
    user_email = os.getenv("USER_EMAIL", "default@example.com")
    raw_data_path = os.getenv("RAW_DATA_PATH", "data/raw/openalex_corpus_raw.json")

    # Target corpus settings for snowball sampling
    seed_target = int(os.getenv("SEED_TARGET", 2000))
    max_total_works = int(os.getenv("MAX_TOTAL_WORKS", 20000))

    os.makedirs(os.path.dirname(raw_data_path), exist_ok=True)

    logger.info(f"Starting OpenAlex ingestion pipeline using identity: {user_email}")
    ingestor = OpenAlexIngestor(email=user_email)
    
    # Execute snowball sampling (seeds -> 1-hop reference expansion)
    raw_corpus = ingestor.run_snowball_ingestion(
        seed_target=seed_target, 
        max_total_works=max_total_works
    )

    # Persist raw payload locally
    with open(raw_data_path, "w", encoding="utf-8") as f:
        json.dump(raw_corpus, f, ensure_ascii=False, indent=2)

    logger.info(f"Raw dataset successfully stored at: {raw_data_path}")