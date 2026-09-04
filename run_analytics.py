import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError

from src.analysis.centrality import GraphCentralityAnalyzer
from src.analysis.communities import CommunityDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def ensure_gds_available(driver):
    """Validate that Neo4j Graph Data Science is enabled before running analytics."""
    with driver.session() as session:
        try:
            session.run("CALL gds.version() YIELD gdsVersion RETURN gdsVersion AS version").single()
        except ClientError as exc:
            raise RuntimeError(
                "Neo4j GDS is not available in the current database. "
                "Use the Neo4j Enterprise image and set NEO4J_ACCEPT_LICENSE_AGREEMENT=yes. "
                "The project Docker config must use neo4j:5.18.0-enterprise."
            ) from exc


def run_gds_analytics_pipeline(neo4j_uri: str, neo4j_auth: tuple, graph_name: str = "citation-graph"):
    """Executes GDS graph projection, PageRank centrality, and Louvain community detection."""
    logger.info(f"Connecting to Neo4j instance at {neo4j_uri}...")
    driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)

    try:
        ensure_gds_available(driver)
    except Exception:
        driver.close()
        raise

    centrality_analyzer = GraphCentralityAnalyzer(driver)
    community_detector = CommunityDetector(driver)

    try:
        # 1. Project Citation Subgraph into RAM
        logger.info(f"Creating in-memory GDS graph projection: '{graph_name}'...")
        centrality_analyzer.project_citation_graph(graph_name=graph_name)

        # 2. Compute PageRank
        logger.info("Computing PageRank centrality scores...")
        centrality_analyzer.run_pagerank(graph_name=graph_name)

        # 3. Detect Communities via Louvain
        logger.info("Executing Louvain community detection...")
        community_detector.run_louvain(graph_name=graph_name)

        logger.info("Graph Data Science analytics pipeline completed successfully.")

    finally:
        # 4. Release In-Memory Projection & Close Driver
        logger.info(f"Dropping in-memory projection '{graph_name}' and closing session...")
        community_detector.drop_graph_projection(graph_name=graph_name)
        driver.close()


if __name__ == "__main__":
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        raise ValueError("NEO4J_PASSWORD is not set in environment variables or .env file.")

    run_gds_analytics_pipeline(uri, (user, password))