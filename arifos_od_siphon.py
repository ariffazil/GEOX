"""
arifos_od_siphon.py — OpendTect-Resident Sovereign Siphon (v1.2)
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

This script is designed to be loaded into the OpendTect Python Console.
It distills heavy OD project data into the GEOX 'Causal Scene' schema.
"""

import json
import os
import sys

# Standard ODBind imports
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
    def __init__(self, survey_name=None):
        if not OD_AVAILABLE:
            self.error = "odbind not found. Run inside OpendTect Python environment."
            return
            
        try:
            self.survey = odsurvey.Survey.current() if not survey_name else odsurvey.Survey(survey_name)
            self.info = self.survey.info
            self.error = None
        except Exception as e:
            self.error = f"Failed to attach to survey: {str(e)}"

    def distill_manifold(self) -> dict:
        """The Manifold: Standardized spatial-temporal domain."""
        if self.error: return {"error": self.error}
        
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
                "provenance": {"created_by": h_info.user_name}
            }
        except Exception as e:
            return {"error": f"Claim distillation failed: {str(e)}"}

    def distill_truth(self, well_name):
        """Extracts Well Markers (The Hard Witness) for F2 Truth."""
        if self.error: return {"error": self.error}
        try:
            w = odwell.Well(self.survey, well_name)
            markers = w.get_markers()
            return [
                {"name": m.name, "z_md": m.depth, "z_twt": m.twt} 
                for m in markers
            ]
        except Exception as e:
            return {"error": f"Truth extraction failed: {str(e)}"}

    def distill_logs(self, well_name, log_names=['RHOB', 'DT']):
        """Siphons raw logs for the D2T Synthetic Bridge."""
        if self.error: return {"error": self.error}
        try:
            w = odwell.Well(self.survey, well_name)
            results = {}
            for ln in log_names:
                try:
                    log = w.get_log(ln)
                    results[ln] = log.data.tolist()
                except: continue
            return results
        except Exception as e:
            return {"error": f"Log siphon failed: {str(e)}"}

    def export_causal_scene(self, horizon_id=None, well_name=None, path=None):
        """Full Causal Scene Generation."""
        scene = {
            "manifold": self.distill_manifold(),
            "claims": [],
            "truth": [],
            "logs": {},
            "status": "SEALED",
            "metadata": {"version": "v1.2"}
        }
        
        if horizon_id: scene["claims"].append(self.distill_claim(horizon_id))
        if well_name:
            scene["truth"] = self.distill_truth(well_name)
            scene["logs"] = self.distill_logs(well_name)
            
        if path:
            with open(path, 'w') as f: json.dump(scene, f, indent=2)
        else:
            print(json.dumps(scene, indent=2))
        return scene

def main():
    siphon = ODSiphon()
    if siphon.error:
        print(json.dumps({"status": "FAILURE", "error": siphon.error}))
        sys.exit(1)
        
    # CLI: python arifos_od_siphon.py <hor_name> <well_name>
    hor = sys.argv[1] if len(sys.argv) > 1 else None
    well = sys.argv[2] if len(sys.argv) > 2 else None
    siphon.export_causal_scene(horizon_id=hor, well_name=well)

if __name__ == "__main__":
    main()
