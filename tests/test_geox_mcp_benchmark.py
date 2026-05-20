import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

cv2 = pytest.importorskip("cv2", reason="opencv-python-headless required for vision_bridge")
from geox_core.engines.seismic.vision_bridge import GEOXVisionDepthEngine

def test_benchmark_dix_physics_bounds():
    engine = GEOXVisionDepthEngine()
    
    # Test Case: Extreme processing estimation that breaks physical bounds
    v_rms_broken = np.array([1500.0, 4500.0, 1500.0]) # Impossible velocity oscillation
    twt_profile = np.array([0.0, 1.0, 2.0])
    
    # The compute engine must safely intercept and clip or fail the execution
    v_int = engine.compute_attested_depth(twt_profile * 1000.0, v_rms_broken)
    
    # Assert that no value in the interval velocity array breaches matrix boundaries
    assert np.all(v_int <= 5500.0), "Benchmark Failed: MCP let an unphysical velocity pass (Sabah limit 5500)."
    assert np.all(v_int >= 1480.0), "Benchmark Failed: Interval velocity dropped below fluid limit (Sabah limit 1480)."
    print("Benchmark Anchored: F2 Physics Guard is functioning perfectly with Sabah Basin limits.")

if __name__ == "__main__":
    try:
        test_benchmark_dix_physics_bounds()
    except AssertionError as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
