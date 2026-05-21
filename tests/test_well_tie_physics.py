import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from geox_core.engines.seismic.well_tie import (
    calculate_acoustic_impedance,
    calculate_reflectivity,
    generate_ricker,
    convolve_synthetic
)

def test_reflectivity_math():
    """Verify epsilon < 1e-6 deviation from expected bounds."""
    # Test case: rho1=2000, v1=2000 => Z1=4,000,000
    #            rho2=2200, v2=2500 => Z2=5,500,000
    # R = (5.5 - 4.0) / (5.5 + 4.0) = 1.5 / 9.5 = 0.1578947
    
    rho = np.array([2000.0, 2200.0])
    vp = np.array([2000.0, 2500.0])
    
    z = calculate_acoustic_impedance(rho, vp)
    r = calculate_reflectivity(z)
    
    expected_r0 = (5500000.0 - 4000000.0) / (5500000.0 + 4000000.0)
    
    deviation = abs(r[0] - expected_r0)
    print(f"Computed R[0]: {r[0]}")
    print(f"Expected R[0]: {expected_r0}")
    print(f"Deviation: {deviation}")
    
    assert deviation < 1e-6, f"F2 Violation: Reflectivity deviation {deviation} exceeds epsilon 1e-6"
    print("F2 Verification Passed: Reflectivity math is deterministic and accurate.")

def test_impedance_math():
    rho = np.array([2.0, 2.5])
    vp = np.array([2000.0, 3000.0])
    z = calculate_acoustic_impedance(rho, vp)
    expected_z = np.array([4000.0, 7500.0])
    assert np.allclose(z, expected_z, atol=1e-6)
    print("F2 Verification Passed: Impedance math is correct.")

if __name__ == "__main__":
    try:
        test_impedance_math()
        test_reflectivity_math()
    except AssertionError as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
