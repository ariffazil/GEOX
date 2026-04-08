# Tool Index

> **Type:** Index  
> **Epistemic Level:** OBS  
> **Last Updated:** 2026-04-08  
> **Tags:** [index, tools, mcp, registry]  

---

## Complete Tool Registry

| Tool | Risk Level | Primary Floors | Status | Page |
|------|-----------|----------------|--------|------|
| **geox_load_seismic_line** | GUARDED | F4, F11 | ✅ Active | [[geox_load_seismic_line]] |
| **geox_build_structural_candidates** | SAFE | F2, F7, F9 | ✅ Active | [[geox_build_structural_candidates]] |
| **geox_evaluate_prospect** | GUARDED | F1, F7, F13 | ✅ Active | [[geox_evaluate_prospect]] |
| **geox_load_well_log_bundle** | SAFE | F4, F11 | 🚧 Planned | [[geox_load_well_log_bundle]] |
| **geox_qc_logs** | SAFE | F2, F4 | 🚧 Planned | [[geox_qc_logs]] |
| **geox_extract_attributes** | SAFE | F4 | 🚧 Planned | [[geox_extract_attributes]] |
| **geox_query_ratlas** | SAFE | F2 | ✅ Active | [[geox_query_ratlas]] |
| **geox_audit_conflation** | GUARDED | F9 | 🚧 Planned | [[geox_audit_conflation]] |

---

## Risk Level Definitions

| Level | Description | Floors | Examples |
|-------|-------------|--------|----------|
| **SAFE** | Read-only, no state mutation | F2, F4 | Query RATLAS, load data |
| **GUARDED** | May suggest irreversible actions | +F1, F13 | Evaluate prospect |
| **DANGEROUS** | State mutation, destructive | +888_HOLD | Delete data, modify records |

---

## Floor Coverage

| Floor | Tools Enforcing | Violations Logged |
|-------|----------------|-------------------|
| F1 Amanah | 2 tools | [[70_GOVERNANCE/888_HOLD_Registry]] |
| F2 Truth | 8 tools | [[70_GOVERNANCE/Floor_Enforcement_Log]] |
| F4 Clarity | 6 tools | [[70_GOVERNANCE/Floor_Enforcement_Log]] |
| F7 Humility | 5 tools | [[70_GOVERNANCE/Floor_Enforcement_Log]] |
| F9 Anti-Hantu | 4 tools | [[70_GOVERNANCE/Floor_Enforcement_Log]] |
| F11 Authority | 4 tools | [[70_GOVERNANCE/Floor_Enforcement_Log]] |
| F13 Sovereign | 2 tools | [[70_GOVERNANCE/888_HOLD_Registry]] |

---

## Usage Patterns

### Pattern 1: Data Loading
```
geox_load_seismic_line → geox_qc_logs → geox_extract_attributes
```

### Pattern 2: Structural Interpretation
```
geox_build_structural_candidates → geox_audit_conflation
```

### Pattern 3: Prospect Evaluation
```
geox_evaluate_prospect → [888_HOLD if triggered] → Seals_and_Verdicts
```

---

## Integration with arifOS

All tools register with [[arifos::MCP_Tools]]:
- Tool metadata
- Floor compliance status
- Usage statistics
- Error rates

---

*Tool Index v1.0.0 · Part of GEOX Wiki*
