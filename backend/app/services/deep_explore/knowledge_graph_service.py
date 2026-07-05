from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.gap_object import GapObject
from app.models.gap_cluster import GapCluster
from app.services.llm.factory import get_llm_provider
import uuid

async def build_knowledge_graph(db: Session, gap_objects: List[GapObject]) -> Dict[str, Any]:
    if not gap_objects:
        return {"clusters": []}

    llm = get_llm_provider()

    # 1. Generate Embeddings using Gemini provider
    for obj in gap_objects:
        if not obj.embedding:
            try:
                emb = await llm.generate_embeddings(obj.gap_statement)
                obj.embedding = emb
            except Exception as e:
                print(f"Embedding failed for object {obj.gap_object_id}: {e}")
    db.commit()

    # 2. Semantic Clustering (Using PGVector inside Postgres)
    # We will do a simple single-pass clustering:
    # For each unclustered object, find similar ones with distance < threshold
    clusters_data = []

    unclustered = list(gap_objects)
    threshold = 0.25 # Cosine distance threshold (lower is more similar)

    while unclustered:
        seed = unclustered.pop(0)

        # Find similar objects in the database using pgvector's L2 distance or cosine distance.
        # We use cosine distance: `<=>`
        if seed.embedding is None:
            continue

        similar_objs = db.query(GapObject).filter(
            GapObject.embedding.cosine_distance(seed.embedding) < threshold,
            GapObject.gap_category == seed.gap_category # Keep clusters strictly within category
        ).all()

        # Determine the members of this cluster
        cluster_members = [o for o in similar_objs if o in unclustered] + [seed]

        # Remove them from unclustered
        for member in cluster_members:
            if member in unclustered:
                unclustered.remove(member)

        cluster_id = str(uuid.uuid4())
        cluster_title = f"{seed.gap_category} Insight"
        cluster_summary = f"Aggregated {len(cluster_members)} gap statements related to {seed.gap_category}."

        evidence_score = min(100.0, (len(cluster_members) * 10) + sum([obj.confidence for obj in cluster_members]))
        confidence_level = "High" if evidence_score >= 85 else "Moderate" if evidence_score >= 60 else "Low"

        db_cluster = GapCluster(
            cluster_id=cluster_id,
            cluster_title=cluster_title,
            cluster_summary=cluster_summary,
            gap_category=seed.gap_category,
            evidence_score=evidence_score,
            confidence_level=confidence_level,
            gap_object_count=len(cluster_members),
            paper_count=len(set([o.pmid for o in cluster_members])),
            gap_objects=cluster_members
        )
        db.add(db_cluster)

        clusters_data.append({
            "cluster_id": cluster_id,
            "cluster_title": cluster_title,
            "gap_category": seed.gap_category,
            "paper_count": db_cluster.paper_count,
            "confidence": confidence_level
        })

    db.commit()

    return {
        "clusters": clusters_data,
        "contradictions": [],
        "population_summary": {},
        "methodology_summary": {}
    }
