# Features PRD

# SODH – Research Suggestions & Deep Explore

## Product Requirements Document (PRD)

### Version: v1.0 (Implementation Ready)

---

# 1. Overview


---
**[ADDED: Tech Stack]**
* **Frontend:** React, TypeScript, Vite
* **Backend:** FastAPI (Python 3.12+)
* **ORM:** SQLAlchemy 2.x
* **Validation:** Pydantic v2
* **Database:** PostgreSQL
* **Migrations:** Alembic
* **Authentication:** JWT + bcrypt
* **Background Jobs:** FastAPI BackgroundTasks (MVP)
* **Embeddings:** Gemini Embedding API
* **Vector Storage:** pgvector
* **HTTP Client:** httpx
* **XML Parsing:** lxml
* **Testing:** pytest
* **Configuration:** Pydantic Settings + .env
---

This document defines two independent AI-powered research modules within SODH.

Although both accept a biomedical research topic as input, **their objectives, workflows, implementation, computational requirements and outputs are intentionally different.**

The two modules should remain completely independent so that either feature can be developed, deployed, maintained and upgraded without affecting the other.

---

# Feature Summary

| Feature                              | Purpose                                 | Backend                            | Evidence-backed                                     | Complexity |
| ------------------------------------ | --------------------------------------- | ---------------------------------- | --------------------------------------------------- | ---------- |
| **Feature A – Research Suggestions** | Rapid AI brainstorming                  | Gemini API only                    | No (unless Gemini explicitly references literature) | Low        |
| **Feature B – Deep Explore**         | Literature-backed research intelligence | PubMed + PMC + Europe PMC + Gemini | Yes                                                 | High       |

---

# FEATURE A

# Research Suggestions

---

## Objective

Provide rapid, AI-assisted research brainstorming from a user-provided biomedical topic.

This feature is designed for ideation rather than literature analysis.


**[ADDED: LLM Modularity]**
* The AI integration must be modular to allow switching LLM providers (Gemini, GPT, DeepSeek, Ollama, etc.) easily in the future.
* Current implementation will default to Gemini (e.g., 2.5 Flash).

It should help researchers quickly discover possible research directions before performing detailed literature exploration.

---

## Philosophy

Feature A is intentionally lightweight.

It should:

* return results within seconds
* consume minimal API tokens
* require only a single Gemini API call
* produce structured, concise outputs
* require no literature retrieval

---

## Input

Single research topic.

Example

```
Serum magnesium and acute ischemic stroke
```

---

## Workflow

```
User Topic

↓

Insert into predefined prompt template

↓

Single Gemini API Call

↓

Structured JSON Response

↓

Frontend Formatting

↓

Final User Output
```

---

## Prompt Strategy

A fixed prompt template should be maintained.

Only the research topic is dynamically inserted.

The prompt should instruct Gemini to

* think as a biomedical research mentor
* remain concise
* avoid unnecessary explanation
* output valid JSON
* avoid verbose reasoning
* maximize token efficiency

---

## Expected Output

Generate

* Emerging Research Topics
* Potential Research Gaps
* Potential Future Research Directions
* Suggested SRMA Topics
* Suggested Cohort Studies
* Suggested Clinical Studies
* Suggested RCT Ideas
* AI / ML Opportunities
* Novel Interdisciplinary Ideas
* Relevant references (if Gemini provides them)

---

## Characteristics

Uses Gemini only.

No PubMed.

No PMC.

No Europe PMC.

No XML parsing.

No embeddings.

No gap extraction.

No evidence ranking.

Single Gemini API call.

---

## Credits

Fixed credit cost.

(Default: 5 credits, configurable at developers end.)

---



---
# **[ADDED: FEATURE C]**
# **Standalone Search Builder**
---
## Objective
Provide an independent endpoint and frontend page where users can generate optimized literature search queries without executing the full Deep Explore pipeline.

## Input
* `topic` (string, required)
* `study_type` (string, optional)
* `purpose` (string, optional)

## Workflow
User Input → Gemini API Call → JSON Response containing optimized queries for PubMed, Scopus, and Embase → Output to user.

# FEATURE B

# Deep Explore

---

## Objective

Generate literature-backed research insights by analysing the Discussion, Limitations, Conclusions and Future Directions of relevant published studies.

Unlike Feature A, every major conclusion should be traceable back to supporting literature.

---

## Philosophy

Deep Explore prioritizes

Accuracy

Traceability

Transparency

Evidence-backed reasoning

Every major output should be expandable into its supporting papers and extracted evidence.

---

# Search Strategy

This is the most important stage.

The quality of every downstream analysis depends on retrieval quality.

---

## Literature Source

Primary

* PubMed E-utilities
* PubMed Central (PMC)
* Europe PMC

Future

* Crossref
* Semantic Scholar
* OpenAlex

---

## Search Pipeline

User Topic

↓


**[ADDED/MODIFIED: Query Expansion using LLM]**
* Before executing the PubMed search, a single Gemini API call is made to generate optimized Boolean queries.
* **Workflow:**
  * User Topic → Gemini Query Expansion
  * Gemini returns optimized search queries for PubMed, Embase, and Scopus in JSON format.
  * The PubMed query is parsed and executed via PubMed ESearch.
  * The final output presented to the user will also display these generated search queries.
* **Example:**
  * User: `Stroke magnesium`
  * Gemini returns: `("Stroke"[Mesh] OR stroke OR "ischemic stroke" OR "acute ischemic stroke") AND ("Magnesium"[Mesh] OR magnesium OR hypomagnesemia OR "serum magnesium")`

PubMed Search

↓

Apply filter

✓ Free Full Text

↓

Sort by PubMed relevance

↓

Retrieve Top N papers

Default

```
N = 100
```

User may increase N.

Higher N consumes more credits.

Example

100 papers

↓

10 Credits

200 papers

↓

15 Credits

300 papers

↓

20 Credits

(Default values configurable.)

---

## Why Free Full Text

Deep Explore requires XML access.

Therefore only papers with accessible full text are processed.

This restriction applies **only** to Feature B.

---

# Deep Explore Workflow

```
User Topic

↓

PubMed Search

↓

Free Full Text Filter

↓

Top N Relevant Papers

↓

Retrieve PMIDs

↓

Resolve PMC IDs

↓

Download XML

↓

Extract Relevant Sections

↓

Rule-Based Candidate Extraction

↓

Batch Gemini Extraction

↓

Gap Objects

↓

Gap Clustering

↓

Evidence Ranking

↓

Knowledge Graph

↓

Gemini Synthesis

↓

Final Report

↓

Cache
```

---

# XML Processing

Included Sections

* Discussion
* Limitations
* Conclusions
* Future Directions

Ignored

* Abstract
* Methods
* References
* Funding
* Acknowledgements
* Supplementary Material

Reason

These sections rarely contribute directly to research gap identification while significantly increasing processing cost.

---

# Rule-Based Candidate Extraction

## Objective

Reduce unnecessary Gemini processing.

Gemini should never receive complete discussion sections.

Instead deterministic code identifies only likely research-gap paragraphs.

---

## Candidate Selection Rules

A paragraph qualifies if one or more conditions are satisfied.

### Rule 1

Contains common gap phrases.

Examples

* further studies
* future research
* additional research
* remains unknown
* warrants investigation
* should investigate
* limitation
* limited by
* evidence is limited
* insufficient evidence
* mechanism remains unclear
* randomized trials are needed
* prospective studies
* multicentre studies

---

### Rule 2

Contains uncertainty language.

Examples

* unclear
* uncertain
* poorly understood
* inconsistent
* not established

---

### Rule 3

Contains comparison or contradiction language.

Examples

"Our findings differ..."

"In contrast..."

"Previous studies..."

---

### Rule 4

Paragraph belongs to

* Discussion
* Limitations
* Conclusion
* Future Directions

---

### Rule 5

Minimum paragraph size.

Very short isolated statements should be expanded by including neighbouring sentences.

---

## Candidate Output

Each extracted candidate stores

* PMID
* PMCID (if available)
* Section
* Paragraph ID
* Paragraph Text

These candidates become the only literature sent to Gemini.

---

# Gemini Processing — Stage 1

## Objective

Convert candidate paragraphs into structured Gap Objects.

Gemini is **not** asked to compare papers.

Gemini processes every candidate independently.

Multiple candidates are batched into large requests to reduce API overhead.

The backend automatically creates additional batches if the model context limit is exceeded.

---

## Gemini Input

Large batched collection

```
PMID

Section

Paragraph

Text
```

Repeated for every candidate.

---

## Gemini Output

Return structured JSON only.

Each candidate produces one or more Gap Objects.

Example

```
PMID

Gap Category

Gap Statement

Supporting Evidence

Confidence

Suggested Study

Section
```

No narrative output.

No overall conclusions.

No paper comparisons.

---

# Gap Objects

Gap Objects are the fundamental knowledge units of Deep Explore.

Each Gap Object contains

* PMID
* PMCID
* Gap Category
* Gap Statement
* Supporting Evidence
* Confidence
* Suggested Study
* Section
* Timestamp

Gap Objects are permanently stored.

Raw discussions are not.

---

# Gap Taxonomy

Examples

Population Gap

Methodological Gap

Evidence Gap

Mechanistic Gap

Therapeutic Gap

Diagnostic Gap

Technology Gap

Biomarker Gap

LMIC Gap

Pediatric Gap

Geriatric Gap

Sample Size Gap

RCT Gap

Long-term Follow-up Gap

Contradictory Evidence

Future Research Recommendation

---

# Backend Processing

No AI required.

The backend performs

* Parsing
* Storage
* Gap Object indexing
* Embedding generation
* Semantic clustering
* Frequency counting
* Evidence ranking
* Knowledge graph construction

---

# Knowledge Graph

Cluster similar Gap Objects.

Example

```
31 papers

↓

Population Gap

↓

Lack of pediatric evidence
```

instead of

31 separate statements.

---

# Evidence Ranking

Ranking uses deterministic scoring.

Factors

* Frequency
* Publication recency
* Study quality
* Evidence hierarchy
* Citation count
* Consistency

Output

High

Moderate

Low

---

# Gemini Processing — Stage 2

Input

Compressed Knowledge Graph only.

Gemini no longer sees raw papers.

Objective

Generate a readable final report.

---

# Final User Report

The report contains

* Top Research Gaps
* Evidence Strength
* Supporting Papers
* Representative Evidence Statements
* Research Trends
* Contradictions
* Underrepresented Populations
* Common Methodological Limitations
* Potential Future Studies
* Suggested SRMA Topics
* Suggested Cohort Studies
* Suggested RCT Ideas

Every section should be expandable.

Clicking a finding reveals

Gap Cluster

↓

Gap Objects

↓

Supporting Papers

↓

Original Evidence Statements

---

# Storage Strategy

Never store

* XML
* Discussions
* Complete AI responses

Store

* Gap Objects
* Gap Clusters
* Knowledge Graph
* Final Report Cache

---

# Caching Strategy

Gap Objects

Cached by PMID.

Never reprocess previously analysed papers.

---

Final Reports

Cached by normalized research topic.

Store only

* Final report
* Referenced Gap Cluster IDs

Never duplicate Gap Objects.

---

# Credits

Feature A: research suggestions:- 5 credits

Deep Explore credits depend upon corpus size.

Example

100 Papers

10 Credits

200 Papers

15 Credits

300 Papers

20 Credits

(Configurable.)

#

# Guiding Principles

1. Feature A and Feature B remain completely independent.

2. Retrieval always precedes reasoning in Feature B.

3. Deterministic code performs every task that does not require AI.

4. Gemini performs structured reasoning, not data retrieval.

5. Every literature-backed conclusion must remain explainable.

6. Raw literature is transient; structured knowledge is permanent.

7. Gap Objects form the core knowledge representation of SODH.

---

# Long-Term Vision

Deep Explore is designed as the foundation of SODH's Research Intelligence platform.

The credit system, later to have a admin panel for changing the amount of credits a user has, changing the amount of credits deduction associated with different features etc. Later to be connected to a gateway where credits can be bought.

The Gap Objects and Knowledge Graph generated here should become reusable building blocks for future modules including:

* SRMA Assistant
* Protocol Generator
* Grant Proposal Assistant
* Research Question Validator
* Evidence Dashboard
* Trend Analysis
* Research Recommendation Engine
* Collaborator Matching

# Auth/login page

A clean login page with login credentials as Email and password(to be set by user), security key(letters+digits+special character) , Forgot password system:- allows changing password after matching email and security key

# Database 

A robust yet clean database 

# Credit System

Comprehensive credit deduction system, initially for now, everyone starts at 50 credits. 

Rather than acting as an AI wrapper over PubMed, SODH should evolve into a continuously expanding biomedical knowledge graph capable of understanding, organizing and synthesizing scientific evidence while maintaining complete transparency and traceability.
