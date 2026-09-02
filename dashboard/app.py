import streamlit as st
import pandas as pd
from neo4j import GraphDatabase

# Page Configuration
st.set_page_config(page_title="Research Atlas MVP", layout="wide", page_icon="🕸️")

# Neo4j Connection Setup
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "researchatlas2026")

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

driver = get_driver()

def run_cypher(query, params=None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return pd.DataFrame([record.data() for record in result])

# Sidebar Navigation
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Paper Explorer", "Communities"])

# ---------------------------------------------------------
# PAGE 1: OVERVIEW
# ---------------------------------------------------------
if page == "Overview":
    st.title("🌐 Research Atlas Overview")
    st.markdown("Metrics & summary of the scientific literature corpus.")

    col1, col2, col3 = st.columns(3)
    
    paper_cnt = run_cypher("MATCH (p:Paper) RETURN count(p) as count")['count'][0]
    author_cnt = run_cypher("MATCH (a:Author) RETURN count(a) as count")['count'][0]
    cite_cnt = run_cypher("MATCH ()-[r:CITES]->() RETURN count(r) as count")['count'][0]

    col1.metric("Total Papers", f"{paper_cnt:,}")
    col2.metric("Total Authors", f"{author_cnt:,}")
    col3.metric("Citation Edges", f"{cite_cnt:,}")

    st.subheader("🔥 Top 10 Influential Papers (by PageRank)")
    df_top = run_cypher("""
        MATCH (p:Paper)
        RETURN p.title as Title, p.year as Year, p.cited_by_count as Citations, round(p.pagerank, 2) as PageRank
        ORDER BY p.pagerank DESC LIMIT 10
    """)
    st.dataframe(df_top, use_container_width=True)

# ---------------------------------------------------------
# PAGE 2: PAPER EXPLORER
# ---------------------------------------------------------
elif page == "Paper Explorer":
    st.title("🔍 Paper Lineage Explorer")
    
    search_term = st.text_input("Search paper title containing:", "ImageNet")
    
    if search_term:
        query_search = """
        MATCH (p:Paper)
        WHERE toLower(p.title) CONTAINS toLower($term)
        RETURN p.id as ID, p.title as Title, p.year as Year, p.cited_by_count as Citations, round(p.pagerank, 2) as PageRank
        ORDER BY p.pagerank DESC LIMIT 10
        """
        df_results = run_cypher(query_search, {"term": search_term})
        st.write("### Search Results")
        st.dataframe(df_results, use_container_width=True)

        if not df_results.empty:
            selected_id = st.selectbox("Select Paper ID to view Ego-Graph Network:", df_results["ID"])
            
            # Fetch 1-hop Citations
            ego_query = """
            MATCH (p:Paper {id: $pid})
            OPTIONAL MATCH (p)-[:CITES]->(out:Paper)
            OPTIONAL MATCH (inc:Paper)-[:CITES]->(p)
            RETURN p.title as Paper, collect(distinct out.title)[..5] as Cites, collect(distinct inc.title)[..5] as CitedBy
            """
            ego_df = run_cypher(ego_query, {"pid": selected_id})
            
            st.subheader("Citation Context")
            st.write(f"**References (Cites):** {ego_df['Cites'][0]}")
            st.write(f"**Impact (Cited By):** {ego_df['CitedBy'][0]}")

# ---------------------------------------------------------
# PAGE 3: COMMUNITIES
# ---------------------------------------------------------
elif page == "Communities":
    st.title("🧩 Community Clusters (Louvain)")
    
    df_comm = run_cypher("""
        MATCH (p:Paper)
        WHERE p.community_id IS NOT NULL
        RETURN p.community_id as Community, count(p) as PapersCount
        ORDER BY PapersCount DESC LIMIT 15
    """)
    
    st.subheader("Top Research Clusters")
    st.bar_chart(df_comm.set_index("Community"))

    selected_comm = st.selectbox("Inspect Community ID:", df_comm["Community"])
    
    if selected_comm is not None:
        comm_papers = run_cypher("""
            MATCH (p:Paper {community_id: $cid})
            RETURN p.title as Title, p.year as Year, p.cited_by_count as Citations, round(p.pagerank, 2) as PageRank
            ORDER BY p.pagerank DESC LIMIT 10
        """, {"cid": selected_comm})
        
        st.write(f"### Top Papers in Community #{selected_comm}")
        st.dataframe(comm_papers, use_container_width=True)