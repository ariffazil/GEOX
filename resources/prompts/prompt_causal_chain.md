# Prompt: Causal Chain Discipline (E1)

> **Source:** Copilot "Physical Earth Reality Physics" — Causality section
> **Status:** DRAFT — pending server.py wiring
> **Eurekaness:** HIGH

## What this prompt enforces

Every GEOX result that makes a non-trivial claim should carry a **causal chain** tracing the upstream physics → intermediate effect → downstream claim. Not just provenance (which tool was called) — actual cause-and-effect.

## Pattern

```json
{
  "causal_chain": [
    {
      "step": "fast extension rate at 20 Ma",
      "mechanism": "lithospheric stretching",
      "physics_domain": "tectonics",
      "conservation_law": "momentum"
    },
    {
      "step": "high subsidence rate at margin",
      "mechanism": "flexural isostatic response",
      "physics_domain": "tectonics",
      "conservation_law": "mass"
    },
    {
      "step": "thick sediment accumulation in half-graben",
      "mechanism": "depositional infill",
      "physics_domain": "tectonics",
      "conservation_law": "mass"
    },
    {
      "step": "deep burial of Late Cretaceous source rock",
      "mechanism": "sediment loading",
      "physics_domain": "tectonics",
      "conservation_law": "mass"
    },
    {
      "step": "source rock enters oil window at 10 Ma",
      "mechanism": "thermal maturation (Arrhenius)",
      "physics_domain": "thermodynamics",
      "conservation_law": "energy"
    },
    {
      "step": "hydrocarbon generation, 200 MMbbl",
      "mechanism": "kerogen pyrolysis",
      "physics_domain": "geochemistry",
      "conservation_law": "mass"
    }
  ]
}
```

## Discipline rules

1. **Each step must name a mechanism** — not "associated with" or "correlated with"
2. **Each step must cite a physics domain** — pick from the 8 (tectonics, thermodynamics, fluid_flow, surface_ocean, wave_sar, geochemistry, rock_physics, petrophysics)
3. **Each step should reference a conservation law** — mass, energy, momentum, charge, isotope, pvt, or none
4. **The chain should be falsifiable** — if any link breaks (e.g., source rock not actually mature), the whole chain collapses
5. **No black boxes** — if a step is "AI-predicted", label it as such and require downstream validation

## Where this lives in GEOX

- `envelope.causal_chain[]` — top-level field in result (when wired)
- `definitions.causal_link` — already in `geox_output_envelope.schema.json`
- Used in: `geox_prospect_evaluate`, `geox_subsurface_generate_candidates`, `geox_claim_create`

## Anti-patterns (forbidden)

- ❌ "Trap X is filled with oil" without a chain showing source → migration → trap
- ❌ Citing a single mechanism for a multi-step phenomenon
- ❌ Skipping intermediate steps ("the source rock matured" without showing burial + heat)

## Validation pattern

```python
def validate_causal_chain(chain):
    for i, link in enumerate(chain):
        if not link.get("mechanism"):
            return {"valid": False, "broken_at": i, "reason": "missing mechanism"}
        if not link.get("physics_domain"):
            return {"valid": False, "broken_at": i, "reason": "missing domain"}
        if link.get("conservation_law") in ["mass", "energy", "momentum"]:
            # verify mass/energy balance at this step
            pass
    return {"valid": True, "length": len(chain)}
```

## Cross-references

- `definitions.causal_link` in `geox_output_envelope.schema.json`
- `prompt_claim_discipline.md` — claim-state separation
- `prompt_red_team_reviewer.md` — attacks the chain's weakest link

---

**DITEMPA BUKAN DIBERI** — Trace every claim to its physics.
