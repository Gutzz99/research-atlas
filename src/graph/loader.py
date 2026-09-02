import logging
from typing import Dict, List, Any
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class Neo4jGraphLoader:
    """
    High-performance batch ingestion loader for Research Atlas entities and relations.
    """

    def __init__(self, uri: str = "bolt://localhost:7687", auth: tuple = ("neo4j", "researchatlas2026")):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def load_nodes_in_batches(self, node_label: str, nodes: List[Dict[str, Any]], batch_size: int = 5000):
        """Batch creates or updates nodes using MERGE/UNWIND."""
        logger.info(f"Ingesting {len(nodes)} {node_label} nodes in batches of {batch_size}...")

        query = f"""
        UNWIND $batch AS row
        MERGE (n:{node_label} {{id: row.id}})
        SET n += row
        """

        with self.driver.session() as session:
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i + batch_size]
                session.run(query, batch=batch)
                logger.info(f"Loaded {i + len(batch)} / {len(nodes)} {node_label} nodes.")

    def load_relationships_in_batches(self, rel_type: str, source_label: str, target_label: str, 
                                      source_key: str, target_key: str, edges: List[Dict[str, str]], 
                                      batch_size: int = 5000):
        """Batch creates relationships using UNWIND."""
        logger.info(f"Ingesting {len(edges)} {rel_type} relationships...")

        query = f"""
        UNWIND $batch AS row
        MATCH (src:{source_label} {{id: row.{source_key}}})
        MATCH (tgt:{target_label} {{id: row.{target_key}}})
        MERGE (src)-[:{rel_type}]->(tgt)
        """

        with self.driver.session() as session:
            for i in range(0, len(edges), batch_size):
                batch = edges[i:i + batch_size]
                session.run(query, batch=batch)
                logger.info(f"Loaded {i + len(batch)} / {len(edges)} {rel_type} edges.")