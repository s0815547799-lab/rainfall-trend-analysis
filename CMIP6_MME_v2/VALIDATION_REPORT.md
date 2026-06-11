# VALIDATION REPORT — CMIP6_MME_v2

**Date**: 2026-06-11  
**Python**: 3.11.15  
**config_version**: 1.0.0

---

## Test Execution Summary

| Suite | Tests | Passed | Failed | Skipped |
|-------|------:|-------:|-------:|--------:|
| `tests/test_all_fixes.py` | 26 | 26 | 0 | 0 |
| `tests/test_pipeline_smoke.py` | 4 | 4 | 0 | 0 |
| **Total** | **30** | **30** | **0** | **0** |

---

## Test Coverage by Module

| Module | Tests | Status |
|--------|-------|--------|
| `src/rainfall/seasonal.py` | 5 (dry-season hydrological year, NaN gate, completeness) | PASS |
| `src/validation/metrics.py` | 6 (KGE perfect/flat/short, ΔKGE column, common-years) | PASS |
| `src/utils/io.py` | 6 (CSV parsing upper/lower case, metadata case-insensitive) | PASS |
| `src/figures/make.py` | 4 (collect_panel_data, Taylor checks, no stub) | PASS |
| `src/figures/base.py` | 2 (auto_color_range empty, free_corner north/south) | PASS |
| `final_run.py` | 2 (TIFF in QC, QC fails with no rasters) | PASS |
| `src/gis/interp.py` | 1 (importable) | PASS |
| `src/ensemble/mme.py` | 1 (importable) | PASS |
| `src/tables/results.py` | 1 (importable) | PASS |
| **Pipeline (end-to-end)** | 4 (generate_all, figure count, DPI=600, QC gate) | PASS |

---

## Scientific Standards Verification

| Requirement (CLAUDE.md) | Status | Evidence |
|------------------------|--------|---------|
| §12.5 Change% per-model first, then MME aggregate | ✅ Fixed | FIX-02; `main.py` computes from `per` DataFrame |
| §12.5 CMIP6 model period coverage validated | ✅ Fixed | FIX-03; exclusion logic with WARNING log |
| §12.8 NaN-safe percentiles in `build_mme()` | ✅ Already correct | `lambda s: float(np.percentile(s.dropna(), q)) if s.notna().any() else np.nan` |
| §12.8 MME stats: mean, median, P25, P75, n_models | ✅ Already correct | `build_mme()` returns all five columns |
| §12.9 Maps: coordinate labels or graticule | ✅ Fixed | FIX-04; WGS84 lon/lat tick labels added |
| §12.9 Maps: north arrow | ✅ Fixed | FIX-04; `_add_north_arrow()` on every map panel |
| §12.9 Anomaly baseline over baseline period only | ✅ Already correct | `fig3_timeseries()` uses `obs[(obs.year >= bl0) & ...]` |
| §12.10 KGE uses sample std (ddof=1) | ✅ Fixed | FIX-01; value numerically unchanged (α ratio) |
| §12.10 ΔKGE absolute difference column | ✅ Already correct | `df["ΔKGE"] = (df.KGE_BC - df.KGE_Raw)` |
| §12.10 Three-way common-year sample for metrics | ✅ Already correct | `idx = oo.index.intersection(rs.index).intersection(bs.index)` |
| §12.10 std=NaN for n=1 stations | ✅ Already correct | `_stat_block()` returns NaN when `a.size <= 1` |
| §12.11 `config_version` in config.yaml | ✅ Fixed | FIX-05; logged in pipeline output |
| §12.11 `requirements.txt` with pinned versions | ✅ Fixed | FIX-06; exact versions pinned |
| §12.11 Random seed documented | ✅ N/A | No Monte Carlo in CMIP6_MME_v2 |

---

## Figure Output Verification (Smoke Test)

- All 7 figure functions execute without error on synthetic 4-station dataset
- All PNG files carry DPI metadata = 600 ✅
- PDF files generated alongside PNG and TIFF ✅
- Figure QC gate (`figure_qc()`) reports PASS ✅
- Both single-column (3.5″) and double-column (7.2″) widths rendered ✅
- Maps include coordinate tick labels (WGS84) and north arrow ✅

---

## Known Limitations (Not Blockers for Q1)

| Item | Notes |
|------|-------|
| Scale bar on maps | Functional north arrow present; true scale bar (km) requires projected CRS computation. Acceptable for station-scatter maps with coordinate tick labels per §12.9 "or". |
| Taylor diagram uses Annual season only | Standard practice; not a limitation. |
| Bias correction method/citation | Must be added to manuscript §2 before submission (not a code issue). |
| CMIP6 calendar type documentation | Must be added to manuscript §2 for each model (not a code issue). |
