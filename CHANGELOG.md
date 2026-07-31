# Changelog

All notable changes to this project are documented here.

---

## [v4.1_defect_fixes] — 2026-06-11

### Fixed

#### C-01 — PW-MK Sen's slope corrected to use original series
**File:** `rta/trend_tests.py::pw_mk()`

`standard_mk(y)` was called on the prewhitened series `y`, causing `sens_slope(y)` to
run on residuals instead of rainfall. Prewhitened residuals have expected slope β·(1−ρ₁),
not β (Yue & Wang 2004, §2).

Change: after `standard_mk(y)`, override `slope_Q/slope_lo/slope_hi` with
`sens_slope(x)` results from the original series. Z, p-value, tau, and significance
flags are unaffected — they are correctly derived from `y`.

#### C-03 — MMK field significance added to `field_sig_summary()`
**File:** `rta/field_sig.py::field_sig_summary()`

Walker and Livezey-Chen tests were run only for Standard MK. Four columns were absent
from the output DataFrame: `Walker_p_MMK`, `Walker_sig_MMK`, `LC_p_MMK`, `LC_sig_MMK`.

Change: Walker test now called for both MK and MMK using respective `n_sig_*` counts.
LC p-value for MMK derived by applying the MMK-based observed fraction against the
existing MK null distribution. Valid because permutation destroys autocorrelation,
making the null fractions method-invariant. Zero-station fallback row also updated.

#### CM-05 — Figure 3 anomaly baseline restricted to configured baseline period
**Files:** `CMIP6_MME_v2/src/figures/make.py::fig3_timeseries()`,
           `CMIP6_package/src/figures/make.py::fig3_timeseries()`

`obs.groupby("season").rainfall.mean()` used the entire obs series (historical + future
concatenated) as the anomaly baseline, producing a reference climatology that shifts
when the future window changes (non-reproducible).

Change: filter `obs` to `cfg["periods"]["baseline"]` years before computing the mean.
Baseline period `[1981, 2014]` is already defined in both `config/config.yaml` files.

---

## [v4.0_hydroclimatology_Q1] — 2026-05-27

### Summary
Full Q1-standard hydroclimatological trend analysis pipeline for the
Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand (1981–2014).
Introduces the `rta/` modular package, four trend methods, field significance,
checkpoint/resume, and true WGS84 geographic spatial maps.

### Added

#### rta/ Package (new)
- `rta/config.py` — shared constants, colour palette, `savefig` helper
- `rta/io.py` — CSV discovery, QC, checkpoint wrappers, `load_coords`
- `rta/aggregation.py` — annual / wet / dry / monthly aggregation + dry-season validation
- `rta/autocorr.py` — lag-k autocorrelation functions
- `rta/trend_tests.py` — Standard MK, Modified MK (Hamed & Rao 1998), Sen's slope
- `rta/pw.py` — Prewhitening MK (Yue & Wang 2004)
- `rta/tfpw.py` — Trend-Free Prewhitening MK (Yue et al. 2002)
- `rta/batch.py` — `run_all`, `build_comparison`, `build_4method_comparison`
- `rta/field_sig.py` — Walker (1914) binomial test + Livezey-Chen (1983) Monte Carlo
- `rta/field_significance.py` — parallel field significance implementation (v3 path)
- `rta/checkpoint.py` — 6-step pickle checkpoint/resume system
- `rta/spatial.py` — `load_coords`, `validate_coords`, `coords_to_df`
- `rta/spatial_maps.py` — top-level re-export of all spatial figure functions
- `rta/excel_output.py` — 9-sheet Excel workbook writer
- `rta/markdown.py` — paper-ready Markdown research summary writer

#### Figure Modules (new)
- `rta/figures/timeseries.py` — Fig 1, Fig 2
- `rta/figures/bars.py` — Fig 3
- `rta/figures/comparison.py` — Fig 4
- `rta/figures/heatmaps.py` — Fig 5
- `rta/figures/acf_plots.py` — Fig 6, Fig 12
- `rta/figures/climatology.py` — Fig 7
- `rta/figures/spatial.py` — Fig 8 (index-based legacy)
- `rta/figures/taylor.py` — Fig 9 (Taylor diagram)
- `rta/figures/method_comparison.py` — Fig 10, Fig 11
- `rta/figures/field_sig_plot.py` — Fig 13
- `rta/figures/spatial_maps.py` — Fig 14, Fig SpatialStation, Fig SpatialMethods,
  Fig SpatialFieldSig, Fig SpatialFull (true geographic WGS84 maps)
- `rta/figures/helpers.py` — shared rendering helpers

#### New Scripts
- `rainfall_trend_analysis_v4.py` — modular pipeline: checkpoint/resume,
  4 trend methods, field significance, 28 publication figures, 9-sheet Excel
- `station_coordinates.csv` — WGS84 coordinates for 128 stations
  (lat 11.18–12.59°N, lon 99.55–99.96°E; all 12 rainfall stations present)

#### Documentation
- `CLAUDE.md` — full project specification, module inventory, constants reference,
  execution order, statistical workflow, spatial module documentation
- `CHANGELOG.md` — this file

### Changed
- `rainfall_trend_analysis_v3.py` — extended with PW-MK, TFPW-MK, field
  significance, checkpoint/resume, 10 additional figures (Figs 9–14e),
  CLI flags `--no-resume` / `--no-pdf`; all original 8 figures preserved
- `.gitignore` — excludes runtime outputs, checkpoints, test figures

### Fixed
- `rta/spatial.py` `load_coords`: `pd.read_csv(..., dtype=str)` prevents pandas
  from reading integer station IDs as float64, eliminating `'500001.0'` key
  mismatch (v3 coordinate loader)
- `rta/io.py` `load_coords`: same `dtype=str` fix for v4 coordinate loader;
  root cause was `iterrows()` upcasting int64 to float64 via row Series widening

### Validated
- 12,418 daily records, 1981–2014, 12 stations, 0% missing
- 144/144 statistical results numerically identical v3 ↔ v4
- Dry-season hydrological year: 35 blocks (1981–2015), all PASS
- Autocorrelation-corrected MK applied to S3 (r₁=0.47), S5 (r₁=0.41), S11 (r₁=−0.35)
- Field significance: dry season Walker p < 0.05, LC-MC p < 0.05 (field-significant)
- Station coordinate coverage: 12/12 (1.0) both v3 and v4 paths
- Checkpoint recovery: all 6 steps load cleanly; figures regenerate identically

---

## [v2.0] — prior

- Initial single-file pipeline `rainfall_trend_analysis_v3.py`
- Standard MK + Modified MK (Hamed & Rao 1998) + Sen's slope
- 8 publication figures, 6-sheet Excel, Markdown summary
- Temporal scales: Annual, Wet (May–Oct), Dry (Nov–Apr hydrological year)

---

## [v3.0_Comparative_4MMK] — 2026-07-31

### Scope
Full scientific and statistical audit and correction of `Comparative_4MMK.py`.
All 12 defects (CORR-01 through CORR-12) found and corrected in one pass.
This entry covers changes to `Comparative_4MMK.py` only; the `rta/` package
files are unchanged.

---

### Fixed

#### CORR-01 — `sens_slope` returns dict; Gilbert (1987) CI uses int() floor
**Severity:** CRITICAL

`sens_slope()` previously returned a bare float (the median slope only).  
Callers that passed it to `standard_mk()` received no CI.  
Gilbert (1987) CI bound indices were computed with `round()`, which can inflate
the bound by 0.5 and shift the selected order-statistic.

**Correction:**
- `sens_slope()` now returns `{"Q", "lo", "hi", "intercept"}`.
- Both `lo_r` and `hi_r` computed with `int()` (floor) per Gilbert (1987).
- Intercept anchored at `median(x) − Q·median(t)`, never at a prewhitened series.
- Optional time vector `t` supports gapped series (years dropped by 80% gate).

---

#### CORR-02 — `modified_mk_hamed_rao` only sums SIGNIFICANT lag autocorrelations
**Severity:** CRITICAL

The VIF sum in MMK previously included ALL lag-k autocorrelations `ρ_k` for
`k = 1 … nlags`.  Hamed & Rao (1998) Eq. 3 and CLAUDE.md §12.1 require only
lags where `|ρ_k| > 1.96/√n`.  Including insignificant lags adds sampling
noise to the variance inflation, making the test overly conservative — the
effective sample size `n*` was being understated.

In addition, `nlags` was hard-capped at 20, under-correcting when `n > 42`.

**Correction:**
- `nlags = min(n − 1, n // 2)` — matches H&R98 Eq. 3.
- `sig_thresh = norm.ppf(0.975) / sqrt(n)` applied before summing.
- Only lags with `|ρ_k| > sig_thresh` contribute to `vif_sum`.
- VIF floored at 1.0 (CORR-03 overlap; deflation from negative AC is unphysical).
- ACF computed on **ranked** series via `scipy.stats.rankdata`, per H&R98.

---

#### CORR-03 — MMK VIF clamped at 1.0 (deflation floor)
**Severity:** HIGH

When lag-1 autocorrelation `ρ₁ < 0`, the unadjusted VIF formula yields
`n/n* < 1`, which would *reduce* `Var*(S)` below `Var(S)`.  A lower variance
inflates the Z statistic — the opposite of the intended conservative correction.
This is physically unreasonable for hydroclimatic series.

**Correction:**  
`vif = max(1.0, 1.0 + 2.0 * vif_sum)` — VIF is never less than 1.0.

---

#### CORR-04 — `prewhitening_mk` slope overrides from ORIGINAL series
**Severity:** CRITICAL

The PW-MK Z/p/tau statistics correctly derived from the prewhitened series `y`,
but `sens_slope(y)` was being returned as the reported slope.  The expected
slope of `y` is `β·(1−ρ₁)`, not `β` (Yue & Wang 2004 §2).  Any downstream
slope comparison (e.g. Table 4 ΔSlope columns) was therefore biased toward zero.

**Correction:**
- After `standard_mk(x_pw)`, slope fields `{slope, slope_lo, slope_hi}` are
  overridden with `sens_slope(x)` — from the **original** series `x`.
- `slope_pw = sens_slope(x_pw)["Q"]` retained as a diagnostic field.
- This matches CLAUDE.md §12.1 explicitly.

---

#### CORR-05 — `tfpw_mk` slope NOT overridden with `sens_slope(x)`
**Severity:** MODERATE

A previous version of the code incorrectly set `mk_res["slope"] = beta` 
(the initial detrending slope from the original series), then reset it to
`sens_slope(x)`.  CLAUDE.md §12.1 is explicit: "TFPW-MK: Slope from
trend-restored z is acceptable.  Do not replace with sens_slope(x)."

**Correction:**
- Slope/CI remain from `standard_mk(z)` where `z` is the trend-restored series.
- Initial slope `beta` stored as `slope_initial` for audit trail only.

---

#### CORR-06 — Pre/post-whitening MIN_N guard (n must remain ≥ 10 after n → n−1)
**Severity:** HIGH

Both `prewhitening_mk()` and `tfpw_mk()` shorten the series by 1 observation
when constructing the whitened/restored series.  No guard existed to prevent
running MK on a series of length < MIN_N (= 10) after this reduction.

**Correction:**
- Pre-check: `if n < MIN_N + 1:` — return NaN result before whitening.
- Post-check: `if len(x_pw) < MIN_N:` (PW) and `if len(z) < MIN_N:` (TFPW) —
  return NaN result if the series somehow falls below threshold after construction.
- Per CLAUDE.md §12.1: "re-check len >= MIN_N. Return null result if below threshold."

---

#### CORR-07 — `MIN_N = 10` enforced globally; replaced all `n < 4` guards
**Severity:** HIGH

Several functions used ad-hoc minimum-length checks (`n < 4`, `n < 5`) that
were far below the scientifically defensible threshold for non-parametric trend
tests.  MK S statistic has only 3 possible values for `n = 4`, making p-value
interpretation meaningless.

**Correction:**  
`MIN_N = 10` defined as a module-level constant.  All MK/MMK/PW/TFPW functions
now gate on `n < MIN_N`.  Field significance station filter also uses `MIN_N`.

---

#### CORR-08 — 80% per-year completeness gate added to `aggregate_rainfall()`
**Severity:** CRITICAL

Annual and seasonal aggregation previously used `groupby().sum()` with no
per-year completeness check.  A year with only 10 valid observations would
contribute a wildly underestimated annual total (e.g. 50 mm when true total
is ~1500 mm).  This biases the trend slope downward for early or late years
that are data-sparse.

**Correction:**
- New helper `_year_expected_days(year)` returns 365 or 366 via `calendar.isleap`.
- New helper `_valid_year_mask(df, thr=0.80)` computes per-station per-year
  valid-day fraction; returns a DataFrame of (Station, Year) pairs that pass.
- Annual aggregates inner-joined with `valid_yrs` — incomplete years are
  excluded (set to NaN), not included with deflated totals.
- Same 80% gate applied to wet-season and dry-season aggregates.
- Per CLAUDE.md §12.4: "80% gate applies uniformly to annual, wet, and dry scales."

---

#### CORR-09 — `quality_control()` rewritten; all MISS_FLAGS handled; IQR outlier cap
**Severity:** HIGH

The original `quality_control()` only replaced a subset of sentinel values and
had no outlier detection.  Missing-value flags such as `9.99e+20` and `1e+20`
(present in WMO-format Thai rainfall exports) would pass through as implausibly
large rainfalls.

**Correction:**
- All `MISS_FLAGS` iteratively replaced with `NaN`.
- Negative rainfall values → `NaN`.
- Values > 1000 mm/day → `NaN` (physical impossibility for daily gauge).
- Per-station IQR outlier detection: `Q3 + 3×IQR` computed on wet days (≥ 1 mm)
  only, so dry-day zeros do not collapse the IQR.  Outliers above threshold → `NaN`.
- QC report DataFrame saved to processed outputs for audit.

---

#### CORR-10 — `field_significance_mks()` added; all 8 mandatory columns present
**Severity:** HIGH

No field-significance test existed.  Multi-station significance is prone to
false discovery inflation; reporting individual-station p-values without a
field significance correction is insufficient for Q1 publication.

**Correction:**
- New function `field_significance_mks(series_list, p_values_mk, p_values_mmk)`.
- Walker (1914) binomial test for both MK and MMK (4 columns).
- Livezey-Chen (1983) Monte Carlo for both MK and MMK (4 columns).
- LC null distribution shared between MK and MMK per CLAUDE.md §12.3:
  permutation destroys autocorrelation, making the null method-invariant.
- All 8 mandatory columns per CLAUDE.md §12.10:
  `Walker_p_MK, Walker_sig_MK, Walker_p_MMK, Walker_sig_MMK,`
  `LC_p_MK, LC_sig_MK, LC_p_MMK, LC_sig_MMK`.
- Station filter: `len(series) >= MIN_N` (not `>= 4`).

---

#### CORR-11 — Legacy `np.random.seed()` call removed from `main()`
**Severity:** MODERATE

`np.random.seed(RANDOM_SEED)` at the top of `main()` has no effect on
`np.random.default_rng()` objects used throughout the script.  It affects
only the deprecated `numpy.random` module-level functions that are not
called anywhere in the pipeline.  The spurious call creates a false impression
that reproducibility is guaranteed.

**Correction:**
- `np.random.seed()` call removed.
- All PRNG usage routed through explicit `np.random.default_rng(seed)` calls.
- `seed=RANDOM_SEED` (= 42) passed to every Generator constructor.

---

#### CORR-12 — NaN key tuples defined for all four MK variants
**Severity:** MINOR

Early return on `n < MIN_N` previously returned inconsistent dicts (missing
keys that callers expected).  DataFrame construction from these partial dicts
created columns with `NaN` in some rows and missing in others.

**Correction:**  
Module-level tuples:
```python
_MK_NAN_KEYS   = ("S","Var_S","Z","tau","p","slope","slope_lo","slope_hi","method")
_MMK_NAN_KEYS  = ("S","Var_S","Var_S_mod","Z","tau","p","slope","slope_lo",
                  "slope_hi","n_s","vif","method")
_PW_NAN_KEYS   = ("S","Var_S","Z","tau","p","slope","slope_lo","slope_hi",
                  "slope_pw","phi","method")
_TFPW_NAN_KEYS = ("S","Var_S","Z","tau","p","slope","slope_lo","slope_hi",
                  "phi","method")
```
All short-circuit returns use `{k: np.nan for k in _*_NAN_KEYS}`.

---

### Added
- `_year_expected_days(year)` — helper for 80% completeness gate
- `_valid_year_mask(df, thr)` — per-station per-year completeness mask
- `field_significance_mks(series_list, p_values_mk, p_values_mmk)` — Walker + LC-MC
- `_MK_NAN_KEYS`, `_MMK_NAN_KEYS`, `_PW_NAN_KEYS`, `_TFPW_NAN_KEYS` constants
- `slope_pw` field in PW-MK output (diagnostic; slope on whitened series)
- `slope_initial` field in TFPW-MK output (initial detrending beta, for audit trail)
- `MMK_VIF` and `MMK_n_s` columns in Table 4 (`build_table4_trends`)
- All 8 field significance columns appended to Table 4 when `field_sig` is provided

### Changed
- `main()` version updated to v3.0
- `sens_slope()` return type: `float → dict` (breaking change; all callers updated)
- All MK function minimum-n guards unified to `MIN_N = 10`
- `build_table4_trends()` extended: `{m}_slope_lo`, `{m}_slope_hi` added for all methods
- Significance encoded as `"**"/"*"/"ns"` (not binary 0/1) in all tables

---

### Validation

Nine targeted unit tests run after corrections:
1. `sens_slope` dict structure and int() floor — PASS
2. `modified_mk_hamed_rao` VIF = 1.0 on white noise (n=34) — PASS
3. `prewhitening_mk` slope from original x, not whitened y — PASS
4. `tfpw_mk` slope not overridden — PASS
5. `MIN_N` guard: all four methods return NaN for n=5 — PASS
6. `field_significance_mks` returns all 8 mandatory columns — PASS
7. `_valid_year_mask` excludes years below 80% completeness — PASS
8. `aggregate_rainfall` excludes incomplete years (no totals from <80% data) — PASS
9. Full pipeline smoke-test with synthetic data — PASS (all steps run to completion)

