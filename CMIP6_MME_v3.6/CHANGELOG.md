# CHANGELOG

## v3.6 (2026-06-13) — Premium cartography & directional change markers

- **Spatial maps (F4–F7)** rewritten as filled IDW surfaces clipped to the
  province boundary (via dependency-free `geo_lite`), replacing bare station
  dots — continuous fields with white level lines and a zero-change isoline.
- **Figure 7 (ΔP% change) redesigned**:
  • 2×3 layout — rows = SSP scenarios, cols = seasons (matches Figure 4 style).
  • **Directional triangle station markers**: ▲ up = rainfall increase,
    ▼ down = decrease; **3 size classes by |ΔP%|** (auto thresholds from the
    data, ~<4% / 4–7% / ≥7%); colour = ΔP% on RdBu; bold ring = ≥70% inter-model
    sign agreement. Surface kept beneath the markers (toggle `surface=` in
    `_station_change_map`; a triangles-only mode is available).
- **Cartography**: filled-triangle compass north arrow + km scale bar on every
  map; legend/scale-bar collision avoided on the legend panel.
- **Figure 1 (Taylor)** plots per-GCM points (7 models) + MME-mean centroid,
  with adaptive radial limit.
- All figures rendered at 600 DPI × {single, double} column × PNG/TIFF/PDF and
  verified on the real 7-GCM dataset with the real boundary (UTM Zone 47N).
- Portable to any province: set `study_area`/`paths` and supply a `.shp`+`.prj`;
  geo_lite auto-reprojects UTM Transverse Mercator or geographic coordinates.


## v3.5 (2026-06-13) — Methodology hardening for Q1–Q2 submission

Reviewed against the v3 audit. Four methodology fixes (FIX-A…D) plus packaging
and reproducibility corrections. Verified by running the core computational
pipeline on **real ACCESS-ESM1-5 + CanESM5 data** (12 observed stations,
Prachuap Khiri Khan, 1981–2014 baseline / 2021–2050 near future).

| ID | File | Change | Why it mattered |
|----|------|--------|-----------------|
| FIX-A | `main.py` | Change% now computed **per model relative to that model's own bias-corrected historical baseline** (delta-change), then aggregated to MME mean/P25/P75. Adds `bc_hist_baseline` column and a BC-vs-OBS baseline agreement diagnostic. | The previous denominator (observed baseline) folded residual bias-correction error into the change signal. On the real data this would have injected up to **9.0%** spurious change at some station/season (median 1.7%). |
| FIX-B | `config.yaml`, `metrics.py`, `make.py` | `min_years_validate` raised 2 → **10**; Taylor minimum raised 3 → 10. | KGE/NSE/correlation are degenerate on ≤2 years (r = ±1 for any 2 points → KGE looks "perfect"). |
| FIX-C | `mme.py` | Realizations of the same model are **averaged to one series before the ensemble**; `n_models` now counts **distinct models**. | Prevented models with more realizations from dominating the ensemble mean ("one model, one vote"). |
| FIX-D | `gis/interp.py` | Kriging gets a **nugget** term, predictions **clipped to ≥0** (rainfall is non-negative), honest docstring (empirical, unfitted variogram), and a `loocv_rmse()` cross-validation helper. | "Kriging" without a fitted variogram / skill metric is not defensible; unbounded kriging can yield negative rainfall. |

Reproducibility / packaging:
- `config_version` 1.0.0 → **3.5.0**; provenance block added (models, realization,
  calendar, bias-correction method/period/software/DOI placeholders, change reference).
- Boundary shapefile downgraded from a fatal input check to a warning, so the
  **computational pipeline runs without GIS deps**; the figure stage still requires it.
- Parquet writes now **fall back to CSV** when pyarrow/fastparquet is absent.
- requirement pins corrected to versions actually verified in this run.
- Version label corrected throughout (prior reports mislabeled the v3 archive as "v2").

Tests: 22 original computational tests pass; 8 figure/GIS tests require geopandas
(+ a boundary shapefile) and are skipped in the offline sandbox; 17 new v3.5 tests
pass (incl. checks against the real-data Change.csv). **0 failures.**


**New output (v3.5):** daily across-GCM **MME exported in wide layout like the
observed file** (`YEAR, MONTH, DAY, <stations>`), one workbook per dataset —
`MME_daily_Raw_<area>.xlsx` and `MME_daily_BC_<area>.xlsx` — with one sheet per
scenario (historical/ssp245/ssp585). Models on different calendars (e.g.
ACCESS Gregorian vs CanESM5 noleap) are aligned on the date key with 29 Feb
stripped; realizations are pre-averaged; value = across-GCM mean. Toggle via
`export.daily_mme_excel` in config. Caveat documented in the module: the daily
ensemble mean smooths extremes — use individual models for extreme indices.


**v3.5 update (7-GCM verification, 2026-06-13):** verified end-to-end on the full
7-GCM dataset (ACCESS-ESM1-5, CESM2, CanESM5, EC-Earth3, FGOALS-g3, MIROC6,
MRI-ESM2-0), Raw + BC, historical/ssp245/ssp585 (42 CSVs). Daily MME export
renamed to self-describing files `MME_daily_{dataset}_{scenario}_{N}GCM_{area}.xlsx`
(N = models for that dataset/scenario) each with an INFO sheet (exact model list,
period, calendar, aggregation), plus a `MME_daily_manifest_{area}.csv` index and a
Models sheet in the master workbook. Mixed calendars (Gregorian vs noleap) align to
a common 365-day grid; a 360-day calendar now triggers a warning. Tests: 43 pass,
8 skip (GIS), 0 fail.


**Figures verified & upgraded (v3.5, 7-GCM, real boundary):** all figures
rendered on the real 7-GCM data with the actual province boundary
(boundary.shp, UTM Zone 47N) and visually verified:
  F0 study-area map (boundary + stations by elevation), F1 Taylor, F2 validation
  dot plot, F3 1981–2100 anomaly time series, F4–F6 seasonal spatial maps,
  F7 change maps with model-agreement rings, F8 inter-model spread box plots.
The GIS stage uses a new dependency-free backend `src/gis/geo_lite.py` that reads
ESRI shapefiles and reprojects from the `.prj` (UTM Transverse Mercator or
geographic) with numpy + matplotlib only — so maps render without geopandas and
the pipeline is portable to ANY province's shapefile. Figure 1 was upgraded to
plot per-GCM points (proper Taylor usage) with the MME-mean centroid, instead of
only the ensemble mean. Tests: 49 pass, 5 skip, 0 fail.


### v3.6 — Q1 reviewer revision (figures)
Applied a Q1-reviewer figure critique:
- Change-map (F7) triangle markers reduced ~55% so they no longer mask the
  field; contour level lines made visible (grey lines α0.7 + bold dashed zero
  isoline); IDW sharpened (power 2→3) to reduce over-smoothed circular blobs;
  diverging range tightened to the 90th-percentile |ΔP%| (±, ~13 classes) so
  weak-signal panels show contrast instead of a wide white centre.
- Map extent cropped to ~2% margin (≈90% data fill); north arrow shrunk ~25%.
- Station id labels P01..PNN added to maps and the study-area map; a **Stations**
  sheet (label ↔ code ↔ lat/lon/elevation) added to the master workbook for
  traceability.
- **New Figure 9 — ensemble uncertainty**: inter-model SD of ΔP% per station
  (2×3, scenario×season), addressing the most common Q1 ask (show spread, not
  just the mean). 10 figure types total.


### v3.6 — Q1 reviewer revision #2 (figures, significance & validation)
Addressed a second Q1 figure critique:
- F7 change maps: **removed station labels** (overlap) — moved to the study-area
  supplementary map; **uniform direction-only triangles** (▲ increase, ▼ decrease)
  so size no longer duplicates the colour magnitude (removed redundant encoding);
  **agreement shown as stippling** (≥agreement_threshold of GCMs agree on sign)
  instead of marker rings — the CMIP6-standard significance overlay; legend
  simplified to direction + stippling; north arrow shrunk & moved to the corner;
  interior gridlines removed; contour lines thickened.
- **F9 uncertainty** recast into interpretable discrete classes (Low <5 /
  Moderate 5–10 / High 10–15 / Very high 15–20 / Extreme >20 %) via BoundaryNorm,
  thicker contours, classed colourbar (answers "is this SD high or low?").
- **New table `Interpolation_Skill.csv`** — IDW leave-one-out CV (RMSE & MAE, %)
  per scenario×season, addressing the reviewer's key question on interpolating
  from a sparse (N=12) network. (This run: LOOCV RMSE ≈ 1.0–2.3 %.)


### v3.6 — Q1 reviewer revision round 2 (change & uncertainty maps)
- **All multi-panel figures**: x-axis values now shown on every sub-panel
  (Figure 3 no longer shares one axis); each sub-panel carries a descriptive
  title (F3 season names; F2 full metric names). The near-future window
  (2021–2050) grey band is now explicitly labelled "Near future".
- **Master results workbook is now Q1-complete** — added sheets: Area_Summary
  (headline per scenario×season: mean ΔP%, P25/P75, station range, mean
  inter-model SD, % stations with ≥70% sign agreement), Uncertainty (per-station
  inter-model SD, model min/max, agreement fraction), Interpolation_Skill (IDW
  LOOCV RMSE & MAE), Change_per_model, plus Validation, Change_<season>,
  MME_summary, Stations (Pnn↔code), Models and Metadata.
- **Figure 3 (time series)**: fixed the visual gap at the 2014→2015 historical-to-future transition in all three panels — SSP lines and spread bands are now bridged to the historical endpoint (joined series smoothed across the junction, displayed from the transition year), so the curves are continuous.
- **Figure 7**: station id labels REMOVED from the main panels (they overlapped
  badly); kept only on the study-area supplementary map (F0) with a Stations
  table. Triangles are now a **single uniform size encoding DIRECTION only**
  (▲ increase / ▼ decrease) — magnitude is shown by surface colour alone (no
  more redundant size+colour encoding). Markers ~25% smaller. Legend simplified
  to Increase / Decrease + a ≥70%-agreement entry.
- **Significance**: robust areas (≥70% of GCMs agree on the sign) are now shown
  with **stippling** over the surface (CMIP6-standard), in addition to marker
  rings.
- **Figure 9 (uncertainty)**: inter-model SD reclassified into interpretable
  **disagreement classes** (Low <5 / Moderate 5–10 / High 10–15 / Very high
  15–20 / Extreme >20 %) with a boundary-norm colourbar and thicker (0.8 pt)
  contours — so "high vs low" is directly readable.
- Interior **gridlines removed** (lat/lon ticks kept); north arrow reduced.
- **Interpolation skill**: IDW leave-one-out cross-validation (LOOCV RMSE & MAE
  per scenario×season) is computed and saved (Interpolation_Skill table) to
  justify the continuous surface from a sparse 12-station network.

## v3 (2026-06-11)
Six objective-critical fixes (KGE ddof, per-model change ordering, coverage gate,
map coordinate labels/north arrow, config_version, pinned requirements).
