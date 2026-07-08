from geox_mcp.surface_migration import (
    LEGACY_ALIAS_ROUTE_MAP,
    LEGACY_SURFACE_ROUTE_MAP,
    SUPPORTED_TOP_LEVEL_MODES,
    audit_surface_migration,
)


def test_all_legacy_capabilities_have_unified_routes():
    errors = audit_surface_migration()
    assert not errors, "surface migration audit failed:\n" + "\n".join(errors)


def test_routes_target_supported_top_level_modes():
    for route_map in (LEGACY_SURFACE_ROUTE_MAP, LEGACY_ALIAS_ROUTE_MAP):
        for legacy_name, route in route_map.items():
            assert route.mode in SUPPORTED_TOP_LEVEL_MODES[route.tool], (
                f"{legacy_name} routes to unsupported mode {route.tool}:{route.mode}"
            )


def test_fossilization_scope_counts_stable():
    assert len(LEGACY_SURFACE_ROUTE_MAP) == 81
    assert len(LEGACY_ALIAS_ROUTE_MAP) == 50
