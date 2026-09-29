"""Quality-control receipts for derived seismic artifacts.

Per the GEOX Seismic Interpretation Forge Package:
- Every transformation emits a derived artifact + lineage + QC receipt.
- QC receipts declare failure modes explicitly (per Canon #0).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

QC_SCHEMA = "geox.seismic.qc-receipt.v1"


class FailureMode(BaseModel):
    """A specific failure condition and its severity."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Machine-readable failure code")
    severity: Literal["INFO", "WARN", "CAUTION", "FAIL", "HOLD"]
    message: str = Field(..., description="Human-readable description")
    detected_at: datetime | None = None


class ValidationCheck(BaseModel):
    """Single QC check result."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Check identifier, e.g., 'edge_mask_complete'")
    passed: bool
    metric_name: str | None = Field(
        default=None, description="Numeric metric, e.g., 'rms_amplitude_ratio'"
    )
    metric_value: float | None = None
    threshold: float | None = None
    unit: str | None = None
    notes: str | None = None


class QCReceipt(BaseModel):
    """Quality-control receipt attached to a derived artifact.

    QC receipts are immutable. New checks ⇒ new QC receipt referencing the old.
    """

    model_config = ConfigDict(extra="forbid")

    schema_uri: Literal[QC_SCHEMA] = QC_SCHEMA
    artifact_ref: str = Field(..., pattern=r"^geox://[A-Za-z0-9_\-/.@]+$")
    qc_id: str = Field(..., pattern=r"^geox://qc/[A-Za-z0-9_\-/.@]+$")
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    verdict: Literal["PASS", "CAUTION", "FAIL", "HOLD", "VOID"]
    checks: list[ValidationCheck] = Field(default_factory=list)
    failures: list[FailureMode] = Field(default_factory=list)

    # Provenance
    parent_qc_ref: str | None = Field(
        default=None,
        description="Previous QC receipt, if this is an incremental update",
    )
    code_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")

    @field_validator("checks")
    @classmethod
    def _check_names_unique(cls, v: list[ValidationCheck]) -> list[ValidationCheck]:
        names = [c.name for c in v]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate check names")
        return v

    @field_validator("failures")
    @classmethod
    def _failure_codes_unique(
        cls, v: list[FailureMode]
    ) -> list[FailureMode]:
        codes = [f.code for f in v]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate failure codes")
        return v

    def has_hold_failures(self) -> bool:
        return any(f.severity in ("HOLD", "FAIL") for f in self.failures)
