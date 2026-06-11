# Executive Summary — Rainfall Trend Analysis Audit

**Date:** 2026-06-11  
**Basis:** AUDIT_REPORT.md, CMIP6_REVIEW_REPORT.md, CRITICAL_VALIDATION_REPORT.md  
**Scope:** Rainfall trend pipeline (`rta/` package, v3/v4 scripts) + CMIP6 sub-projects

---

## Confirmed Findings

| Component | Critical | Major | Minor |
|-----------|----------|-------|-------|
| Rainfall pipeline (`rta/`) | 5 | 10 | 8 |
| CMIP6 sub-projects | 3 | 7 | 5 |
| **Total** | **8** | **17** | **13** |

The dominant analysis path — Standard MK, Modified MK, Sen's slope, dry-season hydrological year shift — is correctly implemented per cited references. All 8 critical defects are confirmed by direct code evidence.

---

## Top 5 Issues by Scientific Impact

### 1 — PW-MK slope computed on prewhitened series (C-01)
**Files:** `rta/trend_tests.py:265`, `rta/pw.py:82`

`standard_mk(y)` is called where `y` is the prewhitened residual; `standard_mk` calls `sens_slope(y)` internally. For a series with lag-1 autocorrelation ρ₁ = 0.2–0.4, the expected bias is `E[slope_reported] ≈ β·(1−ρ₁)`, giving a 20–40% systematic underestimate. Yue & Wang (2004) state explicitly that Sen's slope must be estimated from the original series. This defect falsifies the 4-method comparison table (`PW_slope`, `dSlope_PW` columns) for all stations where prewhitening is applied.

### 2 — Bias correction undocumented for CMIP6 projections (CC-02)
**Files:** All of `CMIP6_package/` and `CMIP6_MME_v2/`

No QDM, QM, Delta Change, or BCSD code exists in either CMIP6 package. If bias correction was applied before CSV generation, the methods section is incomplete. If it was not applied, all change% projections and KGE/NSE/PBIAS validation scores are scientifically invalid for a hydrological impact assessment. Q1 hydroclimatology journals (Journal of Hydrology, Water Resources Research, Climatic Change) require bias correction to be named, cited, and reproducible. This is a rejection criterion in the current state.

### 3 — MMK field significance absent from v4 pipeline (C-03)
**File:** `rta/field_sig.py:258–282`

`field_sig_summary()` counts `N_sig_MMK` but never calls `walker_test()` or `livezey_chen_mc()` for Modified MK. Columns `Walker_p_MMK`, `Walker_sig_MMK`, `LC_p_MMK`, `LC_sig_MMK` are entirely absent from v4 output (Excel Sheet S8). MMK is the method recommended for autocorrelated series — the absence of its field significance result is a complete output gap that will be immediately queried by reviewers.

### 4 — No CMIP6 calendar harmonisation code (CC-01)
**Files:** All of `CMIP6_package/` and `CMIP6_MME_v2/`

No code handles `noleap`, `360_day`, or `proleptic_gregorian` CMIP6 calendar variants. For `360_day` models (months of 30 days), `pd.to_datetime()` produces NaT on day 31 of long months, corrupting seasonal totals. For `noleap` models the numerical impact is small but the reproducibility requirement stands: CMIP6 protocol requires calendar metadata to be recorded and the handling method to be documented. Without this, independent replication is impossible.

### 5 — Figure 3 anomaly baseline uses grand mean instead of baseline period (CM-05)
**File:** `CMIP6_MME_v2/src/figures/make.py:258`, `CMIP6_package/src/figures/make.py:226`

Both packages compute `base = obs.groupby("season").rainfall.mean()` across the entire concatenated time series (historical + future). The correct IPCC standard is to compute the baseline climatology exclusively over the configured `baseline` period (1981–2014) and subtract it from all periods. The current code produces anomaly magnitudes that change if the length of the future scenario window changes, making Fig 3 non-reproducible across different run configurations.

---

## Publication Risk

| Risk Area | Rating | Reason |
|-----------|--------|--------|
| Rainfall pipeline — MK/MMK/TFPW conclusions | **Acceptable** | Core methods correct; C-03 must be fixed |
| Rainfall pipeline — PW-MK slopes/tables | **Blocked** | C-01 produces systematic numerical error |
| CMIP6 projections — reproducibility | **Blocked** | CC-01 and CC-02 are standard rejection criteria |
| CMIP6 projections — figures | **Blocked** | CM-05 produces wrong anomaly magnitudes |
| Overall Q1 submission readiness | **Not ready** | 4 blockers must be resolved before submission |

Estimated time to clear all blockers: 1–2 days of code work (C-01, C-03, CM-05) plus methods-section writing for CC-01 and CC-02.

---

## Recommended Implementation Order

| Priority | ID | Action | Effort | Impact |
|----------|----|--------|--------|--------|
| 1 | **C-03** | Add Walker + LC tests for MMK in `field_sig_summary()`; copy pattern from `rta/field_significance.py` | 2 h | Closes complete output gap for primary test method |
| 2 | **C-01** | In `rta/trend_tests.py::pw_mk()`, replace `standard_mk(y)` with: run MK on `y` for Z/p; run `sens_slope(x)` on original `x` for slope | 1 h | Removes 20–40% systematic slope bias; fixes 4-method table |
| 3 | **CM-05** | In both `make.py` files, filter `obs` to `baseline_years` before computing `base` | 1 h | Removes wrong anomaly baselines from both CMIP6 packages |
| 4 | **CC-01** | Add "Data Pre-Processing §: Calendar harmonisation" to manuscript; document which calendars each model uses and how handled | 0.5 d | Satisfies reproducibility requirement without code changes (if handled externally) |
| 5 | **CC-02** | Add "Data Pre-Processing §: Bias correction" to manuscript naming the method, reference period, software, and data archive DOI | 0.5 d | Satisfies Q1 documentation standard; absolute prerequisite for CMIP6 component |
| 6 | **C-02** | Consolidate duplicate modules: delete `rta/pw.py`, `rta/tfpw.py`, `rta/field_significance.py`, `rta/checkpoint.py`; update imports | 3 h | Prevents fix-propagation failures; single source of truth |
| 7 | **CC-03** | Copy NaN-safe lambdas from `CMIP6_MME_v2/mme.py` to `CMIP6_package/mme.py` | 15 min | Fixes v1 P25/P75 corruption if v1 is archived or compared |
| 8 | **CM-04** | Add `run_all()` MK loop over projected windows (2021–2050, 2071–2100) in both CMIP6 packages | 1 d | Elevates CMIP6 from period-mean comparison to trend analysis; expected by Q1 reviewers |

**Do not submit until items 1–5 are complete.**
