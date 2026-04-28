import numpy as np
import sys

sys.path.insert(0, "/root/geox")

from geox.skills.subsurface.petro.gr_intervals import run_gr_cognitive_pipeline


def test_gr_cognitive_merging():
    """Verify that thin intervals (<5m) are merged to maintain human-scale resolution."""
    print("Testing GR Cognitive Interval Extraction...")

    # Create a synthetic GR log with 1m resolution
    depth = np.arange(2000, 2100, 1.0)

    # Pattern: 20m clean, 2m dirty (thin), 20m clean, 50m dirty
    gr = np.zeros_like(depth, dtype=float)
    gr[0:20] = 30      # Clean
    gr[20:22] = 120    # Dirty (Thin - 2m)
    gr[22:42] = 30     # Clean
    gr[42:100] = 100   # Dirty (Thick)

    # Add minor noise
    np.random.seed(42)
    gr += np.random.normal(0, 1, size=len(gr))

    # Run pipeline with 5m minimum interval
    result = run_gr_cognitive_pipeline(
        depth,
        gr_array=gr,
        min_interval_m=5.0,
    )

    intervals = result["interval_table"]
    print(f"\nExtracted {len(intervals)} intervals:")
    for i in intervals:
        print(f"  {i['Top_MD']} - {i['Base_MD']} ({i['Thickness']}m): {i['Motif']}")

    # Validation
    assert len(intervals) >= 1
    for i in intervals:
        assert i["Thickness"] >= 4.99, f"Interval {i['Top_MD']} is too thin: {i['Thickness']}m"

    print("\n✅ Verification PASSED: All intervals meet the 5m Human-Scale Law.")


if __name__ == "__main__":
    try:
        test_gr_cognitive_merging()
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
