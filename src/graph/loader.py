import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")

        missing = []
        if not uri:
            missing.append("NEO4J_URI")
        if not username:
            missing.append("NEO4J_USER")
        if not password:
            missing.append("NEO4J_PASSWORD")

        if missing:
            raise RuntimeError(
                "Missing Neo4j configuration: " + ", ".join(missing) + ". "
                "Set values in environment or .env before running the loader."
            )

        return cls(uri=uri, username=username, password=password)


class Neo4jGraphLoader:
    """
    High-performance batch ingestion loader for Research Atlas entities and relations.
    """

    def __init__(
        self,
        uri: str | None = None,
        auth: tuple[str, str] | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        config = Neo4jConfig.from_env()
        self.uri = uri or config.uri

        if auth is not None:
            self.username, self.password = auth
        else:
            self.username = username or config.username
            self.password = password or config.password

        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

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

    def load_relationships_in_batches(
        self,
        rel_type: str,
        source_label: str,
        target_label: str,
        source_key: str,
        target_key: str,
        edges: List[Dict[str, str]],
        batch_size: int = 5000,
    ):
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