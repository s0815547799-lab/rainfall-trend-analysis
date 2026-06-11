# PRIORITY FIX LIST — Rainfall Trend Analysis

**Date:** 2026-06-11  
**Purpose:** Ranked action items for pre-submission remediation.  
**Source:** `DEFECT_LOG.md` and `AUDIT_REPORT.md`

Items are ordered: CRITICAL issues (result correctness) → MAJOR issues (completeness/bias)
→ MINOR issues (housekeeping). Within each severity level, items are ordered by ease
of fix and impact on Q1 reviewability.

---

## Tier 1 — Fix Before Any Submission (CRITICAL)

These issues produce incorrect published results or silently omit required output.

---

### FIX-01 — Correct PW-MK Sen's Slope to Use Original Series

**Defect:** C-01  
**Effort:** Low (4 lines per file)  
**Impact:** Corrects wrong β values in all PW-MK rows in tables, figures, and Excel

In `rta/pw.py::pw_mk()` (line 82) and `rta/trend_tests.py::pw_mk()` (line 263),
replace `standard_mk(y)` with a version that retains the MK test statistics from
`y` but the Sen's slope from `x`:

```python
# Current (wrong):
res = standard_mk(y)

# Correct:
res = standard_mk(y)                      # MK test on prewhitened series
slope_Q, slope_lo, slope_hi = sens_slope(x)  # slope from ORIGINAL series
res["slope_Q"]  = round(slope_Q,  3) if not np.isnan(slope_Q)  else np.nan
res["slope_lo"] = round(slope_lo, 3) if not np.isnan(slope_lo) else np.nan
res["slope_hi"] = round(slope_hi, 3) if not np.isnan(slope_hi) else np.nan
```

Apply to both `rta/pw.py` and `rta/trend_tests.py`.

**Verify:** After fix, PW-MK slope for any given station should be numerically
close (within AC-induced rounding) to the Standard MK slope for the same station.

---

### FIX-02 — Add MMK Field Significance to `rta/field_sig.py`

**Defect:** C-03  
**Effort:** Medium (~20 lines)  
**Impact:** Fills silent gap in Excel Sheet S8; required for Q1 completeness

In `rta/field_sig.py::field_sig_summary()`, add Walker and LC tests for Modified MK
analogously to the existing MK block:

```python
from .trend_tests import modified_mk  # already imported at module bottom

# After existing MK Walker/LC block, add:
wt_mmk = walker_test(n_stn, n_sig_mmk, alpha=alpha)
lc_mmk = livezey_chen_mc(mmk_series, alpha=alpha, n_perm=n_perm)

# Add to the rows.append() dict:
"Walker_p_MMK":  wt_mmk["p_walker"],
"Walker_sig_MMK": wt_mmk["field_significant"],
"LC_p_MMK":      lc_mmk["p_field_LC"],
"LC_sig_MMK":    lc_mmk["field_significant"],
```

The MMK `series_dict` is identical to the MK one (same data, different test).

---

### FIX-03 — Add Post-Prewhitening MIN_N Check in `trend_tests.py::pw_mk()`

**Defect:** C-04  
**Effort:** Low (2 lines)  
**Impact:** Prevents analysis on series too short after prewhitening

In `rta/trend_tests.py::pw_mk()`, after constructing `y`:

```python
y = x[1:] - rho1 * x[:-1]

# ADD:
if len(y) < MIN_N:
    null_base["rho_1_used"] = float(rho1)
    return null_base
```

---

### FIX-04 — Fix `field_sig.py` Min Series Length to Use MIN_N

**Defect:** C-05  
**Effort:** Low (2 substitutions)  
**Impact:** Ensures station eligibility is consistent with the MK test minimum

In `rta/field_sig.py`:
1. `livezey_chen_mc()` line 131: change `if len(a) >= 4:` → `if len(a) >= MIN_N:`
2. `field_sig_summary()` line 229: change `if len(arr) >= 4:` → `if len(arr) >= MIN_N:`

Add `from .config import MIN_N` if not already imported (it's already imported at line 4).

---

### FIX-05 — Consolidate Duplicate Module Implementations

**Defect:** C-02  
**Effort:** High (refactoring; test after each change)  
**Impact:** Ensures fixes propagate to both v3 and v4 paths; eliminates drift risk

Recommended consolidation strategy:

1. **`pw_mk` / `tfpw_mk`:** Make `rta/pw.py` and `rta/tfpw.py` thin wrappers
   that import from `rta/trend_tests.py`:
   ```python
   # rta/pw.py (simplified after consolidation)
   from .trend_tests import pw_mk  # noqa: F401 — re-export for v3 backward compat
   ```

2. **`field_sig_summary`:** Make `rta/field_significance.py` import from `rta/field_sig.py`:
   ```python
   # rta/field_significance.py
   from .field_sig import walker_test, livezey_chen_mc, field_sig_summary  # noqa: F401
   ```

3. **`load_coords`:** Make `rta/io.py::load_coords` call `rta.spatial.load_coords`.

4. **Checkpoint:** Remove checkpoint functions from `rta/io.py`; import
   `save`, `load`, `list_steps` from `rta.checkpoint` inside `rta/io.py`:
   ```python
   from .checkpoint import save as save_checkpoint, load as load_checkpoint, list_steps as list_checkpoints
   ```

**Prerequisite:** Apply FIX-01, FIX-02, FIX-03, FIX-04 before consolidating so
the canonical implementation is already correct.

---

## Tier 2 — Fix Before Final Submission (MAJOR)

These issues introduce statistical bias, incomplete outputs, or reproducibility gaps.

---

### FIX-06 — Correct Sen's Slope CI Upper Bound

**Defect:** M-01  
**Effort:** Low (1 line)

In `rta/trend_tests.py::sens_slope()` line 90, and
`rainfall_trend_analysis_v3.py` at the equivalent line:

```python
# Current:
hi_r = min(N - 1, int(round((N + C_alpha) / 2.0)))

# Correct (Gilbert 1987, Eq 14.2):
hi_r = min(N - 1, int(math.floor((N + C_alpha) / 2.0)))
```

Note: The `round` → `floor` change also matches the textbook convention
(rank-based bounds are floored, not rounded). The impact for typical sample
sizes (n=30–35) is at most one slope rank.

---

### FIX-07 — Fix Wet-Days/yr to Use Only Valid Annual Years

**Defect:** M-02  
**Effort:** Low (4 lines)

In `rta/aggregation.py::descriptive_stats()`:

```python
# Current:
d = df_daily[s].dropna()
w = d[d >= WET_THR]
# ...
"Wet-days/yr": round(float(len(w) / n), 1) if n > 0 else np.nan,

# Replace with:
valid_years = ann[s].dropna().index.year
d_valid = df_daily.loc[df_daily.index.year.isin(valid_years), s].dropna()
w_valid = d_valid[d_valid >= WET_THR]
"Wet-days/yr": round(float(len(w_valid) / n), 1) if n > 0 else np.nan,
```

---

### FIX-08 — Document / Justify Outlier Treatment Policy

**Defect:** M-05  
**Effort:** Low (documentation + optional code change)

Either:
- (a) Add a sentence in the methods section and CLAUDE.md stating: "Extreme daily values
  above the Q3+3×IQR threshold are flagged in the QC report. Following WMO guidelines
  for historical rainfall data, these values are retained as potentially genuine extreme
  events unless they exceed physically plausible maxima for the region."
- (b) Add a flag `remove_outliers=False` parameter to `quality_control()` so the
  behaviour is explicit and configurable.

---

### FIX-09 — Add requirements.txt

**Defect:** M-08  
**Effort:** Trivial

Create `/requirements.txt`:
```
numpy==2.4.6
pandas==3.0.3
scipy==1.17.1
matplotlib==3.10.9
openpyxl==3.1.5
```

Create `/requirements_comparative.txt` (for `Comparative_4MMK.py`):
```
numpy==2.4.6
pandas==3.0.3
scipy==1.17.1
matplotlib==3.10.9
statsmodels>=0.14.0
seaborn>=0.12.0
pymannkendall>=1.4.0
geopandas>=0.14.0
```

---

### FIX-10 — Note Spatial Correlation Limitation in Methods

**Defect:** M-04  
**Effort:** Documentation only

Add to research summary and CLAUDE.md §10:
"The Livezey-Chen Monte Carlo test uses independent temporal permutation of each
station's series. For geographically proximate gauging stations, this assumption may
not hold; inter-station spatial correlation inflates the apparent significance of
field-wide tests (anti-conservative). Results should be interpreted accordingly."

---

### FIX-11 — Remove or Separate CMIP6 Subdirectories

**Defect:** M-06  
**Effort:** Medium (git history cannot be cleaned without filter-repo)

1. Create separate repositories for `CMIP6_package/` and `CMIP6_MME_v2/`.
2. Delete these directories from this repository.
3. Add to `.gitignore`: `CMIP6_*/`, `*.zip`, `Observed_Rain_*.xlsx`.
4. Note: `CMIP6_MME_v2_FINAL_RELEASE.zip` is permanent in git history unless
   `git filter-repo --invert-paths --path CMIP6_MME_v2_FINAL_RELEASE.zip` is run.

---

### FIX-12 — Consolidate Checkpoint Systems

**Defect:** M-09  
**Effort:** Low (redirect imports)

Remove the checkpoint functions from `rta/io.py` and replace with imports from
`rta/checkpoint.py`. Update `rainfall_trend_analysis_v4.py` to import from
`rta.checkpoint` directly.

---

### FIX-13 — Remove Dead Code (`mk_s_ties`)

**Defect:** M-10  
**Effort:** Trivial

Delete the `mk_s_ties` function from:
- `rta/trend_tests.py` (lines 26–35)
- `rainfall_trend_analysis_v3.py` (lines 388–397)

---

## Tier 3 — Fix Before Camera-Ready (MINOR)

These are housekeeping items that polish the submission package.

---

### FIX-14 — Correct CLAUDE.md Completeness Threshold Documentation

**Defect:** m-01  
**File:** `CLAUDE.md` §6.2

Change "≥60% of days" for dry/wet seasons to "≥80% of days" to match the code.

---

### FIX-15 — Add `calval_split.py` to Documentation

**Defect:** m-02  
**Effort:** Trivial

Add a one-paragraph entry to CLAUDE.md §1 describing `calval_split.py` as a
calibration/validation split script for CMIP6 model comparison. Or move it to
the CMIP6 sub-project.

---

### FIX-16 — Add Optional Normality / Stationarity / Change-Point Tests

**Defect:** m-04  
**Effort:** Medium

Suggested additions to `rta/aggregation.py` or as a new `rta/supplemental_tests.py`:
- Shapiro-Wilk normality test (`scipy.stats.shapiro`) on annual series
- Augmented Dickey-Fuller stationarity test (`statsmodels.tsa.stattools.adfuller`)
- Pettitt change-point test (available in `pymannkendall` or implement directly)

These should be reported in Excel Sheet S5 (Descriptive Statistics) as extra columns.

---

### FIX-17 — Update .gitignore to Exclude Binary/Output Files

**Defect:** m-05  
**Effort:** Trivial

Add to `.gitignore`:
```
# Geographic data
*.shp
*.dbf
*.shx
*.prj

# Generated outputs
Observed_Rain_*.xlsx
Output_Trend*
CMIP6_MME_v2_FINAL_RELEASE.zip
checkpoints/
results/
```

---

### FIX-18 — Remove Redundant `savefig.dpi` from rcParams

**Defect:** m-06  
**File:** `rta/config.py` line 79  
**Effort:** Trivial

Delete the line `"savefig.dpi": DPI,` from the `plt.rcParams.update()` dict.

---

### FIX-19 — Unify VERSION String

**Defect:** m-08  
**Files:** `CHANGELOG.md`, `rta/config.py`, `README.md`  
**Effort:** Trivial

Standardise to `v4.0` everywhere. Change CHANGELOG heading from
`[v4.0_hydroclimatology_Q1]` to `[v4.0]`.

---

---

## CMIP6 Sub-Project Fixes

The following items apply to `CMIP6_package/` (v1) and `CMIP6_MME_v2/` (v2).
Items are ordered: CRITICAL → MAJOR → MINOR within each tier.

---

## CMIP6 Tier 1 — Fix Before Any CMIP6 Submission (CRITICAL)

---

### FIX-C01 — Document or Implement Calendar Harmonisation

**Defect:** CC-01  
**Effort:** Low (documentation) or High (implementation)  
**Impact:** Without this, the entire CMIP6 analysis is not reproducible

Choose one:

**(a) Documentation path (faster):**
Add to methods section and `CMIP6_MME_v2/README.md`:
> "All CMIP6 daily rainfall series were extracted from NetCDF using [tool name and version].
> Calendar harmonisation to the proleptic Gregorian calendar was applied by [method: e.g.,
> dropping Feb-29 for noleap models / linear interpolation for 360_day models]. The
> extraction script is archived at [DOI/URL]."

**(b) Implementation path (more robust):**
Add an `xarray`/`cftime`-based ingestion step that reads raw CMIP6 NetCDFs and
converts all calendar types to a common Gregorian basis before CSV export.

---

### FIX-C02 — Document or Implement Bias Correction

**Defect:** CC-02  
**Effort:** Low (documentation) or Very High (implementation)  
**Impact:** Without this, absolute projected change values are unverifiable

Choose one:

**(a) Documentation path:**
Add a "Bias Correction" subsection to `CMIP6_MME_v2/README.md`:
> "Bias correction was applied using [QDM / Quantile Mapping / Delta Change] with
> the 1981–2014 observed period as the reference. The correction was implemented
> using [software, e.g., MBC R package, BCSA Python]. Bias-corrected daily series
> are archived at [Zenodo DOI]."

**(b) Implementation path:**
Implement QDM (Cannon et al. 2015) in `CMIP6_MME_v2/src/bias_correction/qdm.py`.

---

### FIX-C03 — Fix `CMIP6_package` MME NaN Percentile Bug

**Defect:** CC-03  
**Effort:** Trivial (4 lines in one file)  
**Impact:** Corrects P25/P75 ensemble spread values in all v1 tables and figures

In `CMIP6_package/src/ensemble/mme.py`, replace:
```python
# Current (wrong):
p25=lambda s: np.percentile(s, 25),
p75=lambda s: np.percentile(s, 75),
```
With:
```python
# Correct (NaN-safe):
p25=lambda s: float(np.percentile(s.dropna(), 25)) if s.notna().any() else np.nan,
p75=lambda s: float(np.percentile(s.dropna(), 75)) if s.notna().any() else np.nan,
```

---

## CMIP6 Tier 2 — Fix Before Final Submission (MAJOR)

---

### FIX-C04 — Fix Anomaly Baseline in `fig3_anomaly_ts()`

**Defect:** CM-05  
**Effort:** Low (~5 lines)  
**Impact:** Makes anomaly figure reproducible across different future window configurations

In `CMIP6_MME_v2/src/figures/make.py::fig3_anomaly_ts()`, replace the grand-mean baseline
with the configured baseline period:
```python
# Current (wrong):
baseline_mean = series.mean()

# Correct:
baseline_years = range(cfg["periods"]["baseline"]["start"],
                       cfg["periods"]["baseline"]["end"] + 1)
baseline_mean = series[series.index.isin(baseline_years)].mean()
```

---

### FIX-C05 — Fix Change% to Compute Per-Model First

**Defect:** CM-03  
**Effort:** Low (~10 lines)  
**Impact:** Correctly represents asymmetric inter-model spread in projected changes

Refactor `compute_change_pct()` in both packages:
```python
# Correct approach:
for model in models:
    future_val   = future_df[model]
    baseline_val = baseline_df[model]
    change_pct[model] = 100.0 * (future_val - baseline_val) / baseline_val
# Then: mean/median/P25/P75 of change_pct across models
```

---

### FIX-C06 — Fix Hardcoded Scenarios in `CMIP6_package` Figures

**Defect:** CM-01  
**Effort:** Low (search-and-replace)  
**Impact:** Allows v1 figures to respect `config.yaml` scenario settings

In `CMIP6_package/src/figures/make.py`, replace:
```python
SCEN = ["ssp245", "ssp585"]
for scn in ["historical", "ssp245", "ssp585"]:
```
With:
```python
SCEN = cfg.get("scenarios", ["ssp245", "ssp585"])
for scn in ["historical"] + SCEN:
```

---

### FIX-C07 — Add KGE `ddof=1` or Document Convention

**Defect:** CM-07  
**Effort:** Trivial (1–2 lines + documentation)

In `CMIP6_MME_v2/src/validation/metrics.py::kge()`, change:
```python
sigma_s = np.std(sim, ddof=1)   # sample std, matching Gupta et al. (2009)
sigma_o = np.std(obs, ddof=1)
```
Or document explicitly that `ddof=0` is intentional.

---

### FIX-C08 — Add MK Trend Analysis on Projected Series

**Defect:** CM-04  
**Effort:** Medium (~30 lines)  
**Impact:** Completes the trend analysis narrative for projected future windows

Add a `run_projected_trends()` function that loops over each model × each future
window × each temporal scale, calls `standard_mk()` and `sens_slope()`, and
reports Sen's slope (mm/yr), Z, p-value, and trend direction per model with MME statistics.

---

### FIX-C09 — Document Equal Model Weighting

**Defect:** CM-02  
**Effort:** Documentation only

Add to methods section:
> "All CMIP6 models are given equal weight in the multi-model ensemble. Model family
> redundancy was not corrected. Future work may apply performance-based weighting
> (e.g., ClimWIP, Knutti et al. 2017)."

---

## CMIP6 Tier 3 — Fix Before Camera-Ready (MINOR)

---

### FIX-C10 — Fix `CMIP6_package` `load_metadata()` for CSV Input

**Defect:** Cm-01  
**Effort:** Trivial

In `CMIP6_package/src/utils/io.py::load_metadata()`, add:
```python
if path.suffix == ".csv":
    return pd.read_csv(path, ...)
```

---

### FIX-C11 — Fix `std = 0.0` for n=1 Stations

**Defect:** Cm-02  
**Effort:** Trivial

Replace bare `np.std(vals)` with:
```python
std = np.nan if len(vals) <= 1 else np.std(vals, ddof=1)
```

---

### FIX-C12 — Add Version Field to `config.yaml`

**Defect:** Cm-03  
**Effort:** Trivial

Add to both `config.yaml` files:
```yaml
meta:
  run_version: "2.0"
  description: "CMIP6 MME rainfall trend analysis — Prachuap Khiri Khan"
```

---

## Summary Table

### Rainfall Trend Analysis Pipeline

| ID | Severity | Description | Effort | Pre-submission? |
|----|----------|-------------|--------|----------------|
| FIX-01 | CRITICAL | PW-MK slope on original series | Low | ✓ Required |
| FIX-02 | CRITICAL | MMK field significance in v4 | Medium | ✓ Required |
| FIX-03 | CRITICAL | Post-PW MIN_N check | Low | ✓ Required |
| FIX-04 | CRITICAL | field_sig.py MIN_N consistency | Low | ✓ Required |
| FIX-05 | CRITICAL | Consolidate duplicate modules | High | ✓ Required |
| FIX-06 | MAJOR | Sen's slope CI upper bound | Low | ✓ Recommended |
| FIX-07 | MAJOR | Wet-days/yr year-count alignment | Low | ✓ Recommended |
| FIX-08 | MAJOR | Document outlier treatment | Low | ✓ Recommended |
| FIX-09 | MAJOR | Create requirements.txt | Trivial | ✓ Recommended |
| FIX-10 | MAJOR | Note LC spatial correlation limit | Docs | ✓ Recommended |
| FIX-11 | MAJOR | Remove CMIP6 subdirectories | Medium | Optional |
| FIX-12 | MAJOR | Consolidate checkpoint systems | Low | Optional |
| FIX-13 | MAJOR | Remove dead code mk_s_ties | Trivial | Optional |
| FIX-14 | MINOR | CLAUDE.md threshold correction | Trivial | Recommended |
| FIX-15 | MINOR | Document calval_split.py | Trivial | Optional |
| FIX-16 | MINOR | Add normality/ADF/Pettitt tests | Medium | Optional |
| FIX-17 | MINOR | Update .gitignore | Trivial | Recommended |
| FIX-18 | MINOR | Remove redundant rcParam DPI | Trivial | Optional |
| FIX-19 | MINOR | Unify VERSION string | Trivial | Optional |

**Minimum viable fix set for Q1 submission (rainfall pipeline):** FIX-01 through FIX-10.

### CMIP6 Sub-Projects

| ID | Severity | Description | Effort | Pre-submission? |
|----|----------|-------------|--------|----------------|
| FIX-C01 | CRITICAL | Document/implement calendar handling | Low–High | ✓ Required |
| FIX-C02 | CRITICAL | Document/implement bias correction | Low–Very High | ✓ Required |
| FIX-C03 | CRITICAL | CMIP6_package NaN percentile bug | Trivial | ✓ Required |
| FIX-C04 | MAJOR | Fix anomaly baseline to use configured period | Low | ✓ Recommended |
| FIX-C05 | MAJOR | Fix change% to compute per-model first | Low | ✓ Recommended |
| FIX-C06 | MAJOR | Fix hardcoded scenarios in v1 figures | Low | ✓ Recommended |
| FIX-C07 | MAJOR | KGE ddof convention | Trivial | ✓ Recommended |
| FIX-C08 | MAJOR | Add MK trend analysis on projected series | Medium | ✓ Recommended |
| FIX-C09 | MAJOR | Document equal model weighting | Docs | ✓ Recommended |
| FIX-C10 | MINOR | v1 load_metadata CSV support | Trivial | Optional |
| FIX-C11 | MINOR | std=NaN for n=1 | Trivial | Optional |
| FIX-C12 | MINOR | Add version to config.yaml | Trivial | Optional |

**Minimum viable fix set for Q1 submission (CMIP6):** FIX-C01 through FIX-C09.
