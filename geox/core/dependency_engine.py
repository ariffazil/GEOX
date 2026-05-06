from __future__ import annotations
import numpy as np
from typing import List, Dict, Any, Optional
from geox.core.hierarchy import Segment, Prospect

class DependencyEngine:
    """
    WAJIB #3: Explicit Geological Dependency Handling.
    Handles correlation between segments to prevent overestimating portfolio value.
    """
    
    @staticmethod
    def rollout_prospect_probabilistic(prospect: Prospect, draws: int = 10000) -> Dict[str, Any]:
        """
        Rolls up multiple segments into a Prospect-level distribution 
        using explicit dependency logic.
        """
        if not prospect.segments:
            return {"error": "No segments in prospect"}

        # Initialize success trials (Independent by default unless specified)
        # 1.0 = success, 0.0 = failure
        rng = np.random.default_rng(seed=42)
        
        # Shared factors (Global variables for the prospect)
        # In a real model, these would be mapped from prospect.dependencies
        shared_source = rng.random(draws)
        shared_seal = rng.random(draws)
        
        segment_results = []
        prospect_success = np.zeros(draws, dtype=bool)
        prospect_volumes = np.zeros(draws, dtype=float)

        for seg in prospect.segments:
            # Simple Shared Risk Logic:
            # If shared_source < seg.risk.source, the source is present for ALL dependent segments.
            source_success = shared_source < seg.risk.source
            res_success = rng.random(draws) < seg.risk.reservoir
            trap_success = rng.random(draws) < seg.risk.trap
            seal_success = shared_seal < seg.risk.seal
            
            seg_success = source_success & res_success & trap_success & seal_success
            
            # Volume if success
            # (Simplification: assuming P50 as constant for this roll-up demo)
            seg_vol = seg.volumetrics.get("p50", 0.0)
            
            prospect_volumes += np.where(seg_success, seg_vol, 0.0)
            prospect_success = np.logical_or(prospect_success, seg_success) 
            
        success_indices = prospect_volumes > 0
        valid_volumes = prospect_volumes[success_indices]
        
        if len(valid_volumes) == 0:
            return {"gcos": 0.0, "p50": 0.0, "status": "ALL_FAIL"}

        return {
            "prospect_id": prospect.id,
            "gcos": round(float(np.mean(prospect_success)), 4),
            "p90": round(float(np.percentile(valid_volumes, 10)), 2),
            "p50": round(float(np.percentile(valid_volumes, 50)), 2),
            "p10": round(float(np.percentile(valid_volumes, 90)), 2),
            "dependency_mode": "SHARED_SOURCE_SEAL"
        }
