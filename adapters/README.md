# GEOX Core Adapters Inventory

To fulfill the Phase 0 Foundation Hardening, GEOX explicitly identifies and bounds its 4 core adapters. These adapters are the *only* authorized bridges between the GEOX Subsurface Intelligence layer and the rest of the arifOS federation / external systems.

## 1. wealth_bridge (Capital & Compute)
- **Status**: Loaded
- **Purpose**: Connects GEOX to the `WEALTH` MCP for budget authorization when running heavy subsurface compute (e.g., Seismic Foundation Models, Inversion runs, cloud OSDU queries).
- **Target**: `localhost:18082` (WEALTH)

## 2. osdu_bridge (Enterprise Subsurface Data)
- **Status**: Stubbed / Planned
- **Purpose**: Connects GEOX to OSDU / OpenWorks / Petrel data lakes to ingest SEG-Y, LAS, trajectories, and interpretation metadata securely.
- **Target**: External OSDU R3 instances.

## 3. well_readiness_bridge (WELL Organ)
- **Status**: Stubbed / Planned
- **Purpose**: Connects GEOX to the `WELL` organ (Human Readiness) to evaluate interpreter fatigue before allowing the sealing of high-risk prospect decisions.
- **Target**: `localhost:18083` (WELL)

## 4. vault_seal_bridge (Audit & Memory)
- **Status**: Loaded (via `999_vault` volume)
- **Purpose**: Provides cryptographic sealing of all interpretation claims, provenance, and human approvals into `Vault999`.
- **Target**: Local `999_vault` directory / arifOS memory broker.

> **Law of Adapters**: No new adapters may be added without explicit F13 SOVEREIGN authorization. All adapters must adhere to the Bearer Auth / mTLS api_auth schema before touching real Earth data.
