from __future__ import annotations
import numpy as np
from typing import List, Dict, Any, Optional
from geox_core.core.hierarchy import Segment, Prospect

class DependencyEngine:
    """
    WAJIB #3: Explicit Geological Dependency Handling.
    Handles correlation between segments to prevent overestimating portfolio value.
    """
    
    @staticmethod
    def rollout_prospect_probabilistic(prospect: Prospect, draws: int = 10000) -> Dict[str, Any]:
        """
        Rolls up multiple segments into a Prospect-level distribution 
        using explicit dependency logic and structural uncertainty (SUNNAH).
        """
        if not prospect.segments:
            return {"error": "No segments in prospect"}

        rng = np.random.default_rng(seed=42)
        
        # SUNNAH: Segment Multiplier (Structural Uncertainty)
        # Sample how many segments are actually valid per draw
        max_segs = len(prospect.segments)
        if prospect.segment_multiplier_dist:
            s_min = prospect.segment_multiplier_dist.get("min", 1)
            s_ml = prospect.segment_multiplier_dist.get("ml", max_segs)
            s_max = prospect.segment_multiplier_dist.get("max", max_segs)
            active_segments_count = np.round(rng.triangular(s_min, s_ml, s_max, draws)).astype(int)
            active_segments_count = np.clip(active_segments_count, 1, max_segs)
        else:
            active_segments_count = np.full(draws, max_segs, dtype=int)
        
        # Shared factors (Global variables for the prospect)
        shared_source = rng.random(draws)
        shared_seal = rng.random(draws)
        
        prospect_success = np.zeros(draws, dtype=bool)
        prospect_volumes = np.zeros(draws, dtype=float)

        for i, seg in enumerate(prospect.segments):
            # Only consider this segment if it's within the active count for the draw
            is_active = active_segments_count > i
            
            source_success = shared_source < seg.risk.source
            res_success = rng.random(draws) < seg.risk.reservoir
            trap_success = rng.random(draws) < seg.risk.trap
            seal_success = shared_seal < seg.risk.seal
            
            seg_success = source_success & res_success & trap_success & seal_success & is_active
            
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
            "dependency_mode": "SHARED_SOURCE_SEAL",
            "structural_uncertainty_applied": bool(prospect.segment_multiplier_dist)
        }
