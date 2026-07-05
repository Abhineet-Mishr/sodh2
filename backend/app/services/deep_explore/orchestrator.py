from sqlalchemy.orm import Session
from app.models.deep_explore_job import DeepExploreJob
from app.models.paper import Paper
from app.models.gap_object import GapObject
from app.models.report_cache import ReportCache
from app.services.deep_explore import retrieval_service, ai_extraction_service, knowledge_graph_service, search_builder_service
from app.schemas.search import SearchBuilderRequest
from app.services.deep_explore.candidate_service import candidate_extractor
import uuid
import json
from datetime import datetime

async def execute_deep_explore_job(db: Session, job_id: str):
    job = db.query(DeepExploreJob).filter(DeepExploreJob.job_id == job_id).first()
    if not job:
        return

    try:
        job.status = "SEARCHING"
        db.commit()

        # Phase 0: LLM Query Expansion
        search_req = SearchBuilderRequest(topic=job.requested_topic)
        search_queries = await search_builder_service.generate_search_queries(search_req)

        # Save generated queries to job
        job.search_queries = {
            "pubmed_query": search_queries.pubmed_query,
            "scopus_query": search_queries.scopus_query,
            "embase_query": search_queries.embase_query
        }
        db.commit()

        # Phase 1: Retrieval (using the generated PubMed query)
        papers = await retrieval_service.retrieve_and_parse_literature(search_queries.pubmed_query, job.paper_limit)

        # Save parsed papers to DB
        for p in papers:
            if not db.query(Paper).filter(Paper.pmid == p["pmid"]).first():
                db_paper = Paper(
                    pmid=p["pmid"],
                    pmcid=p["pmcid"],
                    title=f"Paper {p['pmid']}",
                    processed=True
                )
                db.add(db_paper)
        db.commit()

        job.status = "CANDIDATE_EXTRACTION"
        db.commit()

        # Phase 2: Candidate Extraction
        all_candidates = []
        for p in papers:
            cands = candidate_extractor.extract_candidates(p)
            all_candidates.extend(cands)

        job.status = "AI_STAGE_1"
        db.commit()

        # Phase 3: Gemini Extraction (Stage 1)
        raw_gap_objects = await ai_extraction_service.extract_gap_objects(all_candidates)

        # Save Gap Objects to DB
        saved_gap_objects = []
        for go_data in raw_gap_objects:
            if db.query(Paper).filter(Paper.pmid == go_data.get("pmid")).first():
                go_id = str(uuid.uuid4())
                db_go = GapObject(
                    gap_object_id=go_id,
                    pmid=go_data["pmid"],
                    pmcid=go_data.get("pmcid"),
                    gap_category=go_data.get("gap_category", "Unknown"),
                    gap_statement=go_data.get("gap_statement", ""),
                    supporting_evidence=go_data.get("supporting_evidence", ""),
                    section=go_data.get("section", ""),
                    confidence=float(go_data.get("confidence", 0.0)),
                    suggested_study=go_data.get("suggested_study")
                )
                db.add(db_go)
                saved_gap_objects.append(db_go)
        db.commit()

        job.status = "KNOWLEDGE_GRAPH"
        db.commit()

        # Phase 4: Knowledge Graph (with pgvector)
        kg_data = await knowledge_graph_service.build_knowledge_graph(db, saved_gap_objects)

        job.status = "AI_STAGE_2"
        db.commit()

        # Phase 5: AI Synthesis
        final_report = await ai_extraction_service.generate_final_report(kg_data)

        # Store in Report Cache
        cache_id = str(uuid.uuid4())
        cluster_ids = [c["cluster_id"] for c in kg_data["clusters"]]

        report_cache = ReportCache(
            cache_id=cache_id,
            normalized_topic=job.normalized_topic,
            paper_limit=job.paper_limit,
            generated_report=final_report,
            cluster_ids=cluster_ids
        )
        db.add(report_cache)

        job.report_cache_id = cache_id
        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        if job.started_at:
            job.execution_time = int((job.completed_at - job.started_at).total_seconds())

        db.commit()

        from app.services.credit.credit_service import finalize_deduction_by_job_id
        finalize_deduction_by_job_id(db, job_id)

    except Exception as e:
        job.status = "FAILED"
        job.completed_at = datetime.utcnow()
        db.commit()
        from app.services.credit.credit_service import refund_credits_by_job_id
        try:
            refund_credits_by_job_id(db, job_id)
        except Exception as refund_error:
            print(f"Failed to refund credits for job {job_id}: {refund_error}")
        print(f"Job {job_id} failed: {e}")
