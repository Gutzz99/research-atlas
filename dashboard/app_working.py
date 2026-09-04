from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import dotenv_values
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, Neo4jError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

st.set_page_config(page_title="Research Atlas", layout="wide")


@st.cache_resource
def get_driver():
    # Read the project-local file directly so dashboard credentials are reproducible.
    config = dotenv_values(ENV_FILE)
    uri = config.get("NEO4J_URI", "bolt://localhost:7687")
    user = config.get("NEO4J_USER", "neo4j")
    password = config.get("NEO4J_PASSWORD")

    if not password:
        raise RuntimeError(f"NEO4J_PASSWORD is missing from {ENV_FILE}")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    # Authenticate before rendering pages so connection failures are reported once.
    driver.verify_connectivity()
    return driver


def run_query(driver, query: str, parameters: dict | None = None) -> pd.DataFrame:
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return pd.DataFrame([record.data() for record in result])


st.title("Research Atlas")
st.caption(f"Using local configuration: {ENV_FILE}")

try:
    driver = get_driver()
except AuthError:
    st.error(
        "Neo4j rejected the credentials in the project .env file. "
        "Ensure they match the password used when the Neo4j database was initialized."
    )
    st.stop()
except (Neo4jError, OSError, RuntimeError) as error:
    st.error(f"Could not connect to Neo4j: {error}")
    st.stop()

st.success("Connected to Neo4j")

page = st.sidebar.radio("View", ["Overview", "Paper Explorer", "Communities"])

if page == "Overview":
    st.header("Corpus overview")
    metrics = run_query(
        driver,
        """
        // Keep each aggregate independent to avoid a Cartesian product.
        CALL {
            MATCH (p:Paper)
            RETURN count(p) AS papers
        }
        CALL {
            MATCH (a:Author)
            RETURN count(a) AS authors
        }
        CALL {
            MATCH ()-[r:CITES]->()
            RETURN count(r) AS citations
        }
        RETURN papers, authors, citations
        """,
    ).iloc[0]

    first, second, third = st.columns(3)
    first.metric("Papers", f"{int(metrics['papers']):,}")
    second.metric("Authors", f"{int(metrics['authors']):,}")
    third.metric("Citation edges", f"{int(metrics['citations']):,}")

    st.subheader("Top papers by PageRank")
    top_papers = run_query(
        driver,
        """
        MATCH (p:Paper)
        RETURN p.title AS Title,
               p.year AS Year,
               p.cited_by_count AS Citations,
               round(coalesce(p.pagerank, 0.0), 4) AS PageRank
        ORDER BY p.pagerank DESC
        LIMIT 10
        """,
    )
    st.dataframe(top_papers, use_container_width=True, hide_index=True)

elif page == "Paper Explorer":
    st.header("Paper explorer")
    term = st.text_input("Title contains", "ImageNet")
    results = run_query(
        driver,
        """
        MATCH (p:Paper)
        WHERE toLower(coalesce(p.title, '')) CONTAINS toLower($term)
        RETURN p.id AS ID,
               p.title AS Title,
               p.year AS Year,
               p.cited_by_count AS Citations,
               round(coalesce(p.pagerank, 0.0), 4) AS PageRank
        ORDER BY p.pagerank DESC
        LIMIT 10
        """,
        {"term": term},
    )
    st.dataframe(results, use_container_width=True, hide_index=True)

    if not results.empty:
        selected_id = st.selectbox("Paper", results["ID"].tolist())
        context = run_query(
            driver,
            """
            MATCH (p:Paper {id: $paper_id})
            OPTIONAL MATCH (p)-[:CITES]->(out:Paper)
            OPTIONAL MATCH (incoming:Paper)-[:CITES]->(p)
            RETURN p.title AS Title,
                   collect(DISTINCT out.title)[..5] AS References,
                   collect(DISTINCT incoming.title)[..5] AS CitedBy
            """,
            {"paper_id": selected_id},
        )
        if not context.empty:
            st.write(context.iloc[0].to_dict())

else:
    st.header("Research communities")
    communities = run_query(
        driver,
        """
        MATCH (p:Paper)
        WHERE p.community_id IS NOT NULL
        RETURN p.community_id AS Community, count(p) AS Papers
        ORDER BY Papers DESC
        LIMIT 15
        """,
    )
    st.bar_chart(communities.set_index("Community"))
    st.dataframe(communities, use_container_width=True, hide_index=True)
