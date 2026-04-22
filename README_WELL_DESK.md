## WellDesk

GEOX WellDesk is the 1D + 2D well log viewer and rock physics engine for the arifOS constitutional federation. It provides depth-indexed track rendering, forward Gassmann fluid substitution, metabolic iterative convergence, and inverse rock physics inversion — all outputs passing through PhysicsGuard and sealing to VAULT999.

### What WellDesk Does

- **1D Track View**: SVG depth-indexed log tracks (GR, RT, NPHI-RHOB overlay, DT) with zoom, hover tooltips, and gas crossover fill
- **2D Correlation**: Multi-well correlation panel with formation top picks and draggable tie lines
- **Forward Rock Physics**: Gassmann (1951) fluid substitution on Voigt-Reuss-Hill mineral mix — computes Vp, Vs, rho, AI, Vp/Vs from porosity, Sw, vsh, fluid type
- **Inverse Rock Physics**: L-BFGS-B inversion (server) / Nelder-Mead simplex (client) — estimates porosity, Sw, fluid type from observed Vp, Vs, rho
- **Metabolic Convergence**: Iterative convergence loop toward AAA-grade Physics9State, logging every iteration to VAULT999
- **Petrophysics**: Vsh (5 methods), porosity (density, neutron, sonic, ND crossplot), Sw (Archie, Indonesian, Simandoux, Waxman-Smits)
- **AC_Risk**: Anomalous Contrast risk assessment — compares computed against scaffold expected values

### Architecture

```
geox/
├── apps/well-desk/
│   ├── manifest.json                 # MCP App manifest (io.modelcontextprotocol/ui spec)
│   ├── index.html                    # Standalone web viewer (vanilla JS, no CDN)
│   ├── src/
│   │   ├── tracks/
│   │   │   ├── TrackRenderer.js      # Base SVG depth track renderer
│   │   │   ├── GRTrack.js            # Gamma Ray (linear, shale fill)
│   │   │   ├── ResistivityTrack.js   # RT/MSFL (log scale)
│   │   │   ├── PoroDensityTrack.js   # NPHI+RHOB overlay (gas crossover)
│   │   │   └── SonicTrack.js         # DT (linear)
│   │   ├── physics/
│   │   │   ├── Gassmann.js           # Fluid substitution (browser)
│   │   │   ├── VpVsRho.js            # Forward compute wrapper
│   │   │   ├── InverseRockPhysics.js # Nelder-Mead inversion (browser)
│   │   │   └── RockPhysicsTemplate.js # Material catalog + template matcher
│   │   ├── petro/
│   │   │   ├── VshCalc.js            # GR linear + Larionov + Steiber + Clavier
│   │   │   ├── PorosityCalc.js       # Density, neutron, sonic, ND crossplot
│   │   │   └── SwArchie.js           # Archie + Indonesian + Simandoux + Waxman-Smits
│   │   ├── crossplot/
│   │   │   └── XPlot2D.js            # Vp/Vs, NPHI/RHOB crossplot (Canvas)
│   │   ├── correlation/
│   │   │   └── MultiWellPanel.js     # 2D multi-well strip (SVG)
│   │   ├── bridge/
│   │   │   └── MCPBridge.js          # postMessage event handler
│   │   └── vault/
│   │       └── VaultReceipt.js       # VAULT999 receipt builder
│   └── styles/well-desk.css          # Dark theme, scientific precision
├── core/
│   ├── physics9.py                   # Physics9 engine contract
│   └── rock_physics_engine.py        # Gassmann + Biot + forward/metabolic/inverse
├── geox_mcp/tools/
│   └── well_desk_tool.py             # FastMCP tool: geox_well_desk_launch
├── schemas/
│   └── well_desk_event_schema.json   # postMessage event contract
├── contracts/mcp/
│   └── geox_well_desk_contract.json  # MCP tool contract (floors F1-F13)
└── tests/
    └── test_well_desk_physics.py     # Pytest: round-trip, convergence, guard
```

### Launch as Web App

```bash
# Serve index.html from any static server
cd geox/apps/well-desk
python -m http.server 8080
# Open http://localhost:8080
```

No build step required. Vanilla JS + SVG only. No external CDN dependencies.

### Use as MCP App

1. Register tool in FastMCP server:
```python
from geox_mcp.tools.well_desk_tool import register
register(mcp_server)
```

2. Connect via MCP client (Claude, etc.):
```json
{
  "name": "geox_well_desk_launch",
  "arguments": {
    "well_id": "BEK-2",
    "mode": "forward",
    "physics_params": {
      "porosity": 0.22,
      "sw": 0.35,
      "vsh": 0.12,
      "fluid_type": "brine"
    }
  }
}
```

3. UI renders via `resourceUri: "ui://well_desk"` → loads `index.html`

### Quickstart

```bash
# 1. Install dependencies
pip install lasio scipy

# 2. Run tests
pytest tests/test_well_desk_physics.py -v

# 3. Launch with BEK-2 scaffold
python -c "
from core.rock_physics_engine import RockPhysicsEngine, Physics9State
engine = RockPhysicsEngine()
state = engine.load_scaffold('BEK-2')
result = engine.forward(state)
print(f'Vp={result.vp} Vs={result.vs} rho={result.rho} grade={result.grade}')
"

# 4. Run metabolic convergence
result = engine.metabolic(result.vp, result.ai * 1000, state)
print(f'Converged: phi={result.porosity:.3f} Sw={result.sw:.3f} grade={result.grade}')
```

### Tool Contract

Full contract: [contracts/mcp/geox_well_desk_contract.json](contracts/mcp/geox_well_desk_contract.json)

| Parameter | Type | Description |
|-----------|------|-------------|
| `well_id` | string | Well ID (BEK-2, DUL-A1, TNG-3, SLG-1) |
| `mode` | enum | `1d` / `2d` / `forward` / `inverse` / `metabolic` |
| `las_path` | string? | Path to LAS file (null = scaffold) |
| `physics_params` | object | `{porosity, sw, vsh, fluid_type, pressure_mpa, temp_c}` |

**Floors enforced**: F1 (reversibility), F2 (epistemic boundary), F4 (audit trail), F7 (dual-key), F9 (anti-hallucination), F11 (vault log), F13 (human veto)

**Vault route**: `999_VAULT`

**Human in the loop**: `seal_interpretation`, `grade_aaa_promotion`, `inverse_map_accept`

### Scaffold Fixtures

| Well | phi | Sw | vsh | Fluid | Depth Range |
|------|-----|-----|-----|-------|-------------|
| BEK-2 | 0.22 | 0.35 | 0.12 | brine | 2040-2220 m |
| DUL-A1 | 0.18 | 0.42 | 0.25 | oil | 3100-3280 m |
| TNG-3 | 0.15 | 0.55 | 0.35 | brine | 2850-2950 m |

Scaffolds work with zero real data. Load BEK-2, run forward physics, view tracks.

### Constraints

1. No React, no Vue, no webpack. Vanilla JS + SVG + Canvas only.
2. No external CDN in index.html. Self-contained or relative paths only.
3. Python: FastMCP pattern matching existing geox_mcp/tools/*.py files.
4. PhysicsGuard MUST run before any output. RAW grade never reaches UI.
5. Every tool call emits vault_receipt JSON (matches VAULT999 schema).
6. Scaffold fixture must work with zero real data.
7. F9 Anti-Hantu: no hallucinated geology. Unknown = UNKNOWN.
8. 888 Judge = human. AI never seals interpretations autonomously.
