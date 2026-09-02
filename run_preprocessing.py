import json
import os
from src.preprocessing.normalize import DataNormalizer
from src.preprocessing.validation import GraphDataValidator

if __name__ == "__main__":
    RAW_PATH = "data/raw/openalex_corpus_raw.json"
    PROCESSED_PATH = "data/processed/graph_data_clean.json"

    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"File {RAW_PATH} belum ada. Jalankan data ingestion terlebih dahulu.")

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 1. Normalize
    normalizer = DataNormalizer()
    papers, authors, topics, citations, authored, has_topic = normalizer.normalize_corpus(raw_data)

    # 2. Validate & Prune
    validator = GraphDataValidator()
    papers, authors, topics, citations, authored, has_topic = validator.validate_and_prune(
        papers, authors, topics, citations, authored, has_topic
    )

    # 3. Save Processed Output
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

    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    with open(PROCESSED_PATH, "w", encoding="utf-8") as f:
        json.dump(processed_payload, f, ensure_ascii=False, indent=2)

    print(f"Data preprocessing selesai. Output bersih disimpan di: {PROCESSED_PATH}")