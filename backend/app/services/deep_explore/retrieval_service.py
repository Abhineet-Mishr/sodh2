from typing import List, Dict, Tuple, Optional
from app.utils.pubmed import esearch, elink_pmc, fetch_pmc_xml
from app.utils.xml_parser import parse_pmc_xml
import asyncio

async def retrieve_and_parse_literature(query: str, paper_limit: int) -> List[Dict]:
    """
    1. Search PubMed
    2. Link to PMC
    3. Filter for Free Full Text (those with PMCIDs)
    4. Fetch XML
    5. Parse XML sections
    """
    # 1. Search PubMed
    # Add Free Full text filter natively
    fft_query = f"({query}) AND free full text[sb]"
    pmids = await esearch(fft_query, max_results=paper_limit * 2) # Get extra in case some PMC links fail

    if not pmids:
        return []

    # 2. Link to PMC
    pmid_to_pmcid = await elink_pmc(pmids)

    # 3. Filter to top N that have PMCIDs
    valid_papers = []
    for pmid in pmids:
        if pmid in pmid_to_pmcid:
            valid_papers.append({
                "pmid": pmid,
                "pmcid": pmid_to_pmcid[pmid]
            })
            if len(valid_papers) >= paper_limit:
                break

    # 4 & 5. Fetch and Parse XML concurrently
    async def process_paper(paper: Dict) -> Optional[Dict]:
        xml_content = await fetch_pmc_xml(paper["pmcid"])
        if not xml_content:
            return None

        sections = parse_pmc_xml(xml_content)
        # Check if we actually extracted anything useful
        if not any(sections.values()):
            return None

        paper["sections"] = sections
        return paper

    tasks = [process_paper(p) for p in valid_papers]
    results = await asyncio.gather(*tasks)

    # Filter out failed papers
    successful_papers = [r for r in results if r is not None]

    return successful_papers
