# FINAL RELEASE REPORT — CMIP6_MME_v2

**Date**: 2026-06-11  
**config_version**: 1.0.0  
**Python**: 3.11.15  
**Test result**: 30/30 PASS

---

## Release Summary

CMIP6_MME_v2 reviewed and corrected. No remaining objective-critical issues identified.

Six objective-critical issues were identified through systematic code review against
the CLAUDE.md mandatory scientific standards and corrected before this release:

| ID | File | Issue | Category |
|----|------|-------|----------|
| FIX-01 | `src/validation/metrics.py` | KGE `ddof=0` → `ddof=1` (§12.10 mandate) | Statistical correctness |
| FIX-02 | `main.py` | Change% computed from MME mean instead of per-model (§12.5) | CMIP6 methodology |
| FIX-03 | `main.py` | No CMIP6 model period coverage validation; partial-coverage models silently included (§12.5) | Data quality gate |
| FIX-04 | `src/figures/make.py` | Geographic maps missing coordinate labels and north arrow (§12.9) | GIS figure standard |
| FIX-05 | `config/config.yaml` | Missing `config_version` field (§12.11) | Reproducibility |
| FIX-06 | `requirements.txt` | Dependencies not pinned; `>=` specifiers only (§12.11) | Reproducibility |

---

## Pre-Release Checklist

### Statistical Correctness
- [x] KGE: `ddof=1` (sample std) — FIX-01
- [x] ΔKGE: absolute difference column present
- [x] Three-way common-year intersection for validation metrics
- [x] NaN-safe percentiles in `build_mme()`
- [x] Change% computed per-model first, then MME aggregated (mean/P25/P75) — FIX-02
- [x] CMIP6 model period coverage validated before inclusion — FIX-03

### Data Quality
- [x] 80% completeness gate applied to Annual, Wet, Dry scales
- [x] All-NaN seasons produce NaN (not 0.0)
- [x] Leap days stripped for consistent expected-day counts

### Figures
- [x] 600 DPI — verified in smoke test
- [x] Serif font (Times New Roman / Liberation Serif / DejaVu Serif)
- [x] No top/right spines
- [x] Maps: WGS84 coordinate tick labels — FIX-04
- [x] Maps: north arrow on every panel — FIX-04
- [x] Anomaly baseline uses observed data filtered to baseline period only
- [x] Bubble/scatter maps: diverging RdBu for change, YlGnBu for absolute values

### CMIP6 Processing
- [x] Models with partial period coverage excluded with WARNING log — FIX-03
- [x] `ssp_timeseries_start` separates historical from SSP load windows
- [x] Dry-season hydrological year convention: Nov(Y)+Dec(Y)+Jan–Apr(Y+1) = Y+1

### Reproducibility
- [x] `config_version: "1.0.0"` in `config.yaml`, logged at pipeline start — FIX-05
- [x] `requirements.txt` with all packages pinned to tested versions — FIX-06
- [x] Timestamped release directories (`RELEASE_{area}_{YYYYMMDD_HHMMSS}`)
- [x] `CURRENT_RELEASE` symlink updated only on QC-PASS
- [x] Parquet intermediate files for pipeline resume

### Still Requiring Manuscript Action (Not Code Issues)
- [ ] Bias correction method, reference period, software version, and archived data DOI in manuscript §2
- [ ] CMIP6 calendar type documented per model in manuscript §2
- [ ] Equal model weighting and family redundancy acknowledged in methods
- [ ] Random seed (if Monte Carlo added in future) documented as 42

---

## Test Results

```
tests/test_all_fixes.py     26 passed
tests/test_pipeline_smoke.py  4 passed
Total: 30/30 PASS
```

---

## Pipeline Architecture (Unchanged)

```
config.yaml (config_version logged)
    │
    ├── observed data (Excel/CSV)
    ├── CMIP6 CSVs (Raw + BC) ← period coverage validated [FIX-03]
    │
    ├── seasonal aggregation (Annual/Wet/Dry, 80% completeness gate)
    ├── build_mme() → mean/median/P25/P75/n_models (NaN-safe)
    ├── validation_metrics() → KGE(ddof=1)/NSE/PBIAS on common years [FIX-01]
    ├── change% per-model → MME mean/P25/P75 [FIX-02]
    │
    ├── 7 publication figures (600 DPI, single+double col, PNG+TIFF+PDF)
    │   └── spatial maps with coord labels + north arrow [FIX-04]
    ├── 3-level results (station×model, station×MME, area summary)
    ├── publication tables (T01–T05, S1–S2)
    │
    └── Figure QC gate → CURRENT_RELEASE symlink (QC-PASS only)
```
