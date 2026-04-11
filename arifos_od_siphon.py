"""
arifos_od_siphon.py — OpendTect-Resident Sovereign Siphon (v1.1)
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

This script is designed to be loaded into the OpendTect Python Console.
It distills heavy OD project data into the GEOX 'Causal Scene' schema.
"""

import json
import os
import sys

# Protocol: We attempt to import odbind. 
# Fixed Bug 2: Correct module names from ODBind documentation.
try:
    import odbind.survey as odsurvey
    import odbind.horizon3d as odhor
    import odbind.well as odwell
    OD_AVAILABLE = True
except ImportError:
    OD_AVAILABLE = False

class ODSiphon:
    """
    The Siphon: Extracts truth from OpendTect mess into GEOX Causal Scenes.
    """
    # Fixed Bug 1: Refactored to __init__
    def __init__(self, survey_name=None):
        if not OD_AVAILABLE:
            self.error = "odbind not found. Ensure this script runs inside OpendTect's Python environment."
            return
            
        try:
            # Use current survey if not specified
            if survey_name:
                self.survey = odsurvey.Survey(survey_name)
            else:
                self.survey = odsurvey.Survey.current()
            
            # Use the high-fidelity info struct from ODBind
            self.info = self.survey.info
            self.error = None
        except Exception as e:
            self.error = f"Failed to attach to survey: {str(e)}"

    def distill_manifold(self) -> dict:
        """The Manifold: Standardized spatial-temporal domain."""
        if self.error: return {"error": self.error}
        
        # ODBind metadata mapping via info object
        zs = self.info.zsamp
        ins = self.info.inlsamp
        crs = self.info.crlsamp
        
        return {
            "survey_name": self.survey.name,
            "crs": self.info.cr_system.name if self.info.cr_system else "Unknown",
            "xy_unit": self.info.xy_unit,
            "z_unit": self.info.z_unit,
            "z_domain": self.info.z_domain,
            "inline":    {"start": ins.start, "step": ins.step, "count": ins.nr},
            "crossline": {"start": crs.start, "step": crs.step, "count": crs.nr},
            "z":         {"start": zs.start,  "step": zs.step,  "count": zs.nr},
            "seal": "DITEMPA_BUKAN_DIBERI"
        }

    # Fixed Bug 3: CLI Non-blocking model
    def distill_claim(self, horizon_id: str) -> dict:
        """The Claim: Interpreted surface geometry."""
        if self.error: return {"error": self.error}
        
        try:
            h = odhor.Horizon3DSurveyObject(self.survey, horizon_id)
            h_info = h.info
            return {
                "id": horizon_id,
                "type": "Horizon3D",
                "z_range": [float(h_info.z_min), float(h_info.z_max)],
                "provenance": {
                    "created_by": h_info.user_name,
                    "created_at": getattr(h_info, 'created_at', 'Unknown')
                }
            }
        except Exception as e:
            return {"error": f"Claim distillation failed: {str(e)}"}

    def export_causal_scene(self, horizon_id=None, path=None):
        """Packages everything into the final JSON manifold."""
        scene = {
            "manifold": self.distill_manifold(),
            "claims": [],
            "truth": [],
            "status": "SEALED",
            "metadata": {"origin": "arifos_od_siphon_v1.1"}
        }
        
        if horizon_id:
            scene["claims"].append(self.distill_claim(horizon_id))
            
        if path:
            with open(path, 'w') as f:
                json.dump(scene, f, indent=2)
        else:
            print(json.dumps(scene, indent=2))
        return scene

def main():
    """CLI Entrypoint for the GEOX Agent to pipe data."""
    siphon = ODSiphon()
    if siphon.error:
        print(json.dumps({"status": "FAILURE", "error": siphon.error}))
        sys.exit(1)
        
    # Example usage: python arifos_od_siphon.py <hor_name>
    hor_name = sys.argv[1] if len(sys.argv) > 1 else None
    siphon.export_causal_scene(horizon_id=hor_name)

if __name__ == "__main__":
    main()
