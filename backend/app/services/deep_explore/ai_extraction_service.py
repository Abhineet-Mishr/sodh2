from typing import List, Dict, Any
from app.services.llm.factory import get_llm_provider
from app.services.llm.prompt_loader import load_prompt
import json

async def extract_gap_objects(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not candidates:
        return []

    llm = get_llm_provider()

    # Simple batching strategy (e.g., 50 candidates per batch)
    batch_size = 50
    all_gap_objects = []

    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i + batch_size]
        batch_json_str = json.dumps(batch, indent=2)

        prompt = load_prompt("deep_explore/stage1_gap_extraction.md", CANDIDATE_BATCH=batch_json_str)

        try:
            gap_objects = await llm.generate_json(prompt)
            if isinstance(gap_objects, list):
                all_gap_objects.extend(gap_objects)
        except Exception as e:
            # Implement retry logic in production
            print(f"Error in batch extraction: {e}")

    return all_gap_objects

async def generate_final_report(knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
    llm = get_llm_provider()

    kg_json_str = json.dumps(knowledge_graph, indent=2)
    prompt = load_prompt("deep_explore/stage2_report_generation.md", KNOWLEDGE_GRAPH=kg_json_str)

    try:
        report = await llm.generate_json(prompt)
        return report
    except Exception as e:
        print(f"Error in report generation: {e}")
        return {}
