# FINAL RELEASE REPORT — CMIP6_MME_v3.6

**Date**: 2026-06-13  
**config_version: 3.6.0  
**Test result**: 39 passed / 0 failed / 8 skipped (figure-GIS, optional deps)

---

## Summary

v3.5 closes the methodology issues identified in the v3 audit that a Q1–Q2
reviewer would most likely challenge, and validates the corrected pipeline on
**real CMIP6 data** (ACCESS-ESM1-5 + CanESM5, Prachuap Khiri Khan, 12 stations).

Blocker-level fixes:
- **FIX-A** — projected change is now a per-model delta against each model's own
  bias-corrected historical baseline, then aggregated (not against the observed
  mean). A built-in diagnostic reports BC-historical vs observed agreement so the
  reference choice is auditable (this run: median 1.7%, max 9.0%).
- **FIX-B** — validation minimum sample raised to 10 years (was 2), removing the
  degenerate short-sample KGE = ±1 artifact.

Major fixes:
- **FIX-C** — realizations averaged per model before the ensemble; `n_models`
  counts distinct models.
- **FIX-D** — kriging gets a nugget, non-negative clipping, an honest
  (empirical/unfitted) variogram docstring, and a LOOCV skill helper.

Reproducibility: config_version: 3.6.0 + provenance block; optional-Parquet
(CSV fallback); boundary made non-fatal for computation; pins corrected to
tested versions; version label corrected (v3 archive had been mislabeled "v2").

---

## What is verified vs. what remains

**Verified here (real data):** seasonal aggregation, MME construction,
KGE/NSE/PBIAS validation, change% — all run end-to-end and produce coherent
results (BC improves KGE and cuts |PBIAS| to 1–5%; Annual drying −6.7% SSP245,
−13.9% SSP585, stronger under higher forcing).

**Not run in this sandbox (requires geopandas + boundary shapefile):** the
figure/GIS stage (`final_run.py`, `src/figures/make.py`, `src/gis/interp.py`
surfaces) and the figure-QC gate. The code is reviewed and unit-skip-guarded;
rerun in a full environment before submission.

---

## Pre-submission checklist (manuscript actions — NOT code)

- [ ] Fill `provenance.bias_correction` (method, software+version, data DOI) in config + §2
- [ ] Justify the two-GCM ensemble (or add models); disclose CanESM5 has no Raw
- [ ] Document CMIP6 calendar handling (data here is Gregorian — verified)
- [ ] State equal model weighting and any model-family redundancy
- [ ] Justify the 1981–2014 baseline window
- [ ] Run the figure/GIS stage with the boundary shapefile and pass figure-QC

---

## Honest scope note

This release makes the pipeline methodologically defensible and reproducible on
real data. It does **not**, and cannot, guarantee journal acceptance: that
depends on the scientific framing, the manuscript, and peer review. The two-GCM
ensemble in particular is a demonstration-scale ensemble and should be expanded
or explicitly framed.
