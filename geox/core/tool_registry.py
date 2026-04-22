"""
GEOX Tool Registry & Sealing Engine
DITEMPA BUKAN DIBERI

Enforces the inter-product risk inheritance rules defined in 
GEOX_INTERPRODUCT_RISK_RULES.md.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

from geox.core.vault_client import VaultClient

logger = logging.getLogger("geox.core.tool_registry")


class Verdict(str, Enum):
    SEAL = "SEAL"
    QUALIFY = "QUALIFY"
    HOLD = "HOLD"
    VOID = "VOID"


class DependencyType(str, Enum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"


class ToolRegistry:
    """
    Registry of GEOX canonical products and their dependencies.
    Enforces risk propagation and sealing rules.
    """

    # Canonical Dependency Graph (from §5 of GEOX_INTERPRODUCT_RISK_RULES.md)
    DEPENDENCIES = [
        {"downstream": "CCS", "upstream": "HYDRO", "type": "required", "weight": 0.9},
        {"downstream": "CCS", "upstream": "STRUCTURAL_GEOLOGY", "type": "required", "weight": 0.7},
        {"downstream": "CCS", "upstream": "FRACTURE", "type": "conditional", "weight": 0.6, "condition": "caprock involves faults"},
        {"downstream": "HAZARD", "upstream": "STRUCTURAL_GEOLOGY", "type": "required", "weight": 0.8},
        {"downstream": "HAZARD", "upstream": "REMOTE_SENSING", "type": "optional", "weight": 0.3},
        {"downstream": "SHALLOW_GEOHAZARD", "upstream": "HAZARD", "type": "required", "weight": 0.85},
        {"downstream": "SHALLOW_GEOHAZARD", "upstream": "HYDRO", "type": "required", "weight": 0.5},
        {"downstream": "SHALLOW_GEOHAZARD", "upstream": "STRUCTURAL_GEOLOGY", "type": "conditional", "weight": 0.4, "condition": "slopes > 15 degrees present"},
        {"downstream": "HYDRO", "upstream": "STRUCTURAL_GEOLOGY", "type": "conditional", "weight": 0.5, "condition": "fractured aquifer or karst"},
        {"downstream": "HYDRO", "upstream": "GEOCHEM", "type": "optional", "weight": 0.2},
        {"downstream": "PETROLEUM_SYSTEM", "upstream": "STRUCTURAL_GEOLOGY", "type": "required", "weight": 0.75},
        {"downstream": "PETROLEUM_SYSTEM", "upstream": "GEOCHEM", "type": "required", "weight": 0.4},
        {"downstream": "PETROLEUM_SYSTEM", "upstream": "FRACTURE", "type": "conditional", "weight": 0.5, "condition": "naturally fractured reservoir"},
        {"downstream": "ENVIRONMENTAL", "upstream": "HYDRO", "type": "required", "weight": 0.85},
        {"downstream": "ENVIRONMENTAL", "upstream": "GEOCHEM", "type": "required", "weight": 0.5},
        {"downstream": "ENVIRONMENTAL", "upstream": "SHALLOW_GEOHAZARD", "type": "optional", "weight": 0.2},
        {"downstream": "FRACTURE", "upstream": "STRUCTURAL_GEOLOGY", "type": "required", "weight": 0.6},
        {"downstream": "FRACTURE", "upstream": "REMOTE_SENSING", "type": "optional", "weight": 0.25},
        {"downstream": "GEOTHERMAL", "upstream": "FRACTURE", "type": "required", "weight": 0.65},
        {"downstream": "GEOTHERMAL", "upstream": "HYDRO", "type": "required", "weight": 0.5},
        {"downstream": "GEOTHERMAL", "upstream": "STRUCTURAL_GEOLOGY", "type": "conditional", "weight": 0.4, "condition": "fault-controlled system"},
        {"downstream": "MINERAL", "upstream": "GEOCHEM", "type": "required", "weight": 0.55},
        {"downstream": "MINERAL", "upstream": "STRUCTURAL_GEOLOGY", "type": "conditional", "weight": 0.4, "condition": "structurally controlled deposit"},
        {"downstream": "STRUCTURAL_GEOLOGY", "upstream": "REMOTE_SENSING", "type": "optional", "weight": 0.3},
    ]

    # Critical products where upstream HOLD forces downstream HOLD (Rule 2)
    CRITICAL_PRODUCTS = ["CCS", "HAZARD", "SHALLOW_GEOHAZARD", "ENVIRONMENTAL", "PETROLEUM_SYSTEM"]

    @classmethod
    def get_upstream_dependencies(cls, product_type: str) -> List[Dict[str, Any]]:
        """Returns list of upstream dependencies for a given product type."""
        return [d for d in cls.DEPENDENCIES if d["downstream"] == product_type]

    @classmethod
    def get_downstream_dependents(cls, product_type: str) -> List[Dict[str, Any]]:
        """Returns list of downstream products that depend on product_type."""
        return [d for d in cls.DEPENDENCIES if d["upstream"] == product_type]

    @classmethod
    def resolve_upstream_products(
        cls,
        product_type: str,
        vault: Optional[VaultClient] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Query the vault for all required/conditional upstream products of product_type.
        Returns a dict mapping upstream product_type -> latest vault record.
        """
        if vault is None:
            vault = VaultClient()

        deps = cls.get_upstream_dependencies(product_type)
        resolved = {}
        for dep in deps:
            if dep["type"] == DependencyType.OPTIONAL:
                continue
            u_type = dep["upstream"]
            # Fetch latest product of this upstream type from vault
            products = vault.get_products_by_type(u_type)
            if products:
                resolved[u_type] = products[0]
            else:
                resolved[u_type] = None
        return resolved

    @classmethod
    def check_interproduct_inheritance(
        cls,
        product_type: str,
        own_ac_risk: float,
        upstream_verdicts: Optional[Dict[str, str]] = None,
        upstream_ac_risks: Optional[Dict[str, float]] = None,
        upstream_valid_until: Optional[Dict[str, Optional[str]]] = None,
        own_valid_until: Optional[str] = None,
        use_case: Optional[str] = None,
        vault: Optional[VaultClient] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate all 6 interproduct inheritance rules.
        If upstream_* dicts are not provided, queries vault automatically.
        """
        # Auto-resolve from vault if not explicitly provided
        if upstream_verdicts is None or upstream_ac_risks is None:
            resolved = cls.resolve_upstream_products(product_type, vault=vault)
            upstream_verdicts = upstream_verdicts or {}
            upstream_ac_risks = upstream_ac_risks or {}
            upstream_valid_until = upstream_valid_until or {}
            for u_type, record in resolved.items():
                if record is None:
                    upstream_verdicts[u_type] = Verdict.VOID
                    upstream_ac_risks[u_type] = 1.0
                    upstream_valid_until[u_type] = None
                else:
                    upstream_verdicts.setdefault(u_type, record.get("verdict", Verdict.VOID))
                    upstream_ac_risks.setdefault(u_type, record.get("toac", {}).get("ac_risk", 1.0))
                    upstream_valid_until.setdefault(u_type, record.get("temporal_window", {}).get("valid_until"))

        final_verdict = Verdict.SEAL if own_ac_risk < 0.15 else Verdict.QUALIFY
        if own_ac_risk >= 0.35:
            final_verdict = Verdict.HOLD
        if own_ac_risk >= 0.60:
            final_verdict = Verdict.VOID

        max_inherited_risk = 0.0
        reasons = []
        hold_triggered = False
        min_valid_until = own_valid_until
        cascaded_holds = []

        upstreams = cls.get_upstream_dependencies(product_type)

        for dep in upstreams:
            u_type = dep["upstream"]
            u_verdict_str = upstream_verdicts.get(u_type, Verdict.VOID)
            u_verdict = Verdict(u_verdict_str) if isinstance(u_verdict_str, str) else u_verdict_str
            u_risk = upstream_ac_risks.get(u_type, 1.0)
            u_valid = upstream_valid_until.get(u_type)

            # Rule 1: VOID Propagation
            if u_verdict == Verdict.VOID and dep["type"] == DependencyType.REQUIRED:
                final_verdict = Verdict.HOLD
                hold_triggered = True
                reasons.append(f"Rule 1 VOID: Required upstream {u_type} is VOID.")
                cascaded_holds.append(u_type)

            # Rule 2: HOLD Propagation for critical products
            if u_verdict == Verdict.HOLD and product_type in cls.CRITICAL_PRODUCTS:
                final_verdict = Verdict.HOLD
                hold_triggered = True
                reasons.append(f"Rule 2 HOLD: Critical upstream {u_type} is HOLD.")
                cascaded_holds.append(u_type)

            # Rule 3: AC_Risk Inheritance
            inherited_risk = u_risk * dep["weight"]
            if inherited_risk > max_inherited_risk:
                max_inherited_risk = inherited_risk

            # Rule 5: Temporal Validity Inheritance
            if u_valid is not None:
                if min_valid_until is None or u_valid < min_valid_until:
                    min_valid_until = u_valid

        final_ac_risk = max(own_ac_risk, max_inherited_risk)

        # Re-evaluate verdict based on inherited risk
        if final_ac_risk >= 0.15 and final_verdict == Verdict.SEAL:
            final_verdict = Verdict.QUALIFY
            reasons.append(f"Rule 3 AC_Risk: Inherited risk ({final_ac_risk:.3f}) exceeds SEAL threshold.")
        if final_ac_risk >= 0.35 and final_verdict in (Verdict.SEAL, Verdict.QUALIFY):
            final_verdict = Verdict.HOLD
            hold_triggered = True
            reasons.append(f"Rule 3 AC_Risk: Inherited risk ({final_ac_risk:.3f}) forces HOLD.")
        if final_ac_risk >= 0.60:
            final_verdict = Verdict.VOID
            reasons.append(f"Rule 3 AC_Risk: Inherited risk ({final_ac_risk:.3f}) forces VOID.")

        # Rule 6: City-Scale and Infrastructure Planning
        if use_case:
            use_case_lower = use_case.lower()
            city_cases = ["urban", "city", "dam", "infrastructure", "planning"]
            if any(case in use_case_lower for case in city_cases):
                # Any upstream HOLD on required deps blocks SEAL for city planning
                for dep in upstreams:
                    u_type = dep["upstream"]
                    u_verdict_str = upstream_verdicts.get(u_type, Verdict.VOID)
                    u_verdict = Verdict(u_verdict_str) if isinstance(u_verdict_str, str) else u_verdict_str
                    if dep["type"] in (DependencyType.REQUIRED, DependencyType.CONDITIONAL) and u_verdict in (Verdict.HOLD, Verdict.VOID):
                        if final_verdict == Verdict.SEAL:
                            final_verdict = Verdict.HOLD
                            hold_triggered = True
                            reasons.append(f"Rule 6 Planning: Upstream {u_type} is {u_verdict.value}; city-scale use requires explicit 888_HOLD sign-off.")
                            cascaded_holds.append(u_type)

        return {
            "verdict": final_verdict.value,
            "final_ac_risk": round(final_ac_risk, 4),
            "own_ac_risk": round(own_ac_risk, 4),
            "max_inherited_risk": round(max_inherited_risk, 4),
            "hold_triggered": hold_triggered,
            "cascaded_holds": cascaded_holds,
            "reasons": reasons,
            "effective_valid_until": min_valid_until,
            "upstream_count": len(upstreams),
        }

    @classmethod
    def can_grant_seal(
        cls,
        product_type: str,
        own_ac_risk: float,
        upstream_verdicts: Optional[Dict[str, str]] = None,
        upstream_ac_risks: Optional[Dict[str, float]] = None,
        upstream_valid_until: Optional[Dict[str, Optional[str]]] = None,
        own_valid_until: Optional[str] = None,
        use_case: Optional[str] = None,
        vault: Optional[VaultClient] = None,
    ) -> Dict[str, Any]:
        """
        Terminal check: Can this product be SEALED?
        Implements VOID propagation, HOLD propagation, AC_Risk inheritance,
        temporal validity, and city-scale planning rules.
        """
        result = cls.check_interproduct_inheritance(
            product_type=product_type,
            own_ac_risk=own_ac_risk,
            upstream_verdicts=upstream_verdicts,
            upstream_ac_risks=upstream_ac_risks,
            upstream_valid_until=upstream_valid_until,
            own_valid_until=own_valid_until,
            use_case=use_case,
            vault=vault,
        )
        result["can_seal"] = result["verdict"] == Verdict.SEAL.value
        result["audit_trail"] = {
            "own_ac_risk": result["own_ac_risk"],
            "max_inherited_risk": result["max_inherited_risk"],
            "upstream_count": result["upstream_count"],
            "hold_triggered": result["hold_triggered"],
            "cascaded_holds": result["cascaded_holds"],
        }
        return result
