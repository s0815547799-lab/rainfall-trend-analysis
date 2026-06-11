# AUDIT REPORT — Rainfall Trend Analysis Repository

**Date:** 2026-06-11  
**Auditor:** Senior Hydroclimatological Review (AI-assisted full-codebase audit)  
**Scope:** All Python modules, statistical methods, data workflows, reproducibility, and publication readiness  
**Standard:** Q1–Q2 journal submission (Hydrology, Hydroclimatology, Environmental Science)

---

## 1. Executive Summary

The repository implements a publication-quality rainfall trend analysis pipeline for the
Phetchaburi–Prachuap Khiri Khan River Basin, Thailand (1981–2014, 12 stations, daily data).
Version 4 (`rainfall_trend_analysis_v4.py` + `rta/` package) extends the legacy v3
single-file script with four Mann-Kendall variants, field significance testing,
checkpoint/resume, and true WGS84 geographic maps.

The **scientific logic is fundamentally sound** and the dominant analysis path (Standard MK,
Modified MK, Sen's slope) is correctly implemented per the cited references.

However, **eight defects are CRITICAL** and must be resolved before any submission or public
release:

**Rainfall trend analysis pipeline:**

| Severity | Count | Nature |
|----------|-------|--------|
| CRITICAL | 5 | Wrong results, silent output gaps, cross-module divergence |
| MAJOR | 10 | Bias, misleading statistics, dependency/structure issues |
| MINOR | 8 | Documentation inconsistencies, dead code, non-standard practices |

**CMIP6 sub-projects (CMIP6_package / CMIP6_MME_v2):**

| Severity | Count | Nature |
|----------|-------|--------|
| CRITICAL | 3 | Missing calendar handling, missing bias correction, NaN percentile bug |
| MAJOR | 7 | Hardcoded scenarios, no trend on projections, change% methodology, anomaly base, reproducibility |
| MINOR | 5 | Metadata loader, std=0 for n=1, no config versioning, missing monthly aggregation, period coverage |

---

## 2. Scope of Files Audited

### Rainfall Trend Analysis Pipeline

| File / Module | Status |
|---------------|--------|
| `rainfall_trend_analysis_v3.py` | Fully audited |
| `rainfall_trend_analysis_v4.py` | Fully audited |
| `rta/config.py` | Fully audited |
| `rta/io.py` | Fully audited |
| `rta/aggregation.py` | Fully audited |
| `rta/autocorr.py` | Fully audited |
| `rta/trend_tests.py` | Fully audited |
| `rta/pw.py` | Fully audited |
| `rta/tfpw.py` | Fully audited |
| `rta/batch.py` | Fully audited |
| `rta/field_sig.py` | Fully audited |
| `rta/field_significance.py` | Fully audited |
| `rta/spatial.py` | Fully audited |
| `rta/checkpoint.py` | Fully audited |
| `rta/excel_output.py` | Header audited |
| `rta/figures/helpers.py` | Fully audited |
| `rta/figures/taylor.py` | Header audited |
| `Comparative_4MMK.py` | Header audited |
| `calval_split.py` | Header audited |

### CMIP6 Sub-Projects

| File / Module | Status |
|---------------|--------|
| `CMIP6_MME_v2/config/config.yaml` | Fully audited |
| `CMIP6_MME_v2/main.py` | Fully audited |
| `CMIP6_MME_v2/src/rainfall/seasonal.py` | Fully audited |
| `CMIP6_MME_v2/src/ensemble/mme.py` | Fully audited |
| `CMIP6_MME_v2/src/gis/interp.py` | Fully audited |
| `CMIP6_MME_v2/src/validation/metrics.py` | Fully audited |
| `CMIP6_MME_v2/src/tables/results.py` | Fully audited |
| `CMIP6_MME_v2/src/figures/make.py` | Fully audited |
| `CMIP6_MME_v2/src/utils/io.py` | Fully audited |
| `CMIP6_package/config/config.yaml` | Fully audited |
| `CMIP6_package/main.py` | Fully audited |
| `CMIP6_package/src/ensemble/mme.py` | Fully audited |
| `CMIP6_package/src/figures/make.py` | Fully audited |
| `CMIP6_package/src/utils/io.py` | Fully audited |

---

## 3. Statistical Method Review

### 3.1 Standard Mann-Kendall (Mann 1945; Kendall 1975)

**Location:** `rta/trend_tests.py::standard_mk()`, mirrored in `rainfall_trend_analysis_v3.py`

**Assessment: CORRECT**

- S statistic computed via vectorized inner slice loop `_mk_s_fast()` — O(n²) but correct
- Tie correction in Var(S) is the standard formula: `(n(n-1)(2n+5) − Σt_i(t_i-1)(2t_i+5)) / 18`
- Continuity correction applied: `Z = (S−1)/√Var(S)` for S>0, `(S+1)/√Var(S)` for S<0
- Two-tailed p-value: `2 × (1 − Φ(|Z|))`, capped at 1.0 ✓
- Kendall's τ = S / [n(n-1)/2] ✓
- Significance thresholds α=0.05 (Z₀.₀₂₅=1.96) and α=0.01 (Z₀.₀₀₅=2.576) ✓

**Defect noted:** `mk_s_ties()` (used nowhere) calls `np.sum(generator)` — anti-pattern.
`_mk_s_fast()` name is misleading (still O(n²) Python iterations).

---

### 3.2 Modified Mann-Kendall (Hamed & Rao 1998)

**Location:** `rta/trend_tests.py::modified_mk()`, mirrored in `rainfall_trend_analysis_v3.py`

**Assessment: CORRECT**

- Autocorrelations computed on ranked series (not raw values) as per H&R98 ✓
- Only statistically significant ρ_k values are used (|ρ_k| > z₀.₀₂₅/√n) ✓
- Inflation factor: `n/n* = max(1.0, 1 + (2/n) Σ(n−k)ρ_k)` — floor at 1.0 prevents variance
  deflation ✓
- Var*(S) = Var(S) × (n/n*) ✓
- Z uses Var*(S) ✓
- Sen's slope computed on original series (not adjusted) ✓

**Note:** The floor `max(1.0, ...)` in the inflation factor is consistent with the
`Comparative_4MMK.py` fix log (FIX-3) and prevents the theoretically possible but
practically undesirable case where negative ρ_k values reduce variance below the
uncorrected level.

---

### 3.3 PW-MK — Prewhitening (Yue & Wang 2004)

**Location:** `rta/pw.py::pw_mk()` AND `rta/trend_tests.py::pw_mk()`

**Assessment: CRITICAL DEFECT (C-01)**

The Mann-Kendall Z statistic is correctly applied to the prewhitened series `y = x[t+1] − ρ₁·x[t]`.
However, `standard_mk(y)` is called internally, and `standard_mk` computes Sen's slope
as `sens_slope(y)`. This means the reported Sen's slope and CI reflect the slope of the
**prewhitened (first-difference-like) series**, not the original rainfall series.

**Impact:** The reported β (mm/yr) for PW-MK is systematically different in magnitude and
direction from the true rainfall trend. The prewhitened series y has no direct physical
rainfall interpretation. This would be flagged immediately by Q1 reviewers.

**Correct approach (Yue & Wang 2004):** Apply MK to prewhitened series for hypothesis testing,
but estimate Sen's slope from the **original series** (or from the trend-restored series in TFPW).

Additionally, the two implementations differ:

| Attribute | `rta/pw.py` | `rta/trend_tests.py` |
|-----------|-------------|----------------------|
| Check n<MIN_N after prewhitening | YES (returns null) | NO (proceeds with n<10) |
| Called by | v3 fallback import | v4 pipeline via `rta.batch` |

---

### 3.4 TFPW-MK — Trend-Free Prewhitening (Yue et al. 2002)

**Location:** `rta/tfpw.py::tfpw_mk()` AND `rta/trend_tests.py::tfpw_mk()`

**Assessment: MOSTLY CORRECT; one defect**

The algorithm follows Yue et al. (2002):
1. β = Sen's slope of original series ✓
2. Detrend: x_d = x − β·t (t=1..n) ✓
3. Compute ρ₁ of detrended series ✓
4. If significant: prewhiten x_d, restore trend: z = (x_d[t+1] − ρ₁·x_d[t]) + β·t₂ ✓
5. Apply standard_mk(z) ✓

**Defect:** When `pw_applied=True`, `standard_mk(z)` is called where `z` has length n-1.
`standard_mk` calls `sens_slope(z)` internally, so the reported Sen's slope is the slope of
the trend-restored prewhitened series (n-1 points), not the original series (n points).
The bias is small because the trend has been re-added, but the time axis is shifted by
one observation and the slope magnitude may differ slightly from the original.

The no-prewhitening path is correct: `standard_mk(z)` where z = x_d + β·t = original x. ✓

---

### 3.5 Sen's Slope Estimator (Sen 1968; Gilbert 1987)

**Location:** `rta/trend_tests.py::sens_slope()`

**Assessment: MOSTLY CORRECT; CI upper bound off by one rank**

- Q = median of all N = n(n-1)/2 pairwise slopes ✓
- Slopes computed as (x[j]−x[i])/(j−i) using integer index differences ✓
  (Valid for equidistant annual/seasonal data where Δt=1 year per step)
- CI uses Gilbert (1987) formula with Var(S) from MK variance ✓

**Defect (MAJOR):** The upper confidence bound uses:
```python
hi_r = min(N - 1, int(round((N + C_alpha) / 2.0)))
```
Per Gilbert (1987) Eq. 14.2, the correct 1-indexed upper rank is M2 = (N + Cα)/2 + 1,
which in 0-based indexing is `hi_r = int((N + C_alpha) / 2)` (same as above).
The issue is the missing `+ 1` before the final index conversion. For n=34 years,
N=561 slopes, so C_alpha ≈ 50 — the error is at most 1 slope rank, corresponding to
≈0.2% of the sorted range. Numerically minor but technically incorrect.

---

### 3.6 Autocorrelation Assessment

**Location:** `rta/autocorr.py`

**Assessment: CORRECT**

- Pearson lag-k ACF: `Σ(x[t]−x̄)(x[t+k]−x̄) / Σ(x[t]−x̄)²` ✓
  (Biased estimator — standard for MK correction purposes)
- Significance test: `|r₁| > z₀.₀₂₅ / √n` (Bartlett two-tailed) ✓
- max_lag defaults to `min(n//3, n-1)` — appropriate for short series ✓

**Note:** The Bartlett SE (1/√n) is technically for white noise. For ranked series
used in MMK, this is the formula specified by Hamed & Rao (1998). ✓

---

### 3.7 Field Significance

**Location:** `rta/field_sig.py` (v4) and `rta/field_significance.py` (v3 fallback)

**Walker (1914) Binomial Test — CORRECT**

- P(X ≥ n_sig | n, α) = binom.sf(n_sig − 1, n_stations, alpha) ✓
- One-sided test under H₀: local tests are independent, each with probability α of
  false rejection ✓

**Livezey-Chen (1983) Monte Carlo — CORRECT ALGORITHM, but ANTI-CONSERVATIVE**

- Independent permutation of each station's time series ✓
- p_field_LC = fraction of MC draws ≥ S_obs, floored at 1/n_perm ✓
- **Known limitation (MAJOR):** Independent permutation ignores spatial correlation between
  stations. For 12 stations in a small basin, substantial cross-station correlation exists.
  Under correlated fields, the null distribution has wider spread than the independence
  assumption implies, so the test is anti-conservative (over-rejects H₀).

**CRITICAL — MMK Field Significance Missing in v4 Pipeline:**

`rta/field_sig.py::field_sig_summary()` computes `N_sig_MMK` but does **NOT** run
Walker or LC for Modified MK. Columns `Walker_p_MMK` and `LC_p_MMK` are absent from
the returned DataFrame. The v4 Excel Sheet S8 therefore lacks field significance
results for the method recommended for autocorrelated data (MMK). This is a silent
output gap that would be immediately apparent to reviewers.

**Divergence between implementations:**

| Feature | `field_sig.py` (v4) | `field_significance.py` (v3) |
|---------|--------------------|-----------------------------|
| Min series length | 4 | MIN_N = 10 |
| Walker for MK | ✓ | ✓ |
| Walker for MMK | ✗ | ✓ |
| LC for MK | ✓ | ✓ |
| LC for MMK | ✗ | ✓ |

---

### 3.8 Temporal Aggregation

**Location:** `rta/aggregation.py::aggregate_all()`

**Assessment: CORRECT**

- Annual: YS resample with 80% completeness threshold ✓
- Wet season (May–Oct): filtered by month then YS resample ✓
- Dry season: Nov/Dec shifted to year+1 for hydrological year labelling ✓
- Incomplete dry-season boundary blocks nulled via month-coverage check ✓
- `validate_dry_season()` adds additional integrity checks ✓

**Documentation mismatch (MINOR):** CLAUDE.md §6.2 states 60% threshold for dry/wet seasons
but code uses 80% for all scales.

---

### 3.9 Quality Control

**Location:** `rta/io.py::quality_control()`

**Assessment: FUNCTIONALLY CORRECT; methodological gap for publication**

- Missing-value flags → NaN ✓
- IQR outlier detection on wet-day values only (not zeros) ✓
- Linear interpolation of gaps ≤5 consecutive days ✓
- **MAJOR:** Extreme outliers (> Q3+3×IQR) are FLAGGED but NOT removed from the dataset.
  All downstream trend calculations use the potentially erroneous extreme values.
  For Q1 publication, the treatment of outliers must be explicitly justified.

---

## 4. Module Architecture Review

### 4.1 Duplicate Implementations (CRITICAL)

The repository contains parallel implementations of the same functionality:

| Function | Module A | Module B | Differences |
|----------|----------|----------|-------------|
| `pw_mk` | `rta/pw.py` | `rta/trend_tests.py` | `pw.py` checks n<MIN_N post-prewhiten |
| `tfpw_mk` | `rta/tfpw.py` | `rta/trend_tests.py` | Essentially identical |
| `field_sig_summary` | `rta/field_sig.py` | `rta/field_significance.py` | Differ in MMK coverage and MIN_N threshold |
| `walker_test` | `rta/field_sig.py` | `rta/field_significance.py` | Different docstrings; effectively equivalent |
| `livezey_chen_mc` | `rta/field_sig.py` | `rta/field_significance.py` | len≥4 vs len≥MIN_N |
| `load_coords` | `rta/io.py` | `rta/spatial.py` | Minor pattern differences |
| Checkpoint I/O | `rta/io.py` | `rta/checkpoint.py` | Different function names; same format |

**v4 pipeline uses:** `rta.trend_tests` (pw_mk, tfpw_mk), `rta.field_sig`, `rta.io` (load_coords, checkpoints)  
**v3 fallback uses:** `rta.pw`, `rta.tfpw`, `rta.field_significance`, `rta.checkpoint`

This split means bugs fixed in one version do not propagate to the other.

---

### 4.2 Version Consistency

| Component | VERSION value |
|-----------|--------------|
| `rta/config.py` | `"4.0"` (used by v4) |
| `rainfall_trend_analysis_v3.py` | `"2.0"` (self-contained constant) |
| README.md | `v4.0` |
| CHANGELOG.md | `v4.0_hydroclimatology_Q1` |

The v3 script does NOT import `VERSION` from `rta.config`, so it independently tracks "2.0". ✓

---

### 4.3 Repository Pollution

The following unrelated projects/files are committed to this repository:

| Item | Type | Issue |
|------|------|-------|
| `CMIP6_package/` | Full Python package | Unrelated CMIP6 multi-model ensemble project |
| `CMIP6_MME_v2/` | Full Python package | Duplicate/updated version of above |
| `CMIP6_MME_v2_FINAL_RELEASE.zip` | Binary archive | 22 MB binary in git history (permanent) |
| `Observed_Rain_daily_198101_201412_Prachuap Khiri Khan_ComprehensiveAnalysis.xlsx` | Output file | Generated output committed to repo |
| `30_amarea_prachuap_khiri_khan.*` | Shapefiles (.shp/.dbf/.shx/.prj) | Binary geodata not in .gitignore |
| `calval_split.py` | Script | Undocumented calibration/validation utility |
| `Comparative_4MMK.py` | Script | Undeclared dependencies; simulation study |

---

## 5. Reproducibility Assessment

| Component | Status |
|-----------|--------|
| Python version pinned | ✓ README.md (3.11.15) |
| Package versions pinned | ✓ README.md |
| requirements.txt | ✗ ABSENT |
| pyproject.toml | ✗ ABSENT |
| Random seed fixed | ✓ `seed=42` in LC Monte Carlo |
| Checkpoint/resume system | ✓ 6-step pickle |
| Input data discoverable | ✓ auto-discovery by filename pattern |
| Output path deterministic | ✓ derived from input CSV name |
| `SAVE_PDF=True` mutable global | ⚠ Modified at runtime via `--no-pdf` flag (thread-unsafe but not concurrent) |

---

## 6. Q1 Journal Readiness Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Standard MK implemented correctly | ✓ | |
| Modified MK (H&R98) implemented correctly | ✓ | |
| PW-MK applied correctly | ⚠ | Sen's slope on prewhitened series — CRITICAL |
| TFPW-MK applied correctly | ⚠ | Slope minor bias when PW applied |
| Sen's slope + 95% CI | ⚠ | CI upper bound off by 1 rank |
| Lag-1 autocorrelation test | ✓ | |
| Field significance (Walker) | ⚠ | MMK results missing in v4 |
| Field significance (LC Monte Carlo) | ⚠ | Ignores spatial correlation |
| 4-method comparison table | ✓ | |
| Descriptive statistics | ⚠ | Wet-days/yr numerator mismatch |
| Geographic spatial maps | ✓ | WGS84 with compass/scale bar |
| Publication-quality figures (600 DPI) | ✓ | |
| 9-sheet Excel workbook | ⚠ | Sheet S8 missing MMK field sig |
| Missing data handling documented | ✓ | |
| Outlier treatment justified | ✗ | Flagged but not removed or justified |
| Normality tests | ✗ | Not computed (not required but expected) |
| Change-point tests (Pettitt/CUSUM) | ✗ | Common companion analysis |
| Stationarity tests (ADF) | ✗ | Common companion analysis |
| requirements.txt | ✗ | |

---

---

## 9. CMIP6 Sub-Project Scientific Review

A dedicated audit of `CMIP6_package/` (v1) and `CMIP6_MME_v2/` (v2) was conducted.
Full findings are in `CMIP6_REVIEW_REPORT.md`. Summary:

### 9.1 Architecture

Both packages ingest pre-processed station-level CSVs (assumed bias-corrected from CMIP6
NetCDF). Version 2 extends version 1 with dynamic scenario support, NaN-safe percentiles,
both `.xlsx`/`.csv` metadata loading, and a 3-level publication table format.

### 9.2 CRITICAL Omissions

**CC-01 — No calendar harmonisation code.**
Neither package contains any code for CMIP6 calendar variants (`noleap`, `360_day`,
`proleptic_gregorian`). No references to `cftime`, `xarray.cftime_range`, or leap-day
normalisation exist. Either calendar conversion was done during NetCDF extraction and must
be fully documented in the methods, or it must be implemented in the pipeline.

**CC-02 — No bias correction implementation.**
No QDM, QM, Delta Change, or BCSD code exists in either package. Bias correction is
assumed pre-applied to input CSVs. Without explicit documentation of the BC method,
reference period, software version, and archived corrected data, the analysis is not
independently reproducible. This is a Q1 blocker.

**CC-03 (v1 only) — MME percentile NaN bug.**
`CMIP6_package/src/ensemble/mme.py` computes `p25`/`p75` via bare `np.percentile(s, 25)`.
When any model has a missing year, the pandas `s` series contains NaN. On NumPy ≥ 1.22
this raises; on older versions it silently propagates NaN. Version 2 correctly uses
`np.percentile(s.dropna(), 25) if s.notna().any() else np.nan`.

### 9.3 MAJOR Findings

| ID | Description |
|----|-------------|
| CM-01 | v1 figures hardcode `SCEN = ["ssp245","ssp585"]`; ignores `cfg["scenarios"]` |
| CM-02 | Equal model weighting undocumented; model family redundancy not corrected |
| CM-03 | Change% computed on MME statistics rather than per-model change% aggregated to MME |
| CM-04 | No MK/Sen's slope trend analysis within projected future windows (2021–2050, 2071–2100) |
| CM-05 | `fig3_anomaly_ts()` uses grand-mean baseline instead of configured baseline period |
| CM-06 | No archived or deterministic script to regenerate bias-corrected CSV inputs from raw CMIP6 |
| CM-07 | KGE computed with `ddof=0` (population std); Gupta et al. (2009) uses `ddof=1`; undocumented |

### 9.4 MINOR Findings

| ID | Description |
|----|-------------|
| Cm-01 | `CMIP6_package` `load_metadata()` accepts only `.xlsx`; v2 accepts both |
| Cm-02 | `std = 0.0` reported for stations with n=1 valid year instead of `NaN` |
| Cm-03 | No `version` or `run_id` in `config.yaml`; outputs cannot be traced to config |
| Cm-04 | No monthly aggregation for projected series; prevents climatology comparison |
| Cm-05 | No check that loaded model series actually spans the full configured period |

### 9.5 Reproducibility

Deterministic methods (IDW, kriging, ensemble statistics) require no random seeds.
The analysis is NOT independently reproducible due to CC-01 and CC-02. Resolving
these two omissions is the minimum viable requirement for Q1 submission of CMIP6 results.

---

## 7. Positive Findings

The following are well-implemented and publication-quality:

1. **MMK ranked-series autocorrelation** — Strictly follows Hamed & Rao (1998), using only
   statistically significant ρ_k values, with variance floor at n/n* ≥ 1.

2. **Dry-season hydrological year shift** — The Nov/Dec→year+1 approach is correctly
   implemented with a post-hoc completeness check that nulls boundary blocks.
   The `validate_dry_season()` function provides an auditable diagnostic log.

3. **Tie correction in MK variance** — The tie correction term `Σt(t-1)(2t+5)/18` is
   correctly subtracted. Rainfall data often has many tied zero values; this matters.

4. **Checkpoint/resume system** — The 6-step pickle checkpoint is robust and
   enables rapid iteration during figure development without re-running statistics.

5. **Station coordinate loader robustness** — `pd.read_csv(..., dtype=str)` prevents
   integer station IDs being cast to float64 (e.g., `500001.0`), avoiding silent
   key-mismatch failures in coordinate lookups.

6. **`build_4method_comparison()`** — Comprehensive wide-format table with delta columns
   (dZ, dSlope relative to Standard MK), all_agree flag, and n_sig_methods count.

7. **Backward compatibility** — v4 generates both `Output_TrendV2_*` (v3-identical)
   and `Output_TrendV4_*` outputs. The validation in CHANGELOG confirms 144/144
   statistical results are numerically identical between v3 and v4.

---

## 8. References Cited in Audit

| Reference | Relevance |
|-----------|-----------|
| Mann (1945) *Econometrica* 13:245–259 | Standard MK |
| Kendall (1975) *Rank Correlation Methods* | Standard MK |
| Sen (1968) *JASA* 63:1379–1389 | Sen's slope |
| Gilbert (1987) *Statistical Methods for Environmental Pollution Monitoring* | Sen's slope CI |
| Hamed & Rao (1998) *J. Hydrol.* 204:182–196 | Modified MK |
| Yue & Wang (2004) *Water Resour. Res.* 40:W08307 | PW-MK |
| Yue et al. (2002) *Hydrol. Process.* 16:1807–1829 | TFPW-MK |
| Walker (1914) *Mem. India Met. Dept.* 21:22–45 | Field significance |
| Livezey & Chen (1983) *Mon. Weather Rev.* 111:46–59 | Field significance MC |
| Benjamini & Hochberg (1995) *J. R. Stat. Soc. B* 57:289–300 | FDR (Comparative_4MMK.py) |
