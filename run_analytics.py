import logging
from neo4j import GraphDatabase
from src.analysis.centrality import GraphCentralityAnalyzer
from src.analysis.communities import CommunityDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_AUTH = ("neo4j", "researchatlas2026")
    GRAPH_NAME = "citation-graph"

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    centrality_analyzer = GraphCentralityAnalyzer(driver)
    community_detector = CommunityDetector(driver)

    try:
        # 1. Project Citation Subgraph into Memory
        centrality_analyzer.project_citation_graph(graph_name=GRAPH_NAME)

        # 2. Run PageRank Score Computation
        centrality_analyzer.run_pagerank(graph_name=GRAPH_NAME)

        # 3. Run Louvain Community Detection
        community_detector.run_louvain(graph_name=GRAPH_NAME)

    finally:
        # 4. Clean up Memory Projection
        community_detector.drop_graph_projection(graph_name=GRAPH_NAME)
        driver.close()

    print("Analisis Graph Data Science (PageRank & Louvain) selesai!")