import json
import os
from src.ingestion.openalex import OpenAlexIngestor

if __name__ == "__main__":
    # Settings
    USER_EMAIL = "uzumakinagato90l@gmail.com"  # Ganti dengan email Anda untuk Polite Pool
    RAW_DATA_PATH = "data/raw/openalex_corpus_raw.json"

    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)

    ingestor = OpenAlexIngestor(email=USER_EMAIL)
    
    # Jalankan Snowball Sampling: 2.000 seed -> ekspansi hingga ±20.000 total works
    raw_corpus = ingestor.run_snowball_ingestion(seed_target=2000, max_total_works=20000)

    # Save to disk
    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_corpus, f, ensure_ascii=False, indent=2)

    print(f"Raw data successfully saved to {RAW_DATA_PATH}")