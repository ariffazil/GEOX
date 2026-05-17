import sys
import os

# Add geox to path
sys.path.append(os.path.abspath("."))

from geox.core.epistemic_integrity import EpistemicIntegrity

def test_epistemic_integrity():
    ei = EpistemicIntegrity()
    
    # CASE 1: Low integrity (Low density, high breadth, high coupling)
    outputs_low = {
        "p10": 1.0,
        "p90": 10.0,
        "porosity": 0.15,
        "sw": 0.3
    }
    pos_coupled = {
        "Charge": "model_v1",
        "Reservoir": "model_v1",
        "Trap": "model_v1",
        "Seal": "model_v1"
    }
    
    result_low = ei.compute_integrity(
        outputs=outputs_low,
        well_density=0.1,  # Very sparse
        model_lineage=["model_v1"],
        pos_components=pos_coupled
    )
    
    print("\n--- CASE 1: LOW INTEGRITY ---")
    print(f"Integrity Score: {result_low.integrity_score:.4f}")
    print(f"Classification: {result_low.classification}")
    print(f"Hold: {result_low.hold}")
    print(f"Recommendation: {result_low.recommendation}")
    
    # CASE 2: High integrity (High density, low breadth, diverse models)
    outputs_high = {
        "p10": 2.0,
        "p90": 4.0,  # Ratio 2.0 (good)
        "porosity": 0.22,
        "porosity_source": "measured",
        "sw": 0.2,
        "sw_source": "measured"
    }
    pos_diverse = {
        "Charge": "basin_model_v4",
        "Reservoir": "petrophys_v2",
        "Trap": "seismic_v9",
        "Seal": "seal_model_v1"
    }
    
    result_high = ei.compute_integrity(
        outputs=outputs_high,
        well_density=5.0,  # Dense
        model_lineage=["basin_model_v4", "petrophys_v2", "seismic_v9", "seal_model_v1"],
        pos_components=pos_diverse
    )
    
    print("\n--- CASE 2: HIGH INTEGRITY ---")
    print(f"Integrity Score: {result_high.integrity_score:.4f}")
    print(f"Classification: {result_high.classification}")
    print(f"Hold: {result_high.hold}")
    print(f"Recommendation: {result_high.recommendation}")
    for cl in result_high.confidence_levels:
        print(f"  - {cl.parameter}: {cl.score:.2f} ({cl.basis})")

if __name__ == "__main__":
    test_epistemic_integrity()
