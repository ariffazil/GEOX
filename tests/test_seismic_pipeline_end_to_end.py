#!/usr/bin/env python3
"""
GEOX End-to-End Seismic Interpretation Pipeline Verification Test
===================================================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

Runs the complete 7-stage reality loop and asserts that:
    1. Grayscale seismic JPG is processed to Panel D v2
    2. Synthetic SEG-Y is ingested and trace attributes calculated
    3. LAS well log is tied using Bruges Ricker wavelet convolution
    4. GemPy 3D structural block model is computed
    5. WEALTH capital bridge runs, 9-Harness passes, and EMV is computed.

DITEMPA BUKAN DIBERI.
"""

import unittest
import os
import json
import numpy as np


class TestSeismicPipelineEndToEnd(unittest.TestCase):
    
    def test_01_image_cognition_pipeline(self):
        """Test Phase 1 (reality) & Phase 2 (cognition) + Panel D rendering."""
        print("\n[TEST A] Running Image-first Cognition Pipeline...")
        from geox_geological_cognition import run_geological_cognition
        from geox_physical_reality import GeoxPhysicalReality, _compute_attributes, _compute_fault_probability, _extract_amplitude, _crop_seismic_panel, _extract_faults, _extract_horizons
        from PIL import Image
        
        img_path = "/tmp/seismic_image_test/seismic_greyscale.jpg"
        out_dir = "/tmp/test_pipeline_out/cognition"
        
        self.assertTrue(os.path.exists(img_path), f"Input image missing: {img_path}")
        
        # Run interpreter
        pri = GeoxPhysicalReality()
        res = pri.interpret(img_path, output_dir=out_dir)
        self.assertEqual(res.get("verdict"), "PARTIAL_IMAGE_INTERPRETATION")
        self.assertEqual(len(res.get("faults", [])), 3)
        self.assertEqual(len(res.get("horizons", [])), 5)
        
        # Run cognition
        raw = np.array(Image.open(img_path))
        cropped, crop_bbox = _crop_seismic_panel(raw)
        amp = _extract_amplitude(cropped)
        attrs = _compute_attributes(amp)
        fp = _compute_fault_probability(attrs)
        
        # Re-extract with full pts (needed by cognition module)
        faults   = _extract_faults(fp, min_pts=80, max_faults=15)
        horizons = _extract_horizons(attrs, faults, max_horizons=8)
        
        prov = res.get("input", {}).get("provenance", {})
        prov_short = f"img:{prov.get('image_sha256_short','?')} | {prov.get('run_tag','?')}"
        
        cog = run_geological_cognition(
            attrs, fp, faults, horizons,
            output_dir=out_dir,
            basin_context="malay_basin",
            prov_short=prov_short,
            raw_arr=raw,
            crop_bbox=crop_bbox,
            prov=prov
        )
        
        # Assertions
        self.assertTrue(os.path.exists(os.path.join(out_dir, "D_geologist_report.txt")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "D_cognitive_panel.png")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "cognition.json")))
        print("  ✅ Image cognition pipeline verified.")

    def test_02_segy_and_well_tie_pipeline(self):
        """Test SEG-Y ingestion/audit & Bruges well-to-seismic tie."""
        print("\n[TEST B] Running SEG-Y & Well Tie Pipeline...")
        from geox_segy_trace_reality import run_segy_reality_pipeline
        from geox_well_tie_bruges import run_well_tie
        
        segy_path = "/tmp/test_malay.segy"
        las_path = "/root/GEOX/fixtures/_DEMO_SYNTHETIC/DEMO_WELL_A_SANDAKAN.las"
        out_dir = "/tmp/test_pipeline_out/segy_well"
        
        self.assertTrue(os.path.exists(segy_path), f"Synthetic SEG-Y missing: {segy_path}")
        self.assertTrue(os.path.exists(las_path), f"LAS well log missing: {las_path}")
        
        # Run SEG-Y trace reality
        segy_res = run_segy_reality_pipeline(segy_path, out_dir, "malay_basin")
        self.assertEqual(segy_res["ingested"]["status"], "OBS_SEGY_TRACE")
        self.assertEqual(segy_res["trace_attrs"]["status"], "DER_SEGY_ATTRIBUTE")
        
        # Run well tie
        well_res = run_well_tie(las_path, segy_res["audit_path"], out_dir, 250.0)
        self.assertEqual(well_res["status"], "DER_WELL_TWT")
        self.assertTrue(os.path.exists(os.path.join(out_dir, "W3_well_tie_synthetic.png")))
        print("  ✅ SEG-Y and well tie pipeline verified.")

    def test_03_gempy_and_wealth_bridge(self):
        """Test GemPy 3D modeling & WEALTH harness audit bridge."""
        print("\n[TEST C] Running GemPy & WEALTH Bridge...")
        from geox_3d_modeling_gempy import run_gempy_3d_model
        from geox_wealth_bridge import run_wealth_bridge
        
        json_path = "/tmp/geox_panel_d_v2/geoseismic_model.json"
        well_manifest = "/tmp/geox_well_tie/well_tie_manifest.json"
        out_dir = "/tmp/test_pipeline_out/gempy_wealth"
        
        self.assertTrue(os.path.exists(json_path), f"Geoseismic model JSON missing: {json_path}")
        
        # Run GemPy model
        g_res = run_gempy_3d_model(json_path, out_dir)
        self.assertEqual(g_res["status"], "INT_3D_STRUCTURE")
        self.assertTrue(os.path.exists(g_res["plot_path"]))
        self.assertTrue(os.path.exists(g_res["grid_path"]))
        
        # Run WEALTH bridge
        w_res = run_wealth_bridge(
            os.path.join(out_dir, "gempy_manifest.json"),
            g_res["grid_path"],
            well_manifest,
            out_dir
        )
        self.assertEqual(w_res["status"], "CAPITAL_CONSEQUENCE")
        self.assertEqual(w_res["verdict"], "PASS")
        self.assertEqual(w_res["decision_state"], "HOLD")  # sub-economic reservoir size
        print("  ✅ GemPy and WEALTH bridge verified.")


if __name__ == "__main__":
    unittest.main()
