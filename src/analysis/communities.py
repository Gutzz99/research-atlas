import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class CommunityDetector:
    """
    Executes Community Detection algorithms (Louvain/Leiden) via GDS 
    to partition the citation graph into research clusters.
    """

    def __init__(self, driver):
        self.driver = driver

    def run_louvain(self, graph_name: str = "citation-graph"):
        """Executes Louvain Community Detection and writes 'community_id' back to nodes."""
        query = f"""
        CALL gds.louvain.write(
            '{graph_name}',
            {{
                writeProperty: 'community_id'
            }}
        )
        YIELD communityCount, modularity, modularities;
        """

        with self.driver.session() as session:
            result = session.run(query).single()
            logger.info(
                f"Louvain Community Detection complete. Found {result['communityCount']} "
                f"communities with Modularity score: {result['modularity']:.4f}."
            )

    def drop_graph_projection(self, graph_name: str = "citation-graph"):
        """Cleans up the in-memory graph projection after analysis."""
        query = f"CALL gds.graph.drop('{graph_name}', false) YIELD graphName;"
        with self.driver.session() as session:
            session.run(query)
            logger.info(f"In-memory graph '{graph_name}' released from RAM.")