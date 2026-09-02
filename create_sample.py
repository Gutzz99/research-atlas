import json
import os

def generate_sample_dataset(
    processed_path="data/processed/graph_data_clean.json",
    sample_output_path="data/sample/sample_corpus.json",
    sample_paper_limit=500
):
    if not os.path.exists(processed_path):
        print(f"File {processed_path} tidak ditemukan. Jalankan preprocessing dahulu.")
        return

    with open(processed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Pick top N papers based on citations in the clean corpus
    sample_papers = data["nodes"]["papers"][:sample_paper_limit]
    sample_paper_ids = {p["id"] for p in sample_papers}

    # Filter authors, topics, and valid closed-graph edges
    sample_citations = [
        c for c in data["edges"]["citations"]
        if c["source_id"] in sample_paper_ids and c["target_id"] in sample_paper_ids
    ]
    
    sample_authored = [a for a in data["edges"]["authored"] if a["paper_id"] in sample_paper_ids]
    sample_author_ids = {a["author_id"] for a in sample_authored}
    sample_authors = [a for a in data["nodes"]["authors"] if a["id"] in sample_author_ids]

    sample_topics = [t for t in data["edges"]["has_topic"] if t["paper_id"] in sample_paper_ids]
    sample_topic_ids = {t["topic_id"] for t in sample_topics}
    sample_topic_nodes = [t for t in data["nodes"]["topics"] if t["id"] in sample_topic_ids]

    sample_payload = {
        "nodes": {
            "papers": sample_papers,
            "authors": sample_authors,
            "topics": sample_topic_nodes
        },
        "edges": {
            "citations": sample_citations,
            "authored": sample_authored,
            "has_topic": sample_topics
        }
    }

    os.makedirs(os.path.dirname(sample_output_path), exist_ok=True)
    with open(sample_output_path, "w", encoding="utf-8") as f:
        json.dump(sample_payload, f, ensure_ascii=False, indent=2)

    print(f"Sample dataset ({len(sample_papers)} papers) berhasil dibuat di: {sample_output_path}")

if __name__ == "__main__":
    generate_sample_dataset()