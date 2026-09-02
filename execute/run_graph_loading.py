import json
import os
import logging
from dotenv import load_dotenv

from src.graph.schema import GraphSchemaManager
from src.graph.loader import Neo4jGraphLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_graph_pipeline(processed_path: str, neo4j_uri: str, neo4j_auth: tuple):
    """Executes schema creation and batch ingestion into Neo4j."""
    if not os.path.exists(processed_path):
        raise FileNotFoundError(
            f"Clean dataset not found at {processed_path}. Run preprocessing pipeline first."
        )

    logger.info(f"Loading processed graph data from {processed_path}...")
    with open(processed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    loader = Neo4jGraphLoader(uri=neo4j_uri, auth=neo4j_auth)
    schema_mgr = GraphSchemaManager(loader.driver)

    try:
        # 1. Setup Constraints and Indexes
        logger.info("Setting up database constraints and indexes...")
        schema_mgr.setup_schema()

        # 2. Ingest Nodes
        loader.load_nodes_in_batches("Paper", data["nodes"]["papers"])
        loader.load_nodes_in_batches("Author", data["nodes"]["authors"])
        loader.load_nodes_in_batches("Topic", data["nodes"]["topics"])

        # 3. Ingest Relationships
        loader.load_relationships_in_batches(
            rel_type="CITES",
            source_label="Paper",
            target_label="Paper",
            source_key="source_id",
            target_key="target_id",
            edges=data["edges"]["citations"]
        )
        loader.load_relationships_in_batches(
            rel_type="AUTHORED",
            source_label="Author",
            target_label="Paper",
            source_key="author_id",
            target_key="paper_id",
            edges=data["edges"]["authored"]
        )
        loader.load_relationships_in_batches(
            rel_type="HAS_TOPIC",
            source_label="Paper",
            target_label="Topic",
            source_key="paper_id",
            target_key="topic_id",
            edges=data["edges"]["has_topic"]
        )

        logger.info("Batch graph loading completed successfully.")

    finally:
        loader.close()


if __name__ == "__main__":
    load_dotenv()

    processed_file = os.getenv("PROCESSED_DATA_PATH", "data/processed/graph_data_clean.json")
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        raise ValueError("NEO4J_PASSWORD is not set in environment variables or .env file.")

    load_graph_pipeline(processed_file, uri, (user, password))