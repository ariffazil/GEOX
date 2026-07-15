# GEOX Contrast Primitive Search Spec

Status: Draft v1
Date: 2026-06-09
Owner: GEOX Search / Knowledge Systems

## 1) Problem Statement

Default enterprise Copilot + Graph ranking is optimized for exploitation:
- Prior interaction signals and social proximity dominate ranking.
- High-value low-activity documents are under-surfaced.
- Top-k truncation amplifies known-known bias.

For subsurface discovery work, this creates a structural blindspot: low anomalous contrast in retrieved evidence.

## 2) Design Goal

Operationalize a contrast primitive for discovery workflows.

Contrast primitive:
- Signal = Observation - Expectation
- Retrieval must intentionally surface evidence outside expectation, not only evidence matching prior behavior.

Success condition:
- Every research cycle returns both confirmation and disconfirmation candidates with traceable provenance.

## 3) Retrieval Policy (Dual-Lane)

Use two mandatory retrieval lanes per query:

1. Exploit lane (relevance):
- Semantic retrieval for direct task intent.
- Default weight target: 70% of final context budget.

2. Explore lane (contrast):
- Explicitly seek novelty, contradiction, and boundary-adjacent evidence.
- Default weight target: 30% of final context budget.

Hard rule:
- No final answer is complete if Explore lane returned zero candidates and no explicit uncertainty flag is emitted.

## 4) Ranking Model

For each candidate document d and query q:

- Rel(d, q): semantic relevance score.
- Nov(d, u): novelty distance from user/team interaction profile.
- Div(d, S): diversity gain versus current result set S.
- Ctr(d, h): contradiction likelihood against current hypothesis h.
- Qua(d): quality/confidence score from metadata and document integrity.

Final score:

Score(d) = w_r * Rel + w_n * Nov + w_d * Div + w_c * Ctr + w_q * Qua

Recommended starting weights:
- w_r = 0.45
- w_n = 0.20
- w_d = 0.10
- w_c = 0.20
- w_q = 0.05

Tune per domain using offline evaluation and analyst feedback.

## 5) Query Decomposition

Each user research prompt becomes four internal subqueries:

1. Core intent query:
- "Find strongest supporting evidence for X"

2. Contradiction query:
- "Find evidence that challenges X"

3. Boundary query:
- "Find adjacent-domain evidence likely relevant to X"

4. Orphan query:
- "Find high-content, low-activity historical documents related to X"

Merge and rerank with the contrast ranking model.

## 6) Data Plane and Indexing

Primary discovery index should be full-corpus vector + lexical hybrid search, not activity ranking.

Minimum requirements:
- Index all accessible SharePoint/OneDrive documents for authorized scope.
- Hybrid retrieval: vector + BM25.
- Chunking with section-level provenance.
- Metadata normalization for geology context:
  - basin, block, field, play, formation, well, author, team, vintage, document type.
- OCR pipeline for scanned legacy reports.

Graph/Copilot remains a convenience surface, not canonical discovery engine.

## 7) Governance Constraints (L0)

Mandatory constraints per retrieval run:
- Serendipity budget: >=20% context from Explore lane.
- Source diversity floor: >=3 distinct authors and >=2 distinct site/library origins.
- Temporal diversity floor: include at least one historical candidate older than configured threshold (for example 5 years).
- Disconfirmation floor: >=1 candidate with high contradiction score or explicit no-evidence flag.

If any floor fails:
- Result status must be PARTIAL, not COMPLETE.
- System must emit which floor failed and recommended next retrieval action.

## 8) Output Contract

Answer payload must include:
- Claim summary.
- Supporting evidence list.
- Contradicting evidence list.
- Boundary candidates (outside prior activity graph).
- Confidence band and residual uncertainty.
- Provenance per citation (doc ID, section, timestamp, index version).

## 9) KPI Set

Track discovery performance, not just relevance:
- Novelty@K: fraction of top-K results unseen by user/team history.
- Contradiction Hit Rate: percent of sessions with >=1 useful disconfirming source.
- Diversity Coverage: distinct authors/sites/time-buckets in top-K.
- Orphan Recovery Yield: useful findings from low-activity historical docs.
- Time-to-First-Useful-Unknown (TTFUU).
- Analyst Utility Score (human rating).

Guardrail metric:
- Noise Inflation: percent of explore candidates judged irrelevant.

## 10) Rollout Plan (30-60-90)

Days 0-30:
- Establish baseline on real GEOX questions.
- Build benchmark query set and human labels.
- Deploy manual dual-lane prompting protocol.

Days 31-60:
- Implement query decomposition and reranking service.
- Turn on governance floors and partial-result signaling.
- Launch orphan resurfacing batch job.

Days 61-90:
- Weight tuning and threshold calibration.
- Team adoption with dashboard and weekly review.
- Publish v1 operational playbook.

## 11) Failure Modes and Scar Protocol

If retrieval collapses into exploit-only behavior:
- Record Scar:
  - failing query,
  - missed evidence class,
  - root cause (index gap, metadata, ranking, policy),
  - safe fix,
  - prevention vector.
- Re-run with elevated explore weight and stricter diversity floors.

## 12) Immediate Prompt Templates

- "Return strongest support for X and at least 3 credible contradictions, including legacy docs not recently accessed."
- "Optimize for novelty and disconfirmation, not popularity."
- "Show boundary candidates from outside my collaborator graph and outside the last 12 months."
- "If contradiction set is empty, mark result PARTIAL and tell me what query expansion you attempted."

## 13) Decision

Adopt contrast primitive as a mandatory retrieval contract for GEOX discovery workflows.

Rationale:
- Relevance-only systems optimize task completion.
- Discovery systems require explicit exploration and disconfirmation mandates.
- This spec makes anomalous contrast operational and auditable.
