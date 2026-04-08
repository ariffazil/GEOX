# Cross-Wiki Links — arifOS Federation

> **Type:** Integration  
> **Purpose:** Navigation between federated wikis  
> **Tags:** [federation, navigation, arifos, integration]  

---

## The Federation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    arifOS FEDERATED KNOWLEDGE GRAPH                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│   │   arifOS/wiki/  │◄───►│   GEOX/wiki/    │◄───►│  @WEALTH/wiki/  │      │
│   │   (Constitution)│     │   (Earth)       │     │   (Economics)   │      │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘      │
│          ▲                       ▲                       ▲                  │
│          │                       │                       │                  │
│          └───────────────────────┴───────────────────────┘                  │
│                                                                             │
│                    [[arifos::index]]                                        │
│                    [[geox::index]]        ← You are here                    │
│                    [[wealth::index]]                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Link Syntax

| Target | Syntax | Example |
|--------|--------|---------|
| arifOS wiki | `[[arifos::Page_Name]]` | `[[arifos::Floors]]` |
| GEOX wiki (self) | `[[Page_Name]]` | `[[Theory_of_Anomalous_Contrast]]` |
| @WEALTH wiki | `[[wealth::Page_Name]]` | `[[wealth::NPV_Models]]` |
| Raw source | `[[raw/filename]]` | `[[raw/papers/bond_2007.pdf]]` |

---

## Key arifOS → GEOX Links

| arifOS Page | GEOX Destination | Purpose |
|-------------|------------------|---------|
| [[arifos::GEOX]] | [[index]] | Entry point to Earth knowledge |
| [[arifos::Floors#F2]] | [[70_GOVERNANCE/Floor_Enforcement_Log]] | Truth enforcement in geoscience |
| [[arifos::Floors#F4]] | [[10_THEORY/Epistemic_Levels]] | Clarity in OBS/DER/INT/SPEC |
| [[arifos::Floors#F7]] | [[70_GOVERNANCE/Confidence_Bands]] | Humility in uncertainty |
| [[arifos::Floors#F9]] | [[10_THEORY/Theory_of_Anomalous_Contrast]] | Anti-hantu in geoscience |
| [[arifos::888_JUDGE]] | [[70_GOVERNANCE/888_HOLD_Registry]] | Human sovereignty gates |
| [[arifos::999_VAULT]] | [[80_INTEGRATION/VAULT999_Wiring]] | Audit trail integration |
| [[arifos::Trinity_Architecture]] | [[80_INTEGRATION/Trinity_Architecture]] | Position in ΔΩΨ |

---

## Key GEOX → arifOS Links

| GEOX Page | arifOS Destination | Purpose |
|-----------|-------------------|---------|
| All governance pages | [[arifos::Floors]] | Constitutional foundation |
| All tool specs | [[arifos::MCP_Tools]] | Tool surface alignment |
| All cases | [[arifos::999_VAULT]] | Audit architecture |
| [[80_INTEGRATION/Trinity_Architecture]] | [[arifos::Trinity_Architecture]] | Federation position |

---

## Synchronization Protocol

| Event | Source Wiki | Target Wiki | Action |
|-------|-------------|-------------|--------|
| 888_HOLD triggered | GEOX | arifOS | Update [[arifos::888_JUDGE]] registry |
| Floor violation | GEOX | arifOS | Log in [[arifos::Floors]] enforcement |
| New tool added | arifOS | GEOX | Create [[50_TOOLS/tool_name]] spec |
| New seal issued | arifOS | GEOX | Update [[70_GOVERNANCE/Seals_and_Verdicts]] |
| Weekly lint | GEOX | — | Update [[90_AUDITS/Weekly_Lint_Reports]] |

---

## Navigation Quick Reference

### Start Here
- **New to arifOS?** → [[arifos::Quickstart]]
- **New to GEOX?** → [[00_INDEX/Quickstart]]
- **The intelligence stack?** → [[00_INDEX/LLM_LEM_Manifesto]]

### Constitutional
- **13 Floors** → [[arifos::Floors]]
- **F9 Anti-Hantu** → [[10_THEORY/Theory_of_Anomalous_Contrast]]

### Technical
- **MCP Tools** → [[arifos::MCP_Tools]]
- **GEOX Tools** → [[50_TOOLS/geox_evaluate_prospect]]

### Governance
- **888_JUDGE** → [[arifos::888_JUDGE]]
- **888_HOLD Registry** → [[70_GOVERNANCE/888_HOLD_Registry]]

---

*Federated Knowledge Graph*  
*Constitutional Intelligence Across Wikis*
