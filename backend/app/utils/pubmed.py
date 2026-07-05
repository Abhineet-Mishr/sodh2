import httpx
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
from app.core.config import settings
import asyncio

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

async def esearch(query: str, max_results: int) -> List[str]:
    """Search PubMed and return a list of PMIDs."""
    url = f"{PUBMED_BASE_URL}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "usehistory": "y",
        "tool": settings.NCBI_TOOL_NAME,
        "email": settings.NCBI_EMAIL
    }
    if settings.PUBMED_API_KEY:
        params["api_key"] = settings.PUBMED_API_KEY

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])

async def elink_pmc(pmids: List[str]) -> Dict[str, str]:
    """Given a list of PMIDs, find their corresponding PMCIDs (Free Full Text)."""
    if not pmids:
        return {}

    url = f"{PUBMED_BASE_URL}/elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "db": "pmc",
        "retmode": "json",
        "tool": settings.NCBI_TOOL_NAME,
        "email": settings.NCBI_EMAIL
    }
    if settings.PUBMED_API_KEY:
        params["api_key"] = settings.PUBMED_API_KEY

    # httpx handles multiple values for the same key nicely using lists
    # params['id'] = pmids but let's do it manually for eutils quirks
    query_string = "&".join([f"id={pmid}" for pmid in pmids])
    full_url = f"{url}?{query_string}"

    pmid_to_pmcid = {}
    async with httpx.AsyncClient() as client:
        response = await client.get(full_url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        linksets = data.get("linksets", [])
        for linkset in linksets:
            # Each linkset has idlists (input PMIDs) and linksetdbs (linked IDs)
            input_pmids = linkset.get("ids", [])
            if not input_pmids:
                continue
            input_pmid = str(input_pmids[0])

            linksetdbs = linkset.get("linksetdbs", [])
            for ldb in linksetdbs:
                if ldb.get("linkname") == "pubmed_pmc":
                    pmcids = ldb.get("links", [])
                    if pmcids:
                        pmid_to_pmcid[input_pmid] = "PMC" + str(pmcids[0])

    return pmid_to_pmcid

async def fetch_pmc_xml(pmcid: str) -> Optional[str]:
    """Fetch the full XML for a PMCID."""
    url = f"{PUBMED_BASE_URL}/efetch.fcgi"
    params = {
        "db": "pmc",
        "id": pmcid.replace("PMC", ""),
        "retmode": "xml",
        "tool": settings.NCBI_TOOL_NAME,
        "email": settings.NCBI_EMAIL
    }
    if settings.PUBMED_API_KEY:
        params["api_key"] = settings.PUBMED_API_KEY

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=45.0)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError:
            return None
