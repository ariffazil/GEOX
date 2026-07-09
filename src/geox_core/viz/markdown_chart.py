"""Markdown chart fallback — when forge_chart session/HTTP is unavailable.

Produces structured tables + ASCII spark bars for prospect risk/volumetrics.
ΔS ≤ 0: usable analysis without waiting on transport ownership.
"""

from __future__ import annotations

from typing import Any


def markdown_bar(label: str, value: float, max_value: float = 1.0, width: int = 20) -> str:
    v = max(0.0, float(value))
    m = max(abs(max_value), 1e-9)
    n = int(round(min(1.0, v / m) * width))
    return f"{label:16s} |{'█' * n}{'░' * (width - n)}| {v:.3g}"


def risk_spider_markdown(dimensions: dict[str, float], scale: float = 5.0) -> str:
    """dimensions: name → score (1–5 or 0–1)."""
    lines = ["### Risk spider (markdown fallback)", ""]
    lines.append("```")
    for k, v in dimensions.items():
        lines.append(markdown_bar(k, float(v), max_value=scale))
    lines.append("```")
    return "\n".join(lines)


def tornado_markdown(cases: list[dict[str, Any]], value_key: str = "value", label_key: str = "case") -> str:
    """cases: [{case: P10, value: ...}, ...]"""
    lines = ["### Tornado / range (markdown fallback)", "", "| Case | Value |", "|------|-------|"]
    for c in cases:
        lines.append(f"| {c.get(label_key, '?')} | {c.get(value_key, '?')} |")
    return "\n".join(lines)


def decision_panel_markdown(obs: list[str], der: list[str], inter: list[str], spec: list[str]) -> str:
    lines = [
        "### Decision panel — OBS / DER / INT / SPEC",
        "",
        "| Class | Items |",
        "|-------|-------|",
        f"| OBS | {'; '.join(obs) if obs else '—'} |",
        f"| DER | {'; '.join(der) if der else '—'} |",
        f"| INT | {'; '.join(inter) if inter else '—'} |",
        f"| SPEC | {'; '.join(spec) if spec else '—'} |",
    ]
    return "\n".join(lines)
