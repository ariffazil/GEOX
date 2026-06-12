#!/usr/bin/env python3
"""
GEOX Low-Entropy Repo Migration Script
═══════════════════════════════════════════════════════════════════════════════
Phase 1: Establish canonical spine
Phase 2: Migrate core + MCP surface
Phase 3: Create resources layer
Phase 4: Archive old surfaces

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("ARIFOS_HOME", "/root") + "/geox")
TARGET_SRC = REPO_ROOT / "src"
TARGET_RESOURCES = REPO_ROOT / "resources"
TARGET_DOCS = REPO_ROOT / "docs"
TARGET_ARCHIVE = REPO_ROOT / "archive"
TARGET_TESTS = REPO_ROOT / "tests"
TARGET_SCRIPTS = REPO_ROOT / "scripts"
TARGET_APPS = REPO_ROOT / "apps"

# ── Import rewrite rules ────────────────────────────────────────────────────
# Order matters: longer prefixes first to avoid partial matches
IMPORT_REWRITES = [
    # MCP tool layer (contracts → geox_mcp)
    ("from contracts.canonical_registry ", "from geox_mcp.registry "),
    ("import contracts.canonical_registry", "import geox_mcp.registry"),
    ("from contracts.tools.unified_13 ", "from geox_mcp.tools.unified_13 "),
    ("from contracts.tools.well_correlation ", "from geox_mcp.tools.well_correlation "),
    ("from contracts.tools.canonical._helpers ", "from geox_mcp.tools._helpers "),
    ("from contracts.tools.canonical.kernel.", "from geox_mcp.tools.kernel."),
    ("from contracts.tools.canonical.ingest ", "from geox_mcp.tools.data "),
    ("from contracts.tools.canonical.qc ", "from geox_mcp.tools.qc "),
    ("from contracts.tools.canonical.subsurface ", "from geox_mcp.tools.petrophysics "),
    ("from contracts.tools.canonical.seismic ", "from geox_mcp.tools.seismic "),
    ("from contracts.tools.canonical.section ", "from geox_mcp.tools.section "),
    ("from contracts.tools.canonical.map_context ", "from geox_mcp.tools.map_context "),
    ("from contracts.tools.canonical.time4d ", "from geox_mcp.tools.time4d "),
    ("from contracts.tools.canonical.prospect ", "from geox_mcp.tools.prospect "),
    ("from contracts.tools.canonical.evidence ", "from geox_mcp.tools.evidence "),
    ("from contracts.tools.canonical.registry ", "from geox_mcp.tools.registry "),
    ("from contracts.tools.canonical.dst ", "from geox_mcp.tools.dst "),
    ("from contracts.mcp.", "from geox_mcp.contracts."),
    ("import contracts.mcp.", "import geox_mcp.contracts."),
    # Core computation layer (geox → geox_core)
    ("from geox.core.", "from geox_core.core."),
    ("from geox.ingest.", "from geox_core.ingest."),
    ("from geox.services.", "from geox_core.services."),
    ("from geox.artifacts.", "from geox_core.artifacts."),
    ("from geox.renderers.", "from geox_core.renderers."),
    ("from geox.plot_specs.", "from geox_core.plot_specs."),
    ("from geox.well.tools.", "from geox_core.well.tools."),
    ("from geox.well.stratigraphy.", "from geox_core.well.stratigraphy."),
    ("from geox.well.mcp_tools ", "from geox_mcp.tools.well "),
    ("from geox.well.mcp_stratigraphy ", "from geox_mcp.tools.stratigraphy "),
    ("from geox.skills.", "from geox_core.skills."),
    ("from geox.telemetry.", "from geox_core.telemetry."),
    ("from geox.wealth.", "from geox_core.wealth."),
    ("from geox.envelopes.", "from geox_core.envelopes."),
    ("from geox.schemas.", "from geox_core.schemas."),
    ("from geox.shared.", "from geox_core.shared."),
    ("from geox.adapters.", "from geox_core.adapters."),
    ("from geox.engines.", "from geox_core.engines."),
    ("from geox.jobs.", "from geox_core.jobs."),
    ("from geox.registry.", "from geox_core.registry."),
    ("from geox.geox_mcp.", "from geox_mcp."),
    ("import geox.geox_mcp.", "import geox_mcp."),
    # Enums/schemas/compatibility (contracts → geox_core)
    ("from contracts.enums.", "from geox_core.enums."),
    ("from contracts.schemas.", "from geox_core.schemas."),
    ("from contracts.governance.", "from geox_core.governance."),
    ("from contracts.parity.", "from geox_core.parity."),
    ("from compatibility.", "from geox_core.compatibility."),
    # Server self-reference (when server.py moves)
    ("from server import GEOX_VERSION", "from geox_mcp.server import GEOX_VERSION"),
]


def rewrite_imports(content: str) -> str:
    """Rewrite import statements according to IMPORT_REWRITES."""
    for old, new in IMPORT_REWRITES:
        content = content.replace(old, new)
    return content


def copy_tree_with_rewrite(src: Path, dst: Path, rename_map: dict[str, str] | None = None) -> None:
    """Copy Python files from src to dst, rewriting imports."""
    rename_map = rename_map or {}
    for root, dirs, files in os.walk(src):
        # Skip pycache and node_modules
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules", ".git")]

        rel_root = Path(root).relative_to(src)
        for file in files:
            if file.endswith(".pyc"):
                continue
            src_file = Path(root) / file
            # Apply rename mapping for filenames
            dst_file_name = rename_map.get(file, file)
            dst_file = dst / rel_root / dst_file_name
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            if file.endswith(".py"):
                content = src_file.read_text(encoding="utf-8")
                content = rewrite_imports(content)
                dst_file.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(src_file, dst_file)


def create_init_py(path: Path) -> None:
    """Create minimal __init__.py if missing."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""GEOX package. DITEMPA BUKAN DIBERI."""\n', encoding="utf-8")


def phase_0_create_directories() -> None:
    """Create target directory spine."""
    print("[Phase 0] Creating directory spine...")

    dirs = [
        TARGET_SRC / "geox_core" / "core",
        TARGET_SRC / "geox_core" / "ingest",
        TARGET_SRC / "geox_core" / "services",
        TARGET_SRC / "geox_core" / "artifacts",
        TARGET_SRC / "geox_core" / "renderers",
        TARGET_SRC / "geox_core" / "plot_specs",
        TARGET_SRC / "geox_core" / "well" / "tools",
        TARGET_SRC / "geox_core" / "well" / "stratigraphy",
        TARGET_SRC / "geox_core" / "skills",
        TARGET_SRC / "geox_core" / "telemetry",
        TARGET_SRC / "geox_core" / "wealth",
        TARGET_SRC / "geox_core" / "envelopes",
        TARGET_SRC / "geox_core" / "schemas",
        TARGET_SRC / "geox_core" / "shared",
        TARGET_SRC / "geox_core" / "adapters",
        TARGET_SRC / "geox_core" / "engines",
        TARGET_SRC / "geox_core" / "jobs",
        TARGET_SRC / "geox_core" / "registry",
        TARGET_SRC / "geox_core" / "enums",
        TARGET_SRC / "geox_core" / "governance",
        TARGET_SRC / "geox_core" / "parity",
        TARGET_SRC / "geox_core" / "compatibility",
        TARGET_SRC / "geox_core" / "laws",
        TARGET_SRC / "geox_core" / "canonical",
        TARGET_SRC / "geox_mcp" / "tools" / "kernel",
        TARGET_SRC / "geox_mcp" / "contracts",
        TARGET_RESOURCES / "capabilities",
        TARGET_RESOURCES / "toolcards",
        TARGET_RESOURCES / "playbooks",
        TARGET_RESOURCES / "prompts",
        TARGET_RESOURCES / "ontology",
        TARGET_RESOURCES / "schemas",
        TARGET_RESOURCES / "examples",
        TARGET_DOCS,
        TARGET_ARCHIVE,
        TARGET_TESTS / "unit",
        TARGET_TESTS / "integration",
        TARGET_TESTS / "golden",
        TARGET_TESTS / "fixtures",
        TARGET_SCRIPTS,
        TARGET_APPS,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("  ✓ Directories created")


def phase_1_migrate_core() -> None:
    """Migrate core computation to src/geox_core/."""
    print("[Phase 1] Migrating core computation...")

    mappings = [
        (REPO_ROOT / "geox" / "core", TARGET_SRC / "geox_core" / "core"),
        (REPO_ROOT / "geox" / "ingest", TARGET_SRC / "geox_core" / "ingest"),
        (REPO_ROOT / "geox" / "services", TARGET_SRC / "geox_core" / "services"),
        (REPO_ROOT / "geox" / "artifacts", TARGET_SRC / "geox_core" / "artifacts"),
        (REPO_ROOT / "geox" / "renderers", TARGET_SRC / "geox_core" / "renderers"),
        (REPO_ROOT / "geox" / "plot_specs", TARGET_SRC / "geox_core" / "plot_specs"),
        (REPO_ROOT / "geox" / "well" / "tools", TARGET_SRC / "geox_core" / "well" / "tools"),
        (REPO_ROOT / "geox" / "well" / "stratigraphy", TARGET_SRC / "geox_core" / "well" / "stratigraphy"),
        (REPO_ROOT / "geox" / "skills", TARGET_SRC / "geox_core" / "skills"),
        (REPO_ROOT / "geox" / "telemetry", TARGET_SRC / "geox_core" / "telemetry"),
        (REPO_ROOT / "geox" / "wealth", TARGET_SRC / "geox_core" / "wealth"),
        (REPO_ROOT / "geox" / "envelopes", TARGET_SRC / "geox_core" / "envelopes"),
        (REPO_ROOT / "geox" / "schemas", TARGET_SRC / "geox_core" / "schemas"),
        (REPO_ROOT / "geox" / "shared", TARGET_SRC / "geox_core" / "shared"),
        (REPO_ROOT / "geox" / "adapters", TARGET_SRC / "geox_core" / "adapters"),
        (REPO_ROOT / "geox" / "engines", TARGET_SRC / "geox_core" / "engines"),
        (REPO_ROOT / "geox" / "jobs", TARGET_SRC / "geox_core" / "jobs"),
        (REPO_ROOT / "geox" / "registry", TARGET_SRC / "geox_core" / "registry"),
        (REPO_ROOT / "geox" / "laws", TARGET_SRC / "geox_core" / "laws"),
        (REPO_ROOT / "geox" / "canonical", TARGET_SRC / "geox_core" / "canonical"),
        (REPO_ROOT / "contracts" / "enums", TARGET_SRC / "geox_core" / "enums"),
        (REPO_ROOT / "contracts" / "schemas", TARGET_SRC / "geox_core" / "schemas"),
        (REPO_ROOT / "contracts" / "governance", TARGET_SRC / "geox_core" / "governance"),
        (REPO_ROOT / "contracts" / "parity", TARGET_SRC / "geox_core" / "parity"),
        (REPO_ROOT / "compatibility", TARGET_SRC / "geox_core" / "compatibility"),
    ]

    for src, dst in mappings:
        if src.exists():
            copy_tree_with_rewrite(src, dst)
            print(f"  ✓ {src.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
        else:
            print(f"  ⚠ Missing: {src}")

    # Copy geox/well/__init__.py and schemas
    if (REPO_ROOT / "geox" / "well" / "__init__.py").exists():
        shutil.copy2(REPO_ROOT / "geox" / "well" / "__init__.py", TARGET_SRC / "geox_core" / "well" / "__init__.py")
    well_schemas = REPO_ROOT / "geox" / "well" / "schemas"
    if well_schemas.exists():
        copy_tree_with_rewrite(well_schemas, TARGET_SRC / "geox_core" / "well" / "schemas")

    # Also copy top-level geox __init__.py
    if (REPO_ROOT / "geox" / "__init__.py").exists():
        shutil.copy2(REPO_ROOT / "geox" / "__init__.py", TARGET_SRC / "geox_core" / "__init__.py")


def phase_2_migrate_mcp() -> None:
    """Migrate MCP surface to src/geox_mcp/."""
    print("[Phase 2] Migrating MCP surface...")

    # Server
    server_src = REPO_ROOT / "server.py"
    server_dst = TARGET_SRC / "geox_mcp" / "server.py"
    if server_src.exists():
        content = server_src.read_text(encoding="utf-8")
        content = rewrite_imports(content)
        server_dst.write_text(content, encoding="utf-8")
        print(f"  ✓ server.py → src/geox_mcp/server.py")

    # Registry
    registry_src = REPO_ROOT / "contracts" / "canonical_registry.py"
    registry_dst = TARGET_SRC / "geox_mcp" / "registry.py"
    if registry_src.exists():
        content = registry_src.read_text(encoding="utf-8")
        content = rewrite_imports(content)
        registry_dst.write_text(content, encoding="utf-8")
        print(f"  ✓ contracts/canonical_registry.py → src/geox_mcp/registry.py")

    # Tool mappings
    tool_mappings = {
        "unified_13.py": "unified_13.py",
        "well_correlation.py": "well_correlation.py",
        "_helpers.py": "_helpers.py",
    }
    tools_src = REPO_ROOT / "contracts" / "tools"
    tools_dst = TARGET_SRC / "geox_mcp" / "tools"

    for fname, dst_name in tool_mappings.items():
        src_file = tools_src / fname
        if src_file.exists():
            content = src_file.read_text(encoding="utf-8")
            content = rewrite_imports(content)
            (tools_dst / dst_name).write_text(content, encoding="utf-8")
            print(f"  ✓ contracts/tools/{fname} → src/geox_mcp/tools/{dst_name}")

    # Canonical tools (with renames)
    canonical_tools = {
        "ingest.py": "data.py",
        "qc.py": "qc.py",
        "subsurface.py": "petrophysics.py",
        "seismic.py": "seismic.py",
        "section.py": "section.py",
        "map_context.py": "map_context.py",
        "time4d.py": "time4d.py",
        "prospect.py": "prospect.py",
        "evidence.py": "evidence.py",
        "registry.py": "registry.py",
        "dst.py": "dst.py",
    }
    canonical_src = tools_src / "canonical"

    for src_name, dst_name in canonical_tools.items():
        src_file = canonical_src / src_name
        if src_file.exists():
            content = src_file.read_text(encoding="utf-8")
            content = rewrite_imports(content)
            (tools_dst / dst_name).write_text(content, encoding="utf-8")
            print(f"  ✓ contracts/tools/canonical/{src_name} → src/geox_mcp/tools/{dst_name}")

    # Kernel helpers
    kernel_src = canonical_src / "kernel"
    kernel_dst = tools_dst / "kernel"
    if kernel_src.exists():
        copy_tree_with_rewrite(kernel_src, kernel_dst)
        print(f"  ✓ contracts/tools/canonical/kernel → src/geox_mcp/tools/kernel")

    # MCP contracts
    mcp_contracts_src = REPO_ROOT / "contracts" / "mcp"
    mcp_contracts_dst = TARGET_SRC / "geox_mcp" / "contracts"
    if mcp_contracts_src.exists():
        copy_tree_with_rewrite(mcp_contracts_src, mcp_contracts_dst)
        print(f"  ✓ contracts/mcp → src/geox_mcp/contracts")

    # Well MCP wrappers
    well_mcp_tools = REPO_ROOT / "geox" / "well" / "mcp_tools.py"
    well_mcp_strat = REPO_ROOT / "geox" / "well" / "mcp_stratigraphy.py"

    if well_mcp_tools.exists():
        content = well_mcp_tools.read_text(encoding="utf-8")
        content = rewrite_imports(content)
        # Fix relative imports that break when moved
        content = content.replace("from .config import", "from geox_core.well.stratigraphy.config import")
        content = content.replace("from .pipeline import", "from geox_core.well.stratigraphy.pipeline import")
        content = content.replace("from .seqstrat import", "from geox_core.well.tools.seqstrat import")
        (tools_dst / "well.py").write_text(content, encoding="utf-8")
        print(f"  ✓ geox/well/mcp_tools.py → src/geox_mcp/tools/well.py")

    if well_mcp_strat.exists():
        content = well_mcp_strat.read_text(encoding="utf-8")
        content = rewrite_imports(content)
        content = content.replace("from .config import", "from geox_core.well.stratigraphy.config import")
        content = content.replace("from .pipeline import", "from geox_core.well.stratigraphy.pipeline import")
        (tools_dst / "stratigraphy.py").write_text(content, encoding="utf-8")
        print(f"  ✓ geox/well/mcp_stratigraphy.py → src/geox_mcp/tools/stratigraphy.py")


def phase_3_create_resources() -> None:
    """Create the resources/ layer from scratch."""
    print("[Phase 3] Creating resources layer...")

    # capabilities.json
    capabilities = {
        "domain": "earth_intelligence",
        "version": "2026.05.17",
        "seal": "DITEMPA BUKAN DIBERI",
        "tools": [
            {
                "name": "geox_data_ingest_bundle",
                "domain": "data_ingest",
                "required_inputs": ["source_uri OR content_base64"],
                "optional_inputs": ["well_id", "source_type", "standardize_curves", "normalize_units"],
                "outputs": ["artifact_ref", "sha256", "curve_inventory", "depth_range_m", "claim_state"],
                "claim_limits": ["FILE_IMPORT means mechanical load, not geological validation."],
                "next_best_tools": ["geox_data_qc_bundle", "geox_las_curve_inventory"],
            },
            {
                "name": "geox_data_qc_bundle",
                "domain": "data_qc",
                "required_inputs": ["artifact_ref", "artifact_type"],
                "optional_inputs": ["qc_mode"],
                "outputs": ["qc_overall", "qc_passed", "claim_state", "flags", "limitations"],
                "claim_limits": ["QC_VERIFIED means mechanical checks passed, not geological truth."],
                "next_best_tools": ["geox_subsurface_generate_candidates", "geox_well_analyze_sequence"],
            },
            {
                "name": "geox_well_analyze_sequence",
                "domain": "well_stratigraphy",
                "required_inputs": ["source", "zone_top", "zone_base"],
                "optional_inputs": ["depo_env_code", "bin_size_m", "min_package_thickness_m", "p50_shift_api", "gr_cutoff_api"],
                "outputs": ["bins", "packages", "systems_tracts", "surfaces", "claim_state"],
                "claim_limits": [
                    "Single-well sequence surfaces are candidates only.",
                    "MFS requires correlation or independent strat evidence.",
                    "GR-only motif cannot prove lithology.",
                ],
                "next_best_tools": ["geox_section_interpret_correlation", "geox_evidence_summarize_cross"],
            },
            {
                "name": "geox_subsurface_generate_candidates",
                "domain": "petrophysics",
                "required_inputs": ["target_class", "evidence_refs"],
                "optional_inputs": ["zone_top_m", "zone_base_m", "realizations", "archie params"],
                "outputs": ["candidates", "residuals", "claim_state"],
                "claim_limits": ["Candidates are hypotheses until verified by independent evidence."],
                "next_best_tools": ["geox_subsurface_verify_integrity", "geox_evidence_summarize_cross"],
            },
            {
                "name": "geox_prospect_evaluate",
                "domain": "prospect",
                "required_inputs": ["prospect_ref"],
                "optional_inputs": ["mode", "evidence_refs"],
                "outputs": ["evaluation", "pos", "evoi", "claim_state"],
                "claim_limits": ["Screen mode is heuristic only. Appraise/develop require QC_VERIFIED evidence."],
                "next_best_tools": ["geox_prospect_judge_preview"],
            },
            {
                "name": "geox_evidence_summarize_cross",
                "domain": "cross_dimension",
                "required_inputs": ["evidence_refs"],
                "optional_inputs": ["export_format", "output_path"],
                "outputs": ["causal_graph", "summary", "claim_state"],
                "claim_limits": ["Cross-domain synthesis is only as strong as the weakest evidence ref."],
                "next_best_tools": ["geox_prospect_judge_preview"],
            },
        ],
    }

    import json

    cap_file = TARGET_RESOURCES / "capabilities" / "geox_capabilities.json"
    cap_file.write_text(json.dumps(capabilities, indent=2), encoding="utf-8")
    print(f"  ✓ {cap_file.relative_to(REPO_ROOT)}")

    # Prompts
    prompts = {
        "geox_agent_system.md": """# GEOX Agent System Prompt

You are an Earth-intelligence reasoning instrument serving the GEOX constitutional federation.

## Core Discipline
1. **Evidence before interpretation.** Prefer QC_VERIFIED artifact_refs over raw files.
2. **Claim layers are separate:**
   - OBSERVED: what the data literally says
   - DERIVED: what the math computes
   - INTERPRETED: what the geology implies
   - RECOMMENDED: what action to take
3. **Never mix these layers.** Never convert a candidate into proven geological truth without correlation evidence.
4. **Use GEOX deterministic tools for computation.** Use the language model only for synthesis, critique, and explanation.
5. **If evidence is missing, return HOLD with missing_inputs_schema.**
6. **Governance over intelligence:** if epistemic integrity < threshold → 888_HOLD.

## Tool Selection Rules
- Ingest before QC. QC before interpretation. Interpretation before judgment.
- Single-well sequence stratigraphy is candidate-only.
- Petrophysics without calibration is hypothesis-only.
- Pressure without calibration is void for operational decisions.
""",
        "claim_discipline.md": """# GEOX Claim Discipline

Every statement must be tagged:
- **[OBSERVED]** — Direct measurement or data point
- **[DERIVED]** — Mathematical or computational result
- **[INTERPRETED]** — Geological inference from evidence
- **[RECOMMENDED]** — Action suggestion based on interpretation

## Forbidden Patterns
- "The reservoir is proven high-quality" (without DST/core)
- "The MFS is confirmed" (without regional correlation)
- "Overpressure is certain" (without calibrated model)
- "PoS = X%" (without showing the risk tree)

## When to HOLD
- Missing canonical curves (GR, RT, RHOB, NPHI)
- QC flags present
- No independent evidence for interpreted surface
- Contradictory evidence (e.g., GR says shale, VCLAY says clean)
""",
        "tool_selection.md": """# GEOX Tool Selection Guide

## Well Sequence Stratigraphy Workflow
1. `geox_data_ingest_bundle` → get artifact_ref
2. `geox_data_qc_bundle` → verify artifact_ref
3. `geox_las_curve_inventory` → check available curves
4. `geox_well_analyze_sequence` → run L1-L3 pipeline
5. `geox_evidence_summarize_cross` → synthesize with other wells

## Prospect Evaluation Workflow
1. `geox_data_ingest_bundle` → load all wells/seismic
2. `geox_data_qc_bundle` → verify evidence
3. `geox_subsurface_generate_candidates` → build petrophysical model
4. `geox_map_context_scene` → get spatial context
5. `geox_time4d_analyze_system` → check charge timing
6. `geox_prospect_evaluate` → evaluate
7. `geox_prospect_judge_preview` → reversible preview
8. Human review → `geox_prospect_judge_seal` (irreversible)

## Failure Recovery
- `ARTIFACT_NOT_FOUND` → re-ingest with source_uri or content_base64
- `QC_ENGINE_FAILED` → check LAS path exists; try shallow QC
- `NO_VALID_EVIDENCE` → list missing_inputs_schema and ask for data
- `GR_PHYSICS_GUARD_FAILED` → run QC; check for bad GR values
""",
    }

    for name, content in prompts.items():
        p = TARGET_RESOURCES / "prompts" / name
        p.write_text(content, encoding="utf-8")
        print(f"  ✓ {p.relative_to(REPO_ROOT)}")

    # Ontology
    ontology = {
        "curve_aliases.yaml": """curve_aliases:
  gamma_ray:
    canonical: GR
    aliases: [GR, GR_P, GAMMA, CGR, SGR, GRC, GAPI, GAMMA_RAY]
    unit: gAPI
  resistivity_deep:
    canonical: RT
    aliases: [RT, RESD, RES_D, RDEP, ILD, RES_DEEP]
    unit: ohm.m
  density:
    canonical: RHOB
    aliases: [RHOB, DENS, DEN, RHOB]
    unit: g/cm3
  neutron_porosity:
    canonical: NPHI
    aliases: [NPHI, NEU, NPOR, PHIN]
    unit: v/v
  sonic:
    canonical: DT
    aliases: [DT, DTC, SONIC, AC, DT4]
    unit: us/ft
  caliper:
    canonical: CAL
    aliases: [CAL, CALI, CALX]
    unit: in
  spontaneous_potential:
    canonical: SP
    aliases: [SP, SPONT, SPL]
    unit: mV
""",
        "depositional_env_codes.yaml": """depositional_env_codes:
  FLUVIAL: [LST, TST, HST]
  TIDAL: [LST, TST, HST]
  SHOREFACE: [LST, TST, HST, FSST]
  SHELF: [LST, TST, HST, FSST]
  DEEPWATER: [LST, TST, HST]
  CARBONATE: [LST, TST, HST]
""",
    }

    for name, content in ontology.items():
        p = TARGET_RESOURCES / "ontology" / name
        p.write_text(content, encoding="utf-8")
        print(f"  ✓ {p.relative_to(REPO_ROOT)}")

    # Playbooks
    playbooks = {
        "well_sequence_stratigraphy.yaml": """name: well_sequence_stratigraphy
domain: subsurface_stratigraphy
goal: Interpret GR motif and candidate sequence surfaces from a well.
required_tools:
  - geox_data_ingest_bundle
  - geox_data_qc_bundle
  - geox_well_analyze_sequence
required_evidence:
  - LAS or CSV
  - GR curve
  - depth_basis
recommended_evidence:
  - VCLAY
  - RHOB
  - NPHI
  - RT
  - tops
  - core
  - biostrat
  - nearby_wells for correlation
claim_limits:
  - Single-well MFS is candidate only.
  - GR-only motif cannot prove lithology.
  - Sequence boundaries require independent evidence.
""",
        "prospect_evaluation.yaml": """name: prospect_evaluation
domain: prospect
goal: Screen, appraise, or develop a petroleum prospect.
required_tools:
  - geox_data_ingest_bundle
  - geox_data_qc_bundle
  - geox_subsurface_generate_candidates
  - geox_map_context_scene
  - geox_prospect_evaluate
required_evidence:
  - well_logs
  - seismic
  - structural_map
recommended_evidence:
  - dst_results
  - pvt_data
  - charge_model
  - regional_correlation
claim_limits:
  - Screen mode is heuristic only.
  - Appraise requires QC_VERIFIED evidence.
  - Develop requires full evidence + prior appraisal.
""",
    }

    for name, content in playbooks.items():
        p = TARGET_RESOURCES / "playbooks" / name
        p.write_text(content, encoding="utf-8")
        print(f"  ✓ {p.relative_to(REPO_ROOT)}")

    # Examples
    example_project = """project: DANUM1_SeqStrat
bin_size_m: 10.0
min_package_thickness_m: 20.0
p50_shift_thresh_gapi: 15.0
gr_cut_api: 75.0
gr_min_api: 0.0
gr_max_api: 150.0
well_order:
  - DANUM-1
wells:
  - name: DANUM-1
    path: /data/DANUM-1.las
    format: LAS
intervals:
  DANUM-1:
    - zone: UBT
      top: 1200
      base: 1800
      depo_env: SHOREFACE
"""
    (TARGET_RESOURCES / "examples" / "danum1_project.yaml").write_text(example_project, encoding="utf-8")
    print(f"  ✓ resources/examples/danum1_project.yaml")

    # Schema exports
    schemas_to_export = [
        (REPO_ROOT / "schemas" / "dimensions.json", TARGET_RESOURCES / "schemas" / "dimensions.json"),
        (REPO_ROOT / "schemas" / "las_manifest.json", TARGET_RESOURCES / "schemas" / "las_manifest.json"),
        (REPO_ROOT / "schemas" / "well_desk_event_schema.json", TARGET_RESOURCES / "schemas" / "well_desk_event_schema.json"),
    ]
    for src, dst in schemas_to_export:
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✓ {dst.relative_to(REPO_ROOT)}")


def phase_4_move_docs() -> None:
    """Move root-level docs to docs/."""
    print("[Phase 4] Moving root docs...")

    doc_files = [
        "888_HOLD_RELEASE_SUMMARY.md",
        "AAA_GRADE_SEAL.md",
        "AGENTS.md",
        "ARIF.md",
        "CHANGELOG.md",
        "CLAUDE.md",
        "CLEANUP_SUMMARY.md",
        "CONSTITUTIONAL_PHYSICS_STACK.md",
        "CONTRACTS_ANALYSIS.md",
        "DEPLOYMENT.md",
        "DEPLOYMENT_SEAL.md",
        "DEPLOYMENT_STATUS.md",
        "EIC_SEAL.md",
        "EXTERNAL_INTEGRATION_GUIDE.md",
        "FEDERATION_LOOP_GEOX_SPACE.md",
        "FORGE_HARDENED_VISION.md",
        "GEOX_CONSTITUTIONAL_PHYSICS_STACK.md",
        "GEOX_DESIGN_FORGE_SEAL.md",
        "GEOX_F1_F13_MAPPING.md",
        "GEOX_GO_NOGO_RULES.md",
        "GEOX_INTERPRODUCT_RISK_RULES.md",
        "GEOX_MAP_RELEASE_NOTE.md",
        "GEOX_ORTHOGONAL_TOOL_SPEC.md",
        "GEOX_PRODUCT_VERSIONING.md",
        "GEOX_SEAL_CHECKLIST.md",
        "GEOX_SIMPLIFIED_MANIFEST.md",
        "GEOX_STATUS_AND_FOCUS.md",
        "GEOX_TOOL_TAXONOMY.md",
        "GEOX_VISION_DEV_CHARTER.md",
        "GOVERNANCE.md",
        "MCP_APPS_AUDIT.md",
        "PHYSICS_ADAPTER_SPEC.md",
        "RELEASE_CHECKLIST.md",
        "RELEASE_NOTES_v2026.05.01.md",
        "REPO_ROUTING_CONSTITUTION.md",
        "ROADMAP.md",
        "SECURITY.md",
        "SITE_DEPLOYMENT_PLAN.md",
        "SITE_GEOK_ARIF_FAZIL_COM.md",
        "SITE_MAP_VISUAL.md",
        "TOAC_AC_RISK_SPEC.md",
        "TOAC_CANON.md",
        "TODO.md",
        "TOOL_CONSOLIDATION_MAP.md",
        "VISION_INTELLIGENCE_IMPLEMENTATION.md",
        "WEBSITE_AUDIT.md",
        "WIKI_UPDATE_SUMMARY.md",
        "architecture.md",
        "README_WELL_DESK.md",
    ]

    for fname in doc_files:
        src = REPO_ROOT / fname
        if src.exists():
            dst = TARGET_DOCS / fname
            shutil.move(str(src), str(dst))
            print(f"  ✓ {fname} → docs/")


def phase_5_archive_surfaces() -> None:
    """Move old competing surfaces to archive/."""
    print("[Phase 5] Archiving old surfaces...")

    surfaces = [
        "arifos",
        "control_plane",
        "execution_plane",
        "domain",
        "governance",
        "internal",
        "knowledge",
        "mcp",
        "sdk",
        "services",
        "traefik",
        "WELL",
        "geox_mcp",
        "src/tools",
        "tools/causal_scene",
        "scratch",
        "stash",
        "legacy",
        "patches",
        "ref",
        "output",
        "telemetry",
        "wiki",
        "c:",
        "geox_sovereign_backend.egg-info",
        "geox.egg-info",
        "geox-site",
        "geox-site-p0",
        "site",
        ".archive",
        "archive/deprecated",
        "archive/legacy_servers",
    ]

    for surf in surfaces:
        src = REPO_ROOT / surf
        if src.exists():
            dst = TARGET_ARCHIVE / Path(surf).name
            # If already in archive/, just reorganize
            if str(src).startswith(str(TARGET_ARCHIVE)):
                continue
            # Handle conflicts
            if dst.exists():
                dst = TARGET_ARCHIVE / f"{Path(surf).name}_migrated"
            shutil.move(str(src), str(dst))
            print(f"  ✓ {surf} → archive/{dst.name}")


def phase_6_init_files() -> None:
    """Create __init__.py files for new packages."""
    print("[Phase 6] Creating package __init__.py files...")

    packages = [
        TARGET_SRC / "geox_core",
        TARGET_SRC / "geox_core" / "core",
        TARGET_SRC / "geox_core" / "ingest",
        TARGET_SRC / "geox_core" / "services",
        TARGET_SRC / "geox_core" / "artifacts",
        TARGET_SRC / "geox_core" / "renderers",
        TARGET_SRC / "geox_core" / "plot_specs",
        TARGET_SRC / "geox_core" / "well",
        TARGET_SRC / "geox_core" / "well" / "tools",
        TARGET_SRC / "geox_core" / "well" / "stratigraphy",
        TARGET_SRC / "geox_core" / "skills",
        TARGET_SRC / "geox_core" / "telemetry",
        TARGET_SRC / "geox_core" / "wealth",
        TARGET_SRC / "geox_core" / "envelopes",
        TARGET_SRC / "geox_core" / "schemas",
        TARGET_SRC / "geox_core" / "shared",
        TARGET_SRC / "geox_core" / "adapters",
        TARGET_SRC / "geox_core" / "engines",
        TARGET_SRC / "geox_core" / "jobs",
        TARGET_SRC / "geox_core" / "registry",
        TARGET_SRC / "geox_core" / "enums",
        TARGET_SRC / "geox_core" / "governance",
        TARGET_SRC / "geox_core" / "parity",
        TARGET_SRC / "geox_core" / "compatibility",
        TARGET_SRC / "geox_core" / "laws",
        TARGET_SRC / "geox_core" / "canonical",
        TARGET_SRC / "geox_mcp",
        TARGET_SRC / "geox_mcp" / "tools",
        TARGET_SRC / "geox_mcp" / "tools" / "kernel",
        TARGET_SRC / "geox_mcp" / "contracts",
    ]

    for pkg in packages:
        create_init_py(pkg)

    print("  ✓ Package inits created")


def phase_7_update_pyproject() -> None:
    """Update pyproject.toml to include new packages."""
    print("[Phase 7] Updating pyproject.toml...")

    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        print("  ⚠ pyproject.toml not found")
        return

    content = pyproject.read_text(encoding="utf-8")

    # Add src to packages if using setuptools or flit
    if "[tool.setuptools.packages.find]" in content and 'where = ["src"]' not in content:
        # Insert find directive
        content = content.replace("[tool.setuptools.packages.find]", '[tool.setuptools.packages.find]\nwhere = ["src"]')
        pyproject.write_text(content, encoding="utf-8")
        print("  ✓ Added setuptools.packages.find.where = ['src']")
    elif "[project]" in content and "packages =" not in content:
        # Minimal: just note that PYTHONPATH needs src
        print("  ℹ Ensure PYTHONPATH includes src/ when running the server")


def main() -> int:
    print("=" * 70)
    print("GEOX Low-Entropy Migration")
    print("=" * 70)

    phase_0_create_directories()
    phase_1_migrate_core()
    phase_2_migrate_mcp()
    phase_3_create_resources()
    phase_4_move_docs()
    # phase_5_archive_surfaces()  # 888_HOLD — WELL/ is a live federation organ, Phase 5 deferred
    phase_6_init_files()
    # phase_7_update_pyproject()  # 888_HOLD — run after Phase 0-4 tests are green

    print("=" * 70)
    print("Migration complete.")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. cd /root/geox")
    print("  2. PYTHONPATH=src python -m geox_mcp.server --help")
    print("  3. Fix any import errors that surface")
    print("  4. Run: python scripts/migrate_to_low_entropy.py --verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
