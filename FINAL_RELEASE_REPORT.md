# Final Release Report

**Project:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan River Basin  
**Pipeline version:** v4.1 (branch `claude/claude-md-docs-79uw4q`)  
**Date:** 2026-06-11

---

## Completed Fixes

| ID | File | Function | What was wrong | What was fixed |
|----|------|----------|----------------|----------------|
| **C-01** | `rta/trend_tests.py` | `pw_mk()` | Sen's slope computed on prewhitened residuals `y`; expected slope ≈ β·(1−ρ₁), not β | After `standard_mk(y)`, override `slope_Q/lo/hi` with `sens_slope(x)` from original series |
| **C-03** | `rta/field_sig.py` | `field_sig_summary()` | Walker and LC tests run only for Standard MK; `Walker_p_MMK`, `Walker_sig_MMK`, `LC_p_MMK`, `LC_sig_MMK` absent from output | Walker test added for MMK; LC p-value for MMK derived from existing null distribution with MMK-based observed fraction |
| **CM-05** | `CMIP6_MME_v2/src/figures/make.py` `CMIP6_package/src/figures/make.py` | `fig3_timeseries()` | Anomaly baseline used grand mean over entire series (historical + future), shifting reference by +101 mm in test scenario | Baseline now filtered to `cfg["periods"]["baseline"]` years (1981–2014) |

Validation results: see `VALIDATION_REPORT.md`.

---

## Remaining Known Issues

### Rainfall Pipeline

| ID | Severity | File | Description |
|----|----------|------|-------------|
| C-02 | CRITICAL | `rta/pw.py`, `rta/trend_tests.py`, `rta/field_sig.py`, `rta/field_significance.py` | Duplicate module implementations with divergent behaviour; fixes applied to one copy do not propagate to the other |
| C-04 | CRITICAL | `rta/trend_tests.py::pw_mk()` | No MIN_N re-check after prewhitening (len n−1); edge case for n=10 stations, negligible for this 34-year dataset |
| C-05 | CRITICAL | `rta/field_sig.py::livezey_chen_mc()`, `field_sig_summary()` | Station eligibility uses `len >= 4` instead of `MIN_N = 10`; Walker test denominator inflated if any station has 4–9 valid years |
| M-01 | MAJOR | `rta/io.py::quality_control()` | Extreme outliers flagged but not removed; outlier treatment not justifiable for Q1 without explicit policy |
| M-02 | MAJOR | `rta/aggregation.py::descriptive_stats()` | Wet-days/yr numerator from all-years daily records; denominator from valid-year count; mismatched |
| M-03 | MAJOR | `rta/field_sig.py::livezey_chen_mc()` | Livezey-Chen uses independent station permutation; ignores spatial correlation between stations (anti-conservative for small basins) |
| M-04 | MAJOR | `rta/trend_tests.py::sens_slope()` | CI `hi_r` uses `round` not `int` (floor); off by 1 slope rank — numerically minor, technically incorrect per Gilbert (1987) |

### CMIP6 Sub-Projects

| ID | Severity | Package | Description |
|----|----------|---------|-------------|
| CC-01 | CRITICAL | Both | No CMIP6 calendar harmonisation code; `360_day` models will corrupt seasonal totals via `pd.to_datetime()`; must be documented in §2 |
| CC-02 | CRITICAL | Both | No bias correction implementation; BC method, reference period, and software must be documented in §2 |
| CC-03 | CRITICAL | `CMIP6_package` only | `np.percentile(s, q)` without NaN guard in `build_mme()`; P25/P75 wrong when any model has missing years. Fixed in `CMIP6_MME_v2`; `CMIP6_package` still unpatched |
| CM-01 | MAJOR | `CMIP6_package` only | Scenarios hardcoded as `["ssp245","ssp585"]`; ignores `cfg["scenarios"]` |
| CM-02 | MAJOR | Both | Equal model weighting undocumented; model family redundancy not corrected |
| CM-03 | MAJOR | Both | Change% computed on MME mean rather than per-model change% aggregated to MME |
| CM-04 | MAJOR | Both | No MK/Sen's slope trend analysis on projected future time series (2021–2050, 2071–2100) |
| CM-06 | MAJOR | Both | No archived or deterministic script to regenerate bias-corrected CSV inputs from raw CMIP6 |
| CM-07 | MAJOR | `CMIP6_MME_v2` | KGE uses `ddof=0` (population std); Gupta et al. (2009) specifies `ddof=1`; undocumented deviation |

### Reproducibility Gaps (both pipelines)

| Item | Status |
|------|--------|
| `requirements.txt` | Absent — must be created before submission |
| `run_id` / `config_version` in `config.yaml` | Absent |
| Bias-corrected input data archived | Not confirmed |
| CMIP6 calendar harmonisation documented | Not documented |
| Bias correction method documented | Not documented |

---

## Q1 Publication Readiness

| Component | Status |
|-----------|--------|
| Rainfall pipeline — MK/MMK/TFPW statistics | Ready |
| Rainfall pipeline — PW-MK slopes | **Fixed (C-01)** |
| Rainfall pipeline — MMK field significance | **Fixed (C-03)** |
| Rainfall pipeline — outlier justification | Not ready |
| Rainfall pipeline — duplicate modules | Not ready |
| CMIP6 anomaly figures | **Fixed (CM-05)** |
| CMIP6 calendar documentation | Not ready |
| CMIP6 bias correction documentation | Not ready |
| CMIP6 change% methodology | Not ready |
| `requirements.txt` | Not ready |

**Minimum additional work before Q1 submission:** resolve CC-01, CC-02 (documentation only), C-02 (consolidate duplicates), add `requirements.txt`.
