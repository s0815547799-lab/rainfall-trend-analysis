# DEFECT LOG — Rainfall Trend Analysis Repository

**Date:** 2026-06-11  
**Format:** Each entry includes ID, severity, location, description, scientific impact, and fix guidance.

Severity scale:
- **CRITICAL** — Produces incorrect published results or silently omits required outputs
- **MAJOR** — Introduces statistical bias, structural confusion, or reproducibility gap
- **MINOR** — Documentation error, dead code, or non-standard practice

---

## CRITICAL Defects

---

### C-01 — PW-MK: Sen's Slope Estimated on Prewhitened Series

**Severity:** CRITICAL  
**Files:** `rta/pw.py::pw_mk()`, `rta/trend_tests.py::pw_mk()`  
**Lines:** `rta/pw.py:82`, `rta/trend_tests.py:263`

**Description:**
When autocorrelation is significant and prewhitening is applied, the code computes:
```python
y = x[1:] - rho1 * x[:-1]    # prewhitened series
res = standard_mk(y)           # standard_mk calls sens_slope(y) internally
```
The returned `slope_Q`, `slope_lo`, `slope_hi` are therefore the Sen's slope of the
prewhitened residual `y`, not of the original rainfall series `x`. The prewhitened
series has different magnitude, units, and trend behaviour than the original data.

**Scientific Impact:**
Reported Sen's slope (mm/yr) and 95% CI for PW-MK results are **physically incorrect**
whenever `pw_applied=True`. Tables, figures (Fig 3, Fig 10, Fig 11), and Excel Sheet S7
that report Sen's slope for PW-MK will contain wrong values that contradict the original
data and the other three methods. This will be flagged by reviewers as a fundamental error.

**Correct Fix:**
After obtaining the MK test result on `y`, replace the slope fields with those from the
original series `x`:
```python
# Correct slope from original series
slope_orig, lo_orig, hi_orig = sens_slope(x)
res["slope_Q"]  = slope_orig
res["slope_lo"] = lo_orig
res["slope_hi"] = hi_orig
```
Apply to both `rta/pw.py::pw_mk()` and `rta/trend_tests.py::pw_mk()`.

---

### C-02 — Duplicate Module Implementations with Divergent Behaviour

**Severity:** CRITICAL  
**Files:** Multiple pairs (see table below)

**Description:**
The same scientific functions are implemented twice with differing logic:

| Function | Module A | Module B | Key Divergence |
|----------|----------|----------|----------------|
| `pw_mk` | `rta/pw.py` | `rta/trend_tests.py` | `rta/pw.py` checks `n<MIN_N` after prewhitening (line 79); `trend_tests.py` does not — will proceed with n<10 after prewhitening |
| `tfpw_mk` | `rta/tfpw.py` | `rta/trend_tests.py` | Essentially identical; both subject to C-01 slope issue |
| `field_sig_summary` | `rta/field_sig.py` | `rta/field_significance.py` | `field_sig.py` returns Walker/LC for **MK only**; `field_significance.py` returns results for **both MK and MMK** |
| `livezey_chen_mc` | `rta/field_sig.py` | `rta/field_significance.py` | Min series length: `≥4` vs `≥MIN_N(=10)` — different station eligibility |
| `load_coords` | `rta/io.py` | `rta/spatial.py` | Minor discovery pattern differences |
| Checkpoint I/O | `rta/io.py` | `rta/checkpoint.py` | Different API names: `save_checkpoint` vs `save`; same file format |

The v4 pipeline uses Module A for all functions; the v3 fallback import path uses Module B.
Bugs fixed in one do not propagate to the other.

**Scientific Impact:**
Any fix to PW-MK slope (C-01), the MIN_N post-prewhitening check, or field significance
coverage must be applied twice. If only one is fixed, the two pipelines produce
inconsistent results. This contradicts the CHANGELOG claim that v3 and v4 are numerically
identical (for PW-MK with significant AC, they will differ after the C-01 fix).

**Fix:** Consolidate to a single canonical implementation per function. v3 should import
from the same modules as v4. Remove the duplicate files or reduce them to thin re-exports.

---

### C-03 — v4 Pipeline Silently Missing Field Significance for Modified MK

**Severity:** CRITICAL  
**File:** `rta/field_sig.py::field_sig_summary()`, lines 252–283  
**Used by:** `rainfall_trend_analysis_v4.py` line 316

**Description:**
`field_sig_summary()` in `rta/field_sig.py` counts `N_sig_MMK` (stations significant
under Modified MK) but does **not** run the Walker or Livezey-Chen test for MMK.
The returned DataFrame is missing columns `Walker_p_MMK`, `Walker_sig_MMK`,
`LC_p_MMK`, `LC_sig_MMK`.

The v3-path implementation (`rta/field_significance.py::field_sig_summary()`)
correctly returns these columns for both MK and MMK.

**Scientific Impact:**
Excel Sheet S8 (Field Significance) in the v4 output contains no Walker or LC
test results for Modified MK — precisely the method that is most appropriate when
autocorrelation exists. A reviewer asking "is the dry-season trend field-significant
under the autocorrelation-corrected test?" will find no answer in the v4 Excel output.

**Fix:** Add Walker and LC tests for MMK inside `rta/field_sig.py::field_sig_summary()`,
matching the structure in `rta/field_significance.py`. Return columns:
`Walker_p_MMK`, `Walker_sig_MMK`, `LC_p_MMK`, `LC_sig_MMK`.

---

### C-04 — PW-MK Does Not Check Minimum n After Prewhitening (trend_tests.py path)

**Severity:** CRITICAL  
**File:** `rta/trend_tests.py::pw_mk()`, lines 253–268  
**Contrast:** `rta/pw.py::pw_mk()` line 79 correctly checks `len(y) < MIN_N`

**Description:**
After prewhitening, the series `y` has length `n−1`. If the original series has
exactly `MIN_N = 10` observations, `y` has 9 observations. The `trend_tests.py`
implementation proceeds to call `standard_mk(y)` with n=9, which internally checks
`n < MIN_N` and returns a null result anyway, but the null result has `method = None`
(standard_mk's null result) rather than `method = "PW-MK"`. The returned dict is then
modified to add `pw_applied`, `rho_1_used`, `method = "PW-MK"`, masking the null.

More dangerously: if a future edit changes the `standard_mk` null check, this path
would silently compute MK on 9 observations without the minimum sample size guard.

**Scientific Impact:**
For stations/scales with exactly 10 complete years, the PW-MK result via
`rta/trend_tests.py` is undefined/unreliable when prewhitening is applied.

**Fix:** Add `if len(y) < MIN_N: return null_base` after constructing `y` in
`rta/trend_tests.py::pw_mk()`, matching `rta/pw.py`.

---

### C-05 — `field_sig.py::livezey_chen_mc()` Uses `len(a) >= 4` Instead of `MIN_N`

**Severity:** CRITICAL  
**File:** `rta/field_sig.py::livezey_chen_mc()`, line 131  
**Contrast:** `rta/field_significance.py::livezey_chen_mc()` uses `MIN_N = 10` at line 130

**Description:**
`rta/field_sig.py::livezey_chen_mc()` includes stations with `len(a) >= 4` in the
Monte Carlo. `rta/field_significance.py::livezey_chen_mc()` uses `len(a) >= MIN_N`
(10 years minimum, consistent with the trend test minimum sample requirement).

Also in `rta/field_sig.py::field_sig_summary()`, station eligibility at line 229
uses `len(arr) >= 4` instead of `len(arr) >= MIN_N`, creating inconsistency with
the MK tests which require `MIN_N = 10`.

**Scientific Impact:**
Stations with 4–9 complete years would pass the LC null test filter but fail the
actual MK test filter. Their observed p-value would be 1.0 (from MK null return),
making them always non-significant, artificially inflating `N_stations` and
deflating the observed fraction `S_obs`. This biases the field significance test
toward non-significance.

**Fix:** Replace `len(a) >= 4` with `len(a) >= MIN_N` in both locations within
`rta/field_sig.py`.

---

## MAJOR Defects

---

### M-01 — Sen's Slope CI Upper Bound Missing +1

**Severity:** MAJOR  
**File:** `rta/trend_tests.py::sens_slope()`, line 90  
Also in `rainfall_trend_analysis_v3.py`, same line

**Description:**
```python
hi_r = min(N - 1, int(round((N + C_alpha) / 2.0)))
```
Per Gilbert (1987) Eq. 14.2, the upper confidence rank (1-indexed) is
`M₂ = (N + Cα)/2 + 1`. In 0-based indexing: `hi_r = int((N + Cα)/2)`.
The `+ 1` in the formula is missing, making `hi_r` one rank short.

**Numerical Impact:** For n=34, N=561, Cα ≈ 50; the error = 1/561 of the slope range.
Numerically small but technically incorrect. The CI is reported as slightly narrower
than the exact Gilbert (1987) bound.

**Fix:**
```python
hi_r = min(N - 1, int(math.floor((N + C_alpha) / 2.0)))
```
(Using `floor` matches the ceiling/floor interpretation of Gilbert's rank pair.)

---

### M-02 — Wet-Days/yr: Numerator-Denominator Year-Count Mismatch

**Severity:** MAJOR  
**File:** `rta/aggregation.py::descriptive_stats()`, line 148

**Description:**
```python
d = df_daily[s].dropna()
w = d[d >= WET_THR]
n = len(v)    # v = ann[s].dropna() — annual series with 80% threshold applied
"Wet-days/yr": round(float(len(w) / n), 1)
```
`d` is the full daily series (all non-NaN days across the entire record). If some
annual years are excluded due to the 80% completeness threshold, their daily values
(including wet days) remain in `d` but those years do not contribute to `n`.
The ratio `len(w)/n` thus has wet-day counts from more years in the numerator
than there are years in the denominator.

**Fix:** Count wet days only in years where the annual value is non-NaN:
```python
valid_years = ann[s].dropna().index.year
mask = df_daily.index.year.isin(valid_years)
d_valid = df_daily.loc[mask, s].dropna()
w_valid = d_valid[d_valid >= WET_THR]
"Wet-days/yr": round(float(len(w_valid) / n), 1) if n > 0 else np.nan
```

---

### M-03 — `_mk_s_fast` Is Not Vectorized Despite Its Name

**Severity:** MAJOR  
**File:** `rta/trend_tests.py::_mk_s_fast()`, lines 43–48  
Also in `rainfall_trend_analysis_v3.py`, lines 401–411

**Description:**
```python
for i in range(n - 1):
    S += int(np.sum(np.sign(x[i+1:] - x[i])))
```
The outer loop is O(n) Python iterations. True vectorization would be:
```python
diff = x[:, None] - x[None, :]          # (n × n) broadcast
S = int(np.sum(np.sign(diff[np.triu_indices(n, k=1)])))
```
For n=34 the performance impact is negligible, but the name "fast" is misleading
and may cause confusion if this is applied to larger datasets in the future.

**Note:** The `mk_s_ties` function (in the same file) is dead code (never called)
and also uses `np.sum(generator)` which is an anti-pattern.

**Fix:** Rename `_mk_s_fast` to `_mk_s_vectorized` and replace the outer Python loop
with a proper O(1) Python-overhead implementation. Remove `mk_s_ties`.

---

### M-04 — LC Monte Carlo Ignores Spatial Correlation Between Stations

**Severity:** MAJOR  
**File:** `rta/field_sig.py::livezey_chen_mc()`, `rta/field_significance.py::livezey_chen_mc()`

**Description:**
Each station's time series is independently permuted. For the 12 stations in the
Prachuap Khiri Khan basin (geographic extent ~150 km), inter-station rainfall
correlations are likely substantial (r > 0.5 between adjacent gauges is common in
such basins). Independent permutation treats the stations as uncorrelated, which
underestimates the width of the null distribution and makes the test anti-conservative
(more likely to falsely declare field significance).

Livezey & Chen (1983) explicitly address spatial correlation in their framework.

**Fix Options:**
1. Use block-bootstrap permutation that preserves spatial structure (more complex).
2. Report the limitation explicitly in results/methods and note that the test is
   anti-conservative for the current network density.
3. Apply Benjamini-Hochberg FDR correction as an alternative field-wide test
   (already implemented in `Comparative_4MMK.py`).

---

### M-05 — Outliers Flagged but Not Removed from Analysis Dataset

**Severity:** MAJOR  
**File:** `rta/io.py::quality_control()`, lines 119–120

**Description:**
```python
n_out = int((series > upper_fence).sum())   # count only
# outliers are NOT set to NaN
```
Values above the Q3+3×IQR fence of wet-day values are counted and reported but
remain in the dataset for all subsequent analysis including trend tests. For Q1
journals, the treatment of extreme values must be explicitly decided:
either (a) confirm they are genuine events and justify inclusion, or
(b) flag them as suspicious, set to NaN, and document the decision.

The current approach of flagging-but-keeping is problematic because it implies
the values are unreliable (triggering the outlier flag) yet are used without
correction or justification.

---

### M-06 — CMIP6 Subdirectories Committed to Repository

**Severity:** MAJOR  
**Files:** `CMIP6_package/`, `CMIP6_MME_v2/`, `CMIP6_MME_v2_FINAL_RELEASE.zip`

**Description:**
Two complete CMIP6 multi-model ensemble projects and a 22 MB zip archive are
committed to this rainfall trend analysis repository. These are unrelated projects
that belong in their own repositories.

The binary zip file (`CMIP6_MME_v2_FINAL_RELEASE.zip`) is permanent in git history
even after deletion. The shapefiles (`30_amarea_prachuap_khiri_khan.*`) and
the comprehensive analysis Excel workbook are similarly committed binary files.

**Impact:** Repository size inflation, confusing project scope, risk of
accidentally treating CMIP6 code as part of the rainfall analysis pipeline.

**Fix:** Move CMIP6 packages to separate repositories. Add binary output files and
large data files to `.gitignore`. The CMIP6 zip cannot be removed from history
without a `git filter-repo` operation.

---

### M-07 — `Comparative_4MMK.py` Has Undeclared Dependencies

**Severity:** MAJOR  
**File:** `Comparative_4MMK.py`, lines 51–79

**Description:**
This script imports `statsmodels`, `seaborn`, and optionally `pymannkendall`
and `geopandas`. None of these appear in the README.md dependency list.
Running the script in the documented environment will fail with ImportError.

**Fix:** Either add these to a separate `requirements_comparative.txt` or move
`Comparative_4MMK.py` to a separate sub-project with its own requirements file.

---

### M-08 — No Machine-Readable Dependency Specification

**Severity:** MAJOR  
**File:** None exists (gap)

**Description:**
Package versions are documented in README.md prose but there is no
`requirements.txt`, `pyproject.toml`, or `environment.yml`. The standard
reproducibility mechanism (`pip install -r requirements.txt`) is unavailable.

**Fix:** Create `requirements.txt`:
```
numpy==2.4.6
pandas==3.0.3
scipy==1.17.1
matplotlib==3.10.9
openpyxl==3.1.5
```
For `Comparative_4MMK.py`, create `requirements_comparative.txt` adding:
`statsmodels`, `seaborn`, `pymannkendall`, `geopandas`.

---

### M-09 — Two Checkpoint Systems with Different APIs

**Severity:** MAJOR  
**Files:** `rta/io.py` (lines 140–205), `rta/checkpoint.py`

**Description:**
Checkpoint functionality is implemented twice:
- `rta/io.py` exports `save_checkpoint`, `load_checkpoint`, `list_checkpoints`
- `rta/checkpoint.py` exports `save`, `load`, `list_steps`, `prompt_resume`

v4 main (`rainfall_trend_analysis_v4.py`) imports from `rta.io`.
v3 fallback import tries `rta.checkpoint`.
Both write `ckpt_{name}.pkl` files in the same format.

**Fix:** Remove the checkpoint functions from `rta/io.py` and import from
`rta/checkpoint.py` instead (consistent canonical source). Update v4 main imports.

---

### M-10 — `mk_s_ties` Is Dead Code with np.sum(generator) Anti-Pattern

**Severity:** MAJOR  
**File:** `rta/trend_tests.py`, lines 26–35. Also `rainfall_trend_analysis_v3.py` lines 388–397

**Description:**
```python
S = int(np.sum(np.sign(x[j] - x[i])
               for i in range(n-1) for j in range(i+1, n)))
```
`np.sum()` on a Python generator creates a Python iterator and calls the C-level
sum; it does not dispatch the vectorized NumPy path. This is an anti-pattern that
will produce a deprecation warning in future NumPy versions.

More critically, `mk_s_ties` is never called anywhere in the codebase. `_mk_s_fast`
is used by all callers. The dead function creates confusion about which is canonical.

**Fix:** Remove `mk_s_ties` from both files.

---

## MINOR Defects

---

### m-01 — CLAUDE.md Completeness Threshold Differs from Code

**Severity:** MINOR  
**File:** `CLAUDE.md` §6.2 vs `rta/aggregation.py::aggregate_all()`

**Description:**
CLAUDE.md §6.2 states "≥60% of days" for wet and dry seasons, but the code applies
80% for all scales. The documentation is incorrect.

**Fix:** Update CLAUDE.md §6.2 to state "≥80% of days for all temporal scales".

---

### m-02 — `calval_split.py` Is Undocumented

**Severity:** MINOR  
**File:** `calval_split.py`

**Description:**
A calibration/validation split utility script is present in the repo root but
not mentioned in CLAUDE.md, README.md, or CHANGELOG.md. Its purpose
(likely comparing observed vs CMIP6 model output) is unclear in context.

**Fix:** Add a brief entry to CLAUDE.md and README.md, or move to `CMIP6_package/`.

---

### m-03 — Taylor Diagram (Fig 9) Non-Standard for Trend Papers

**Severity:** MINOR  
**File:** `rta/figures/taylor.py`

**Description:**
Taylor diagrams are designed for model performance evaluation (comparing modelled
vs observed statistics). Using them for station-vs-regional-mean comparison in a
trend analysis paper is unconventional. Q1 hydrology reviewers may question its
inclusion or request justification.

**Fix:** Either (a) add a justification sentence in the methods section about why
the Taylor diagram is included (spatial coherence assessment), or (b) replace with
a more standard inter-station correlation heatmap.

---

### m-04 — Missing Shapiro-Wilk / ADF / Pettitt Tests

**Severity:** MINOR  
**File:** Codebase-wide (gap)

**Description:**
For Q1 hydrology publications, authors typically report:
- Shapiro-Wilk normality test on annual series (to characterize distribution)
- Augmented Dickey-Fuller or KPSS stationarity test (to support or contradict trend conclusions)
- Pettitt or CUSUM change-point test (to distinguish gradual trends from abrupt shifts)

None of these are computed by the pipeline. They are not required for valid MK analysis
but are expected by reviewers in the target journals.

**Fix:** Add these as optional outputs (descriptive statistics sheet or separate sheet).

---

### m-05 — Shapefiles and Output Files Committed to Git

**Severity:** MINOR  
**Files:** `30_amarea_prachuap_khiri_khan.*`, `Observed_Rain_daily_198101_201412_Prachuap Khiri Khan_ComprehensiveAnalysis.xlsx`

**Description:**
Binary geographic files and output Excel workbooks are tracked in git. These should
be either ignored via `.gitignore` or managed via Git LFS for large binaries.

**Fix:** Add to `.gitignore`:
```
*.dbf
*.shx
*.shp
*.prj
Observed_Rain_*.xlsx
CMIP6_MME_v2_FINAL_RELEASE.zip
```

---

### m-06 — `savefig.dpi` Set Redundantly in Both rcParams and Function Call

**Severity:** MINOR  
**File:** `rta/config.py` lines 79, 176

**Description:**
```python
"savefig.dpi": DPI,   # in rcParams
fig.savefig(..., dpi=DPI, ...)  # in savefig() function
```
The explicit `dpi=DPI` argument overrides the rcParam anyway, so the rcParam entry
is redundant. Harmless but creates potential for confusion if DPI is changed in one
place but not the other.

**Fix:** Remove `"savefig.dpi": DPI` from rcParams since `savefig()` always passes
`dpi=DPI` explicitly.

---

### m-07 — TFPW-MK Sen's Slope Slightly Biased When PW Applied

**Severity:** MINOR  
**File:** `rta/tfpw.py::tfpw_mk()`, `rta/trend_tests.py::tfpw_mk()`

**Description:**
When `pw_applied=True`, `standard_mk(z)` is called on the trend-restored series
`z = y + β·t₂` where `y = x_d[1:] − ρ₁·x_d[:-1]` (length n-1). The `sens_slope(z)`
inside `standard_mk` operates on n-1 points and a time axis shifted by 1.
While the trend β has been restored, the reduced series length slightly alters the
slope estimate compared to the full original series.

**Actual impact is small** (1 observation removed from a 34-year series), but for
transparency, the Sen's slope should ideally be reported from the original n-point
series for all four methods.

---

### m-08 — CHANGELOG VERSION Tag Inconsistency

**Severity:** MINOR  
**Files:** `CHANGELOG.md` line 7, `rta/config.py` line 24

**Description:**
CHANGELOG header reads `[v4.0_hydroclimatology_Q1]` but `rta/config.py` has
`VERSION = "4.0"`. Output files use the prefix `Output_TrendV4_*`. Three different
version strings for the same release. Adopt a single canonical form.

**Fix:** Use `v4.0` consistently across CHANGELOG, config, and README.
