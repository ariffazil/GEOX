"""
GEOX False-Success Monitor — TF-IDF + Heuristic Detector

Detects the "transport-success ≠ evidence-success" defect described in
Advani (arXiv:2606.09863): agents report completion confidently but the
actual programmatic state shows no change or incorrect results.

Architecture (from Roadmap §1.4):
  - Lightweight TF-IDF detector on closing-message language
  - Heuristic features: empty evidence, contradiction signals, confidence markers
  - NOT an LLM judge (LLM judges cap at AUROC ≤ 0.65)
  - Target: AUROC ≥ 0.83 on geoscience corpus; 4-8x more FS detected than LLM judge
  - ~3,300x lower latency than LLM judge (microseconds vs seconds)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("geox.monitoring.false_success")

# ── False-Success Language Patterns ──────────────────────────────────────────
# These are the "confident closing-message" patterns that LLM judges
# anchor on. Advani 2026: "no configuration across 5 judges, 5 prompt
# strategies, and full task specifications exceeds AUROC 0.65" because
# judges "anchor on confident closing-message language."

_FALSE_SUCCESS_TRIGRAMS = [
    # Confident closing without evidence
    ("successfully", "completed", "task"),
    ("ready", "complete", "done"),
    ("all", "steps", "completed"),
    ("task", "finished", "successfully"),
    ("execution", "completed", "success"),
    ("processed", "successfully", "results"),
    ("everything", "looks", "good"),
    ("no", "errors", "found"),
    ("validation", "passed", "all"),
    ("checks", "passed", "successfully"),
    # Hallucinated evidence
    ("data", "loaded", "successfully"),
    ("model", "trained", "converged"),
    ("interpretation", "complete", "results"),
    ("analysis", "finished", "output"),
    ("computation", "done", "returning"),
]

_FALSE_SUCCESS_BIGRAMS = [
    ("completed", "successfully"),
    ("successfully", "processed"),
    ("ready", "use"),
    ("all", "good"),
    ("everything", "working"),
    ("done", "here"),
    ("looks", "correct"),
    ("should", "work"),
    ("seems", "fine"),
    ("appears", "valid"),
]

_FALSE_SUCCESS_UNIGRAMS = {
    "success",
    "complete",
    "done",
    "ready",
    "finished",
    "resolved",
    "achieved",
    "verified",
    "validated",
    "confirmed",
}

# Evidence absence signals: text that claims success without actual data
_EMPTY_EVIDENCE_PATTERNS = [
    re.compile(r"no\s+(data|results|output|evidence|findings)\s+(available|found|returned)", re.I),
    re.compile(r"empty\s+(result|response|output|dataset)", re.I),
    re.compile(r"0\s+(results|records|entries|points|wells)\s+(found|returned|matched)", re.I),
    re.compile(r"null\s+(result|data|output)", re.I),
    re.compile(r"nothing\s+(to|found|returned|matched)", re.I),
]

_CONTRADICTION_SIGNALS = [
    re.compile(r"(?:however|but|although|despite|unfortunately).{0,80}(?:fail|error|missing|incomplete|invalid)", re.I),
    re.compile(r"(?:warning|caution|note|attention).{0,40}(?:empty|missing|incomplete|unverified)", re.I),
]

_OVERCONFIDENCE_MARKERS = [
    re.compile(r"\b(?:definitely|certainly|absolutely|undoubtedly|guaranteed)\b", re.I),
    re.compile(r"100%\s*(?:confident|certain|sure)", re.I),
    re.compile(r"(?:high|very\s+high)\s+confidence", re.I),
    re.compile(r"confidently\s+(?:state|assert|claim|report)", re.I),
]


@dataclass
class FalseSuccessReport:
    """Structured false-success detection report."""

    verdict: str  # CLEAN | SUSPECT | FALSE_SUCCESS
    score: float  # 0.0 (clean) → 1.0 (definite false success)
    features: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    receipt_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "score": round(self.score, 4),
            "features": {k: round(v, 4) for k, v in self.features.items()},
            "evidence": self.evidence,
            "receipt_hash": self.receipt_hash,
            "timestamp": datetime.now(UTC).isoformat(),
        }


class FalseSuccessDetector:
    """Lightweight false-success detector for GEOX tool outputs.

    Uses TF-IDF-weighted trigram/bigram/unigram matching + heuristic
    feature extraction. Designed to run in microseconds per call —
    ~3,300× faster than LLM judge.

    Target: AUROC ≥ 0.83 on geoscience false-success corpus.
    """

    def __init__(self, corpus_documents: list[str] | None = None):
        self._tfidf: dict[str, float] = {}
        self._corpus_size = 0
        if corpus_documents:
            self._fit_tfidf(corpus_documents)

    def _tokenize_ngrams(self, text: str, n: int) -> list[str]:
        words = re.findall(r"[a-z]+", text.lower())
        if len(words) < n:
            return []
        return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]

    def _fit_tfidf(self, documents: list[str]) -> None:
        """Fit TF-IDF weights from a corpus of known false-success texts."""
        doc_count = len(documents)
        self._corpus_size = doc_count
        if doc_count == 0:
            return

        df: Counter[str] = Counter()
        for doc in documents:
            tokens = set()
            for n in (1, 2, 3):
                tokens.update(self._tokenize_ngrams(doc, n))
            df.update(tokens)

        # Smooth IDF: log((N+1)/(df+1)) + 1
        self._tfidf = {token: math.log((doc_count + 1) / (count + 1)) + 1.0 for token, count in df.items()}

    def _tfidf_score(self, text: str) -> float:
        """Compute TF-IDF score for text against false-success corpus."""
        if not self._tfidf:
            return 0.0

        tokens: list[str] = []
        for n in (1, 2, 3):
            tokens.extend(self._tokenize_ngrams(text, n))

        if not tokens:
            return 0.0

        tf: Counter[str] = Counter(tokens)
        total = sum(tf.values())
        if total == 0:
            return 0.0

        score = 0.0
        for token, count in tf.items():
            idf = self._tfidf.get(token, 0.0)
            score += (count / total) * idf

        return score / len(tokens)  # Average TF-IDF per token

    def _extract_heuristic_features(self, text: str, result: dict[str, Any] | None) -> dict[str, float]:
        """Extract heuristic features from text + structured result."""
        features: dict[str, float] = {}

        text_lower = text.lower()
        words = re.findall(r"[a-z]+", text_lower)
        word_set = set(words)

        # ── 1. False-success unigram density (stem-aware) ──────────────────
        unigram_hits = 0
        for fs_word in _FALSE_SUCCESS_UNIGRAMS:
            for word in word_set:
                # Match exact or as prefix (handles "successfully" → "success")
                if word == fs_word or word.startswith(fs_word):
                    unigram_hits += 1
                    break
        features["fs_unigram_density"] = unigram_hits / max(len(word_set), 1)

        # ── 2. Bigram hits (sliding window over tokenized words) ───────────
        bigram_set: set[tuple[str, str]] = set()
        for i in range(len(words) - 1):
            bigram_set.add((words[i], words[i + 1]))
        bg_hits = 0
        for bg in _FALSE_SUCCESS_BIGRAMS:
            for a, b in bigram_set:
                if (a.startswith(bg[0]) or bg[0].startswith(a)) and (b.startswith(bg[1]) or bg[1].startswith(b)):
                    bg_hits += 1
                    break
        features["fs_bigram_hits"] = bg_hits / max(len(_FALSE_SUCCESS_BIGRAMS), 1)

        # ── 3. Trigram hits (fuzzy sliding window) ─────────────────────────
        tg_text = " ".join(words)
        tg_hits = 0
        for tg in _FALSE_SUCCESS_TRIGRAMS:
            pattern = " ".join(tg)
            if pattern in tg_text:
                tg_hits += 1
            else:
                # Fuzzy: check if each trigram word appears in order within 3-word window
                for i in range(len(words) - 2):
                    if all(words[i + j].startswith(tg[j][:4]) or tg[j].startswith(words[i + j][:4]) for j in range(3)):
                        tg_hits += 1
                        break
        features["fs_trigram_hits"] = tg_hits / max(len(_FALSE_SUCCESS_TRIGRAMS), 1)

        # 2. Empty evidence signals
        empty_matches = sum(1 for p in _EMPTY_EVIDENCE_PATTERNS if p.search(text))
        features["empty_evidence_signals"] = min(empty_matches / 3.0, 1.0)

        # 3. Contradiction signals
        contradiction_matches = sum(1 for p in _CONTRADICTION_SIGNALS if p.search(text))
        features["contradiction_signals"] = min(contradiction_matches / 2.0, 1.0)

        # 4. Overconfidence markers
        overconf_matches = sum(1 for p in _OVERCONFIDENCE_MARKERS if p.search(text))
        features["overconfidence_markers"] = min(overconf_matches / 3.0, 1.0)

        # 5. Structural evidence check (from dict result)
        if result:
            evidence_keys = {
                "observed",
                "derived",
                "interpreted",
                "data",
                "results",
                "well_id",
                "basin_name",
                "prospect_ref",
                "claim_id",
                "volume_ref",
                "artifact_ref",
                "evidence_id",
                "horizons",
                "faults",
                "volumetrics",
                "petrophysics",
                "attributes",
                "contradictions",
                "verdict",
            }
            has_structural = bool(evidence_keys & set(str(k).lower() for k in result))
            features["structural_evidence"] = 1.0 if has_structural else 0.0

            # Check for empty arrays/objects as values
            empty_values = sum(
                1
                for v in result.values()
                if (isinstance(v, (list, dict)) and len(v) == 0) or (isinstance(v, str) and len(v.strip()) == 0) or v is None
            )
            total_values = max(len(result), 1)
            features["empty_value_ratio"] = empty_values / total_values

            # isError flag
            features["is_error_flagged"] = 1.0 if result.get("isError") or result.get("ok") is False else 0.0

        # 6. Text length (very short success messages are suspicious)
        text_len = len(text)
        features["text_length_short"] = 1.0 if text_len < 100 else (0.0 if text_len > 500 else 0.5)

        return features

    def _compute_verdict(self, score: float) -> str:
        if score >= 0.38:
            return "FALSE_SUCCESS"
        elif score >= 0.22:
            return "SUSPECT"
        return "CLEAN"

    def detect(
        self,
        text: str,
        result: dict[str, Any] | None = None,
        tool_name: str = "",
    ) -> FalseSuccessReport:
        """Detect false-success in a tool output.

        Args:
            text: The natural-language text content from the tool (the 'content' channel)
            result: The structured dict result (the 'structuredContent' channel)
            tool_name: The tool that produced this output

        Returns:
            FalseSuccessReport with verdict, score, features, evidence
        """
        # Feature extraction
        features = self._extract_heuristic_features(text, result)

        # TF-IDF score from corpus
        tfidf = self._tfidf_score(text)
        features["tfidf_score"] = tfidf

        # Composite false-success language score (ngram aggregate)
        ngram_score = (
            features.get("fs_unigram_density", 0) * 0.25
            + features.get("fs_bigram_hits", 0) * 0.35
            + features.get("fs_trigram_hits", 0) * 0.40
        )
        features["fs_ngram_composite"] = min(ngram_score * 2.0, 1.0)

        # has_no_evidence: true when no structural evidence keys present
        has_no_evidence = float(features.get("structural_evidence", 0) == 0.0)

        # MULTIPLICATIVE core: false-success = confident language × no evidence
        # If either is zero, false-success probability is low
        fs_core = features["fs_ngram_composite"] * has_no_evidence
        features["fs_core"] = fs_core

        # absence_of_evidence: stronger signal when result has NO substantive keys
        if result:
            substantive_keys = [
                k
                for k in result
                if k
                not in (
                    "ok",
                    "isError",
                    "status",
                    "error",
                    "tool",
                    "mode",
                    "message",
                    "_memory",
                    "_epistemic",
                    "_meta",
                    "_evidence_receipt",
                    "content",
                    "structuredContent",
                )
                and result.get(k) is not None
            ]
            features["absence_of_evidence"] = 1.0 if len(substantive_keys) == 0 else 0.0
        else:
            features["absence_of_evidence"] = 1.0

        # Weighted ensemble score
        weights = {
            "fs_core": 0.30,
            "absence_of_evidence": 0.25,
            "fs_ngram_composite": 0.10,
            "empty_evidence_signals": 0.10,
            "contradiction_signals": 0.08,
            "overconfidence_markers": 0.08,
            "empty_value_ratio": 0.05,
            "text_length_short": 0.04,
            "tfidf_score": 0.05,
            "is_error_flagged": -0.50,
        }

        score = sum(weights.get(k, 0.0) * v for k, v in features.items())

        # If error-flagged, score is capped low regardless
        if features.get("is_error_flagged", 0) > 0:
            score = min(score, 0.15)

        score = max(0.0, min(1.0, score))

        verdict = self._compute_verdict(score)

        # Evidence digest
        evidence = {
            "tool": tool_name,
            "text_preview": text[:200],
            "text_length": len(text),
            "has_result_dict": result is not None,
            "result_keys": list(result.keys())[:20] if result else [],
        }
        receipt_hash = hashlib.sha256(
            json.dumps({"text": text, "verdict": verdict, "score": score}, default=str, sort_keys=True).encode()
        ).hexdigest()

        if verdict != "CLEAN":
            logger.warning(
                "FALSE_SUCCESS_DETECT: %s score=%.3f verdict=%s",
                tool_name or "unknown",
                score,
                verdict,
            )

        return FalseSuccessReport(
            verdict=verdict,
            score=score,
            features=features,
            evidence=evidence,
            receipt_hash=receipt_hash,
        )


# ── Seeded False-Success Corpus ──────────────────────────────────────────────
# Documents representing known false-success patterns from the geoscience
# domain. These seed the TF-IDF weights. Expand with real corpus data (P1.5).

_FALSE_SUCCESS_SEED_CORPUS: list[str] = [
    # Pattern 1: Confident completion with no evidence
    "successfully completed the basin analysis all steps are done results are ready",
    "task finished successfully everything looks good no errors found",
    "execution completed successfully validation passed all checks passed successfully",
    "the interpretation is complete analysis finished output returned successfully",
    "data loaded successfully model trained converged computation done returning results",
    # Pattern 2: Hallucinated well data
    "well log processed successfully porosity computed successfully vsh calculated done",
    "petrophysics analysis complete all curves loaded successfully net pay computed ready",
    "seismic interpretation complete horizon picked successfully fault detected successfully",
    "prospect evaluation done volumetrics computed successfully risk assessment complete",
    # Pattern 3: Overconfident empty
    "absolutely certain the model is correct 100% confident in these results",
    "definitely the right interpretation high confidence in all picks",
    "undoubtedly correct confidently report these findings as final",
    "very high confidence the anomaly is real guaranteed to be hydrocarbons",
    # Pattern 4: Contradiction buried in success language
    "successfully processed the data however some files were missing but everything is fine",
    "analysis complete although calibration data was incomplete results are good",
    "basin model ready unfortunately some wells had missing logs but looks correct",
    # Pattern 5: Fake ready/complete
    "all steps completed ready to use done here task finished",
    "ready complete done everything is working all good",
    "results ready analysis complete successful processing done",
]
