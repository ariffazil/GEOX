# DEMO LAS — SABAH BASIN, SANDAKAN FORMATION

**NOT REAL FIELD DATA. FOR TESTING ONLY.**

---

## Well Information

| Field | DEMO_WELL_A | DEMO_WELL_B |
|---|---|---|
| **Basin** | Sabah (North Borneo Trough) | Sabah (North Borneo Trough) |
| **Formation** | Sandakan Fm (Late Miocene–Pliocene) | Sandakan Fm (Late Miocene–Pliocene) |
| **Depth Range** | 1200–2500 mMD | 1235–2565 mMD |
| **Lithology** | Prodelta to deltaic clastics | Prodelta to deltaic clastics |
| **Status** | DEMO — synthetic | DEMO — synthetic |
| **Original Name** | BOKOR_1_demo.las | BOKOR_2_demo.las |

## Why These Are NOT Real

| Indicator | What It Shows |
|---|---|
| LAS `CLAIM = EXPLORATORY_VISUALIZATION` | Self-disclosed synthetic |
| Identical interval thicknesses (180/140/160/110/160 m) in both wells | Geometrically impossible in real deltaic geology |
| Uniform 35 m structural offset across all tops | No real structural dip — synthetic artifact |
| GR values uniformly high (~88–115 API) with no clean-sand motif | Real Sandakan delta-front shows coarsening-upward GR with clean tops |
| No well operator, license, or country metadata | Synthetic placeholder |

## Geological Context

The **Sandakan Formation** is the primary offshore reservoir target in Sabah Basin:
- **Age:** Late Miocene–Pliocene (12–2.6 Ma)
- **Depositional environment:** Prodelta to deltaic clastics, prograding from the north
- **Reservoir quality:** φ 0.15–0.28, k 100–2000 mD (best in upper delta-front and distributary channels)
- **Seal:** Interbedded prodelta shales (variable)
- **Play type:** Structural traps on Miocene inversion anticlines

These demo wells were constructed to approximate the Sandakan depth window but do **not** represent real reservoir facies, fluid contacts, or petrophysical properties.

## Allowed Use

- LAS parsing and schema validation tests
- Plotting and visualization demos
- Well-log display development

## NOT Allowed

- Petrophysical analysis (Vsh, φ, Sw calculations)
- GCoS or prospect evaluation
- Publication or reference as "real Sabah data"
- Any exploration or investment decision

## Disposition

Relocated from `/root/geox/fixtures/` on 2026-06-25 by `FORGE-000_INIT`
per sovereign directive from Arif. Original names (`BOKOR_1_demo.las`,
`BOKOR_2_demo.las`) were misleading — "Bokor" is a real PETRONAS field
in offshore Sabah.

**Restore:** `mv /root/geox/fixtures/_DEMO_SYNTHETIC/*.las /root/geox/fixtures/`

---

*DITEMPA BUKAN DIBERI*
