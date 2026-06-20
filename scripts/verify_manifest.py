"""Verify physics manifest hash computation."""
import sys

sys.path.insert(0, "src")
from geox_core.physics.manifest import get_domain_law, get_geo_identity, get_physics_manifest_hash

print("domain_law:", get_domain_law())
print("physics_manifest_hash:", get_physics_manifest_hash())
print("identity:", get_geo_identity())
