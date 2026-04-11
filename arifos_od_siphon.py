"""
arifos_od_siphon.py — OpendTect-Resident Sovereign Siphon
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

This script is designed to be loaded into the OpendTect Python Console.
It distills heavy OD project data into the GEOX 'Causal Scene' schema.
"""

import json
import os
import sys

# Protocol: We attempt to import odbind. 
# If running inside OpendTect's Python, this should succeed.
try:
    import odbind.survey as odsurvey
    import odbind.seismic as odseismic
    import odbind.well as odwell
    import odbind.horizon as odhor
    OD_AVAILABLE = True
except ImportError:
    OD_AVAILABLE = False

class ODSiphon:
    """
    The Siphon: Extracts truth from OpendTect mess into GEOX Causal Scenes.
    """
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
            self.error = None
        except Exception as e:
            self.error = f"Failed to attach to survey: {str(e)}"

    def distill_manifold(self) -> dict:
        """The Manifold: Admissible spatial-temporal domain."""
        if self.error: return {"error": self.error}
        
        # ODBind metadata mapping
        sm = self.survey.metadata
        return {
            "manifold": {
                "name": self.survey.name,
                "crs": sm.get("CRS", "Unknown"),
                "z_domain": sm.get("ZDomain", "TWT"),
                "ranges": {
                    "inl": [float(sm.get("FirstInl", 0)), float(sm.get("LastInl", 0))],
                    "crl": [float(sm.get("FirstCrl", 0)), float(sm.get("LastCrl", 0))],
                    "z": [float(sm.get("FirstZ", 0)), float(sm.get("LastZ", 0))]
                },
                "units": {
                    "xy": sm.get("Units.XY", "m"),
                    "z": sm.get("Units.Z", "ms")
                }
            },
            "status": "SEALED",
            "seal": "DITEMPA_BUKAN_DIBERI"
        }

    def distill_claim(self, horizon_id: str) -> dict:
        """The Claim: Interpreted surface geometry."""
        if self.error: return {"error": self.error}
        
        try:
            h = odhor.Horizon3D(self.survey, horizon_id)
            return {
                "claim": {
                    "id": horizon_id,
                    "type": "Horizon3D",
                    "z_range": [float(h.min_z), float(h.max_z)],
                    "provenance": {
                        "created_by": h.metadata.get("Created.By", "Unknown"),
                        "created_at": h.metadata.get("Created.At", "Unknown")
                    }
                }
            }
        except Exception as e:
            return {"error": f"Claim distillation failed: {str(e)}"}

def main():
    """CLI Entrypoint for the GEOX Agent to pipe data."""
    siphon = ODSiphon()
    if siphon.error:
        print(json.dumps({"status": "FAILURE", "error": siphon.error}))
        sys.exit(1)
        
    # Default behavior: Print Manifold
    print(json.dumps(siphon.distill_manifold(), indent=2))

if __name__ == "__main__":
    main()
