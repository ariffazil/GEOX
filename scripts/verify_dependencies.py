import json

from geox.core.dependency_engine import DependencyEngine
from geox.core.hierarchy import GeologicalRisk, Prospect, Segment


def test_dependency():
    print("--- TESTING WAJIB #2 & #3: HIERARCHY & DEPENDENCY ---")
    
    # 1. Create Segments
    # Both segments have Source=0.5 risk.
    risk = GeologicalRisk(source=0.5, reservoir=0.8, trap=0.8, seal=0.8)
    
    seg1 = Segment(id="S1", name="Lower Reservoir", risk=risk, volumetrics={"p50": 100})
    seg2 = Segment(id="S2", name="Upper Reservoir", risk=risk, volumetrics={"p50": 100})
    
    # 2. Create Prospect
    prospect = Prospect(id="P-01", name="Alpha Prospect")
    prospect.add_segment(seg1)
    prospect.add_segment(seg2)
    
    # 3. Roll up with DependencyEngine
    result = DependencyEngine.rollout_prospect_probabilistic(prospect)
    
    print(f"Prospect: {prospect.name}")
    print(f"Segment GCOS: {seg1.risk.gcos:.4f}")
    print(f"Combined GCOS (with Shared Source/Seal): {result['gcos']:.4f}")
    
    # 4. Independent Math for comparison:
    # P(Success) = 1 - P(Fail_both)
    # P(Fail) = 1 - 0.256 = 0.744
    # P(Fail_both) = 0.744 * 0.744 = 0.553
    # P(Success_indep) = 1 - 0.553 = 0.446
    
    print("Independent Math Result would be ~0.446")
    print(f"Shared Logic Result (Simulated): {result['gcos']}")
    
    # If Shared Source is used, the combined GCOS should be LOWER than independent 
    # if the source failure kills both.
    
    print("\nFull Result Payload:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_dependency()
