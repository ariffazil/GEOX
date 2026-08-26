# Upstream Map Ingestion Proposal: Geological Map of Malaysia (JMG 1:500,000)

**To:** Prof. Shanan Peters, Dr. Daven Quinn & The Macrostrat Team (University of Wisconsin–Madison)  
**From:** Muhammad Arif bin Fazil (Exploration Geoscientist, PETRONAS Subsurface Alum & arifOS Federation Architect)  
**Date:** 2026-08-26  
**Last Updated:** 2026-08-26T09:08:00+08:00 (v1.2 — Section 6 maintainer questions added & source envelope verified)  
**Target Repository:** `https://github.com/UW-Macrostrat/macrostrat` (Macrostrat Ingestion Track)  
**Subject:** High-Resolution Map Ingestion Submission: National Geological Map of Malaysia (JMG 1:500k Bedrock & Major Faults)

---

## 1. Executive Summary & Geoscientific Rationale

Currently, Macrostrat's global coverage over Southeast Asia and Malaysia is largely derived from generalized global compilations (e.g., Chorlton 1998 1:25M global bedrock layer) and localized memoirs.

This submission provides the complete, authoritative, official national geoscientific dataset from the **Department of Mineral and Geoscience Malaysia (Jabatan Mineral dan Geosains Malaysia - JMG)** under the **MyGEMS** National Geospatial Framework:
* **Nominal Scale:** 1:500,000 (Medium/Regional Scale).
* **Coverage:** All 14 States of Malaysia across Sundaland (Peninsular Malaysia) and Borneo (Sabah and Sarawak), covering the national terrestrial extent (~330,803 km²).
* **Structural Lineaments:** Suture zones, major shear systems, and thrust faults (Bentong-Raub Suture, Bukit Tinggi Fault, Bok Bak Fault, Lupar Line, Crocker Fold-Thrust Belt).
* **Spatial Reference:** EPSG:4326 (WGS84) Geodetic / Web Mercator EPSG:3857.

---

## 2. Source Metadata & Open Access Provenance

* **Source Name:** Geological Map of Malaysia (1:500k JMG National Series)
* **Publishing Agency:** Jabatan Mineral dan Geosains Malaysia (JMG)
* **Primary Web Portal:** `https://mygems.jmg.gov.my/portal/apps/webappviewer/index.html?id=90702a483ab6489bbaab210e038c2ed9`
* **GIS Service Endpoint:** `https://mygems.jmg.gov.my/server/rest/services/Demarcation/Litology_by_Negeri/MapServer`
* **Structural Fault Service:** `https://mygems.jmg.gov.my/server/rest/services/GeologiAsas/Major_Fault/MapServer/5`
* **Licensing:** Open Government Data (Malaysia) / Public Domain Geoscience / CC-BY 4.0 Compatible.
* **Bounding Box:** `[99.5, 0.8, 119.5, 7.5]` (WGS84 Lat/Lng).

---

## 3. Stratigraphic Architecture & Lexicon Concordance

The dataset is subdivided into key geotectonic domains:

1. **Western Peninsular Belt (Sibumasu Terrane / Gondwana-derived):**
   - *Machinchang Formation* (Cambrian quartzites & sandstones)
   - *Setul / Singa Formations* (Ordovician-Permian diamictites & limestones)
   - *Main Range Granite* (Late Triassic S-type peraluminous tin granites)
2. **Central Belt & Suture Zone (Paleo-Tethys Closure):**
   - *Bentong-Raub Suture Ophiolites* (Devonian-Carboniferous serpentinite, chert, melange)
   - *Semantan Formation* (Triassic flysch turbidites)
3. **Eastern Peninsular Belt (East Malaya / Indochina Affinity):**
   - *Kenyir & Kapal Granites* (Permian-Triassic I-type calc-alkaline magmatism)
   - *Kuantan Basalts* (Quaternary intraplate volcanism)
4. **Northwest Borneo & Sabah Orogeny:**
   - *Crocker & Trusmadi Formations* (Eocene-Oligocene deepwater turbidite prism)
   - *Kinabalu Pluton* (10-7 Ma Late Miocene granite adamellite)
5. **Sarawak & Rajang Flysch:**
   - *Belaga Formation* (Cretaceous-Eocene Rajang accretionary wedge)
   - *Lupar Melange & Central Luconia Carbonates* (Miocene build-ups)

---

## 4. Integration Artifacts & Manifest

1. `macrostrat_ingestion_manifest.json`: Standardized Macrostrat Source & Layer mapping specification.
2. `jmg_malaysia_states_summary.json`: Detailed 14-state layer catalog with verified ArcGIS Server endpoints and bounding extents.
3. `export_jmg_macrostrat.py`: Automated GIS vector extractor script formatting all 14 state layers into Macrostrat GeoPackage/Shapefile schema with clean topological boundary resolution.

---

## 5. Contact & Coordination

* **Submitter:** Muhammad Arif bin Fazil
* **Email:** `arif@arif-fazil.com`
* **Canonical Web Surface:** `https://arif-fazil.com/earth/macrostrat-ingestion/`
* **Upstream Submission:** Intended for submission as an Issue on [UW-Macrostrat/macrostrat](https://github.com/UW-Macrostrat/macrostrat/issues).

---

## 6. Schema & Pipeline Coordination Questions for Maintainers

1. **Target Ingestion Specification**: What is the Macrostrat team's preferred table structure / GeoPackage schema for contributor-submitted national vector datasets? (We have currently mapped fields into `jmg_bedrock_lithology` and `jmg_major_faults` layers under standard `source` envelope).
2. **Lithology Dictionary Alignment**: Are there specific lithological vocabularies or strat name IDs in the Macrostrat dictionary you would like us to pre-match against before merging?
3. **Delivery Mechanism**: We can provide either a direct PostGIS dump, merged GeoPackage (.gpkg), or automated REST harvesting scripts against JMG MyGEMS endpoints.
