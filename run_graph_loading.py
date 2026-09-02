import json
import os
import logging
from src.graph.schema import GraphSchemaManager
from src.graph.loader import Neo4jGraphLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    PROCESSED_PATH = "data/processed/graph_data_clean.json"
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_AUTH = ("neo4j", "researchatlas2026")

    if not os.path.exists(PROCESSED_PATH):
        raise FileNotFoundError(f"File {PROCESSED_PATH} tidak ditemukan. Jalankan preprocessing dahulu.")

    with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    loader = Neo4jGraphLoader(uri=NEO4J_URI, auth=NEO4J_AUTH)
    schema_mgr = GraphSchemaManager(loader.driver)

    # 1. Setup Constraints & Indexes
    schema_mgr.setup_schema()

    # 2. Ingest Nodes
    loader.load_nodes_in_batches("Paper", data["nodes"]["papers"])
    loader.load_nodes_in_batches("Author", data["nodes"]["authors"])
    loader.load_nodes_in_batches("Topic", data["nodes"]["topics"])

    # 3. Ingest Relationships
    loader.load_relationships_in_batches(
        rel_type="CITES", source_label="Paper", target_label="Paper",
        source_key="source_id", target_key="target_id", edges=data["edges"]["citations"]
    )
    loader.load_relationships_in_batches(
        rel_type="AUTHORED", source_label="Author", target_label="Paper",
        source_key="author_id", target_key="paper_id", edges=data["edges"]["authored"]
    )
    loader.load_relationships_in_batches(
        rel_type="HAS_TOPIC", source_label="Paper", target_label="Topic",
        source_key="paper_id", target_key="topic_id", edges=data["edges"]["has_topic"]
    )

    loader.close()
    print("Graph loading selesai! Buka http://localhost:7474 untuk mengeksplorasi database.")