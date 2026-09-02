import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class GraphCentralityAnalyzer:
    """
    Handles In-Memory Graph Projections and Centrality algorithms (PageRank) via Neo4j GDS.
    """

    def __init__(self, driver):
        self.driver = driver

    def project_citation_graph(self, graph_name: str = "citation-graph"):
        """Creates an In-Memory GDS Projection of the Paper Citation Network."""
        drop_query = f"CALL gds.graph.drop('{graph_name}', false) YIELD graphName;"
        
        project_query = f"""
        CALL gds.graph.project(
            '{graph_name}',
            'Paper',
            {{
                CITES: {{
                    type: 'CITES',
                    orientation: 'NATURAL'
                }}
            }}
        )
        YIELD graphName, nodeCount, relationshipCount;
        """

        with self.driver.session() as session:
            session.run(drop_query)
            result = session.run(project_query).single()
            logger.info(
                f"Graph Projection '{result['graphName']}' created with "
                f"{result['nodeCount']} nodes and {result['relationshipCount']} relationships."
            )

    def run_pagerank(self, graph_name: str = "citation-graph", damping_factor: float = 0.85, max_iterations: int = 20):
        """Runs PageRank and writes results directly back to node properties ('pagerank')."""
        query = f"""
        CALL gds.pageRank.write(
            '{graph_name}',
            {{
                maxIterations: $max_iterations,
                dampingFactor: $damping_factor,
                writeProperty: 'pagerank'
            }}
        )
        YIELD nodePropertiesWritten, computeMillis;
        """

        with self.driver.session() as session:
            result = session.run(
                query, 
                max_iterations=max_iterations, 
                damping_factor=damping_factor
            ).single()
            logger.info(
                f"PageRank computation complete. Updated {result['nodePropertiesWritten']} "
                f"Paper nodes in {result['computeMillis']} ms."
            )