import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

class GraphSchemaManager:
    """
    Manages Neo4j Constraints and Indexes to ensure ingestion speed and data uniqueness.
    """

    def __init__(self, driver):
        self.driver = driver

    def setup_schema(self):
        """Creates unique constraints and lookup indexes on node IDs."""
        constraints = [
            "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE;",
            "CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE;",
            "CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;"
        ]

        indexes = [
            "CREATE INDEX paper_year_idx IF NOT EXISTS FOR (p:Paper) ON (p.year);",
            "CREATE INDEX author_name_idx IF NOT EXISTS FOR (a:Author) ON (a.name);"
        ]

        with self.driver.session() as session:
            for statement in constraints + indexes:
                session.run(statement)
                logger.info(f"Executed Schema Statement: {statement}")

        logger.info("Database Schema, Constraints, and Indexes setup complete.")
    
    def clear_database(self):
        """Wipes the database. Use with caution during dev resets."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n;")
            logger.warning("Database cleared.")