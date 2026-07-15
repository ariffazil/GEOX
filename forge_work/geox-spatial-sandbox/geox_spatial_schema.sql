-- geox_spatial_schema.sql
-- Phase 2.2: GEOX Spatial Memory Genesis
-- Location: /root/geox/forge_work/geox-spatial-sandbox/
-- Status: ARTIFACT — execute after docker-compose up -d

-- Enable PostGIS engine
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- ─────────────────────────────────────────────
-- CORE TABLES
-- EPSG:4326 enforced. Z dimension for depth.
-- All geometry stored as MULTILINESTRINGZ / POLYGON / POINTZ
-- ─────────────────────────────────────────────

-- geox_well_surveys
-- 1D measured-depth trajectories → 3D wellbore path
CREATE TABLE IF NOT EXISTS geox_well_surveys (
    well_id        VARCHAR(100) PRIMARY KEY,
    well_name      TEXT NOT NULL,
    trajectory     GEOMETRY(MULTILINESTRINGZ, 4326) NOT NULL,
    metadata       JSONB,
    crs            INTEGER DEFAULT 4326,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_well_surveys_geom ON geox_well_surveys USING GIST (trajectory);
CREATE INDEX idx_well_surveys_name ON geox_well_surveys (well_name);

COMMENT ON TABLE geox_well_surveys IS '1D measured-depth → 3D wellbore trajectories. Z = TVDSS metres.';

-- geox_seismic_lines
-- 2D navigation tracks (surface projection)
CREATE TABLE IF NOT EXISTS geox_seismic_lines (
    line_id        VARCHAR(100) PRIMARY KEY,
    survey_name    TEXT,
    navigation     GEOMETRY(MULTILINESTRING, 4326) NOT NULL,
    metadata       JSONB,
    crs            INTEGER DEFAULT 4326,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_seismic_lines_geom ON geox_seismic_lines USING GIST (navigation);

COMMENT ON TABLE geox_seismic_lines IS '2D seismic line navigation tracks. Surface XY only.';

-- geox_seismic_volumes
-- 3D survey footprints (polygon outline + time/depth range)
CREATE TABLE IF NOT EXISTS geox_seismic_volumes (
    volume_id      VARCHAR(100) PRIMARY KEY,
    survey_name     TEXT,
    footprint      GEOMETRY(POLYGON, 4326) NOT NULL,
    z_min          FLOAT,   -- time (ms) or depth (m) base
    z_max          FLOAT,   -- time (ms) or depth (m) top
    metadata       JSONB,
    crs            INTEGER DEFAULT 4326,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_seismic_volumes_geom ON geox_seismic_volumes USING GIST (footprint);

COMMENT ON TABLE geox_seismic_volumes IS '3D seismic volume footprints with z range.';

-- geox_basin_polygons
-- Structural/basin boundary polygons
CREATE TABLE IF NOT EXISTS geox_basin_polygons (
    basin_id       VARCHAR(100) PRIMARY KEY,
    basin_name     TEXT NOT NULL,
    boundary       GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    metadata       JSONB,
    crs            INTEGER DEFAULT 4326,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_basin_polygons_geom ON geox_basin_polygons USING GIST (boundary);

COMMENT ON TABLE geox_basin_polygons IS 'Structural/basin boundary polygons.';

-- geox_horizon_grids
-- Raster horizon surfaces (continuous gridded data)
CREATE TABLE IF NOT EXISTS geox_horizon_grids (
    horizon_id     VARCHAR(100) PRIMARY KEY,
    horizon_name   TEXT NOT NULL,
    surface        RASTER NOT NULL,
    metadata       JSONB,
    crs            INTEGER DEFAULT 4326,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_horizon_grids_rast ON geox_horizon_grids USING GIST (st_convexhull(surface));

COMMENT ON TABLE geox_horizon_grids IS 'Gridded horizon surfaces as PostGIS raster.';

-- ─────────────────────────────────────────────
-- READ-ONLY ROLE FOR MCP AGENTS
-- Hard statement timeout prevents Cartesian death
-- ─────────────────────────────────────────────

CREATE ROLE IF NOT EXISTS geox_mcp_read;
GRANT CONNECT ON DATABASE geox_spatial TO geox_mcp_read;
GRANT USAGE ON SCHEMA public TO geox_mcp_read;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO geox_mcp_read;
ALTER ROLE geox_mcp_read SET statement_timeout = '10s';
ALTER ROLE geox_mcp_read SET default_transaction_read_only = ON;

-- Separate write role (for ingestion pipeline, not MCP agents)
CREATE ROLE IF NOT EXISTS geox_admin_write;
GRANT ALL ON DATABASE geox_spatial TO geox_admin_write;
GRANT ALL ON SCHEMA public TO geox_admin_write;
GRANT ALL ON ALL TABLES IN SCHEMA public TO geox_admin_write;
ALTER ROLE geox_admin_write BYPASSRLS;

-- ─────────────────────────────────────────────
-- PROVENANCE & AUDIT COLUMNS (F11)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS geox_data_provenance (
    record_id      SERIAL PRIMARY KEY,
    table_name     TEXT NOT NULL,
    record_key     TEXT NOT NULL,
    source_file    TEXT,
    source_hash    TEXT,
    ingestion_ts   TIMESTAMPTZ DEFAULT NOW(),
    agent_id       TEXT,
    method         TEXT  -- 'osm2pgsql_flex', 'las_ingest', 'manual'
);
CREATE INDEX idx_provenance_table ON geox_data_provenance (table_name);
