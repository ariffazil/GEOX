"""
translation.py — Semantic Translation Layer
============================================
The Layang-Layang Lesson encoded. When the same label (e.g., IRU/ROU/BU)
appears in two interpretation schemes, never map across schemes without an
explicit translation entry.

Every token has: {PCSB_meaning, TTE_meaning, Published_meaning, ...}.
Translation binds them without forcing identity.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TranslationEntry(BaseModel):
    """One token, multiple schemes. Binds without forcing identity."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., description="The label (e.g. 'IRU', 'ROU', 'BU')")
    schemes: dict[str, str] = Field(
        default_factory=dict,
        description='{"PCSB": "Intra-Rift Unconformity", "TTE": "TTE_IRU", "Published": "IRU_Ali2023"}',
    )
    notes: str = Field(default="", description="Context on differences between schemes")
    canonical_meaning: str = Field(default="", description="The best-known geological meaning, if consensus exists")


class TranslationLayer(BaseModel):
    """Semantic mapping between interpretation schemes.

    Rule: never map across schemes without an explicit entry here.
    If a token is not in this layer, it cannot be translated.
    """

    model_config = ConfigDict(extra="forbid")

    entries: dict[str, TranslationEntry] = Field(default_factory=dict, description="Token → TranslationEntry")
    scheme_names: list[str] = Field(default_factory=list, description="Known scheme names (e.g. PCSB, TTE, Published)")

    def add_entry(self, entry: TranslationEntry) -> str:
        """Register a token. Update scheme_names if new schemes appear."""
        self.entries[entry.token] = entry
        for scheme in entry.schemes:
            if scheme not in self.scheme_names:
                self.scheme_names.append(scheme)
        return entry.token

    def translate(self, token: str, from_scheme: str, to_scheme: str) -> str | None:
        """Translate a token from one scheme to another. Returns None if no mapping exists."""
        entry = self.entries.get(token)
        if entry is None:
            return None
        return entry.schemes.get(to_scheme)

    def lookup(self, token: str) -> TranslationEntry | None:
        """Get all known schemes for a token."""
        return self.entries.get(token)

    def to_summary(self) -> dict[str, Any]:
        return {
            "num_entries": len(self.entries),
            "schemes": self.scheme_names,
            "tokens": list(self.entries.keys()),
        }


# ── Convenience: create the canonical Layang-Layang example ──────────────────


def layang_layang_example() -> TranslationLayer:
    """The Layang-Layang Lesson as a TranslationLayer.

    IRU_PCSB and IRU_TTE are different STS objects, both valid within their scheme.
    Translation binds without forcing identity.
    """
    tl = TranslationLayer()
    tl.add_entry(
        TranslationEntry(
            token="IRU",
            schemes={
                "PCSB": "Intra-Rift Unconformity (PCSB scheme)",
                "TTE": "TTE_IRU (TTE scheme)",
                "Published": "IRU_Ali2023",
            },
            notes="PCSB and TTE schemes differ in age calibration. Both valid.",
            canonical_meaning="Late Eocene–Early Oligocene unconformity in Sabah Basin",
        )
    )
    tl.add_entry(
        TranslationEntry(
            token="ROU",
            schemes={
                "PCSB": "Rift-Onset Unconformity (PCSB scheme)",
                "TTE": "TTE_ROU (TTE scheme)",
                "Published": "ROU_Prabal2024",
            },
            notes="Syn-rift initiation unconformity. Diachroneity class: strongly_diachronous.",
        )
    )
    tl.add_entry(
        TranslationEntry(
            token="BU",
            schemes={
                "PCSB": "Breakup Unconformity (PCSB scheme)",
                "TTE": "TTE_BU (TTE scheme)",
                "Published": "BU_Tan2022",
            },
            notes="Drift-onset breakup surface. Strongly diachronous across margin.",
        )
    )
    return tl
