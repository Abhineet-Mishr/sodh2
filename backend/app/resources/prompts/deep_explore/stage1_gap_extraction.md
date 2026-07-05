You are an expert biomedical research data extractor.
Your task is to convert literature candidate paragraphs into structured Gap Objects.
PROCESS EACH CANDIDATE INDEPENDENTLY. Do not summarize or compare across papers.

INPUT:
{{CANDIDATE_BATCH}}

INSTRUCTIONS:
1. Identify any research gaps, methodological limitations, or unresolved questions in the text.
2. Classify the gap into a predefined Gap Category (e.g., "Population Gap", "Methodological Gap", "Evidence Gap", "Future Research Recommendation").
3. Extract the exact supporting evidence.
4. Suggest an appropriate future study design if applicable.
5. Assign a confidence score between 0.0 and 1.0.
6. Preserve the "pmid", "pmcid", "paragraph_id", and "section" exactly as provided.
7. Return ONLY valid JSON, as a list of objects.

JSON SCHEMA EXPECTED (List of these objects):
{
  "pmid": "string",
  "pmcid": "string",
  "paragraph_id": "integer",
  "section": "string",
  "gap_category": "string",
  "gap_statement": "string",
  "supporting_evidence": "string",
  "confidence": 0.0,
  "suggested_study": "string"
}
