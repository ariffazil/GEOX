# Governance & Policy

Governance ensures operations respect rights, boundaries, and constitutional constraints. GEOX embeds governance into every skill.

## Overview

The Governance domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `boundary_verify` | Reconcile boundary geometries | machine, human |
| `rights_mapping` | Map tenure and restrictions | machine, human |
| `compliance_check` | Verify regulatory conformance | machine, human |
| `constitutional_gate` | Enforce arifOS constraints | machine, human, void |

## Boundary Verification

Boundaries define jurisdictions:
- **International**: Treaty boundaries
- **National**: Country borders
- **Subnational**: States, provinces, districts
- **Property**: Cadastral parcels

### Boundary Challenges

- **Ambiguity**: "The river" shifts over time
- **Overlaps**: Competing claims
- **Gaps**: Unclaimed areas
- **Datums**: Different reference frames

## Rights Mapping

Tenure rights define who can do what where:
- **Ownership**: Freehold, leasehold
- **Use rights**: Grazing, fishing, water
- **Restrictions**: Protected areas, easements
- **Sovereign rights**: Natural resources

### Rights Matrix

| Area | Owner | User | Restrictions |
|------|-------|------|--------------|
| Zone A | State | Local community | No extraction |
| Zone B | Private | Owner only | Standard use |
| Zone C | Federal | Multiple | Navigable waters |

## Compliance Checking

Operations must comply with:
- **Environmental**: EIA,排放 standards
- **Spatial**: Zoning, setback requirements
- **Sectoral**: Mining, forestry, fishing permits
- **International**: Treaties, conventions

### Compliance Workflow

1. Define operation boundaries
2. Overlay regulatory layers
3. Identify conflicts
4. Propose mitigations
5. Document compliance status

## Constitutional Gate

The `constitutional_gate` skill implements arifOS F1-F13 constraints.

### Verdict Types

- **888 SEAL**: Proceed — all floors passed
- **888 QUALIFY**: Proceed with conditions
- **888 HOLD**: Pause for human review
- **888 VOID**: Reject — constitutional violation

### Floors Evaluated

| Floor | Principle | Check |
|-------|-----------|-------|
| F1 | Reversibility | Can this be undone? |
| F2 | Truth | Are all claims grounded? |
| F6 | Harm | Any foreseeable harm? |
| F9 | Anti-Hantu | No hidden intentions? |
| F13 | Sovereign | Human authority preserved? |

## Constitutional Constraints

Governance is foundational:
- **F13 Sovereign**: Human authority is non-negotiable
- **F1 Amanah**: No irreversible action without 888 SEAL
- **All floors**: Every operation passes F1-F13

## See Also

- [888 HOLD Protocol](888-hold.md) — Human authorization
- [arifOS Constitution](arifos.md) — Full constitutional text
- [Constitutional Gate](../../apps/site/skills/constitutional_gate.html) — Skill detail
