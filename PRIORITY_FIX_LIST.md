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

## Summary Table

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

**Minimum viable fix set for Q1 submission:** FIX-01 through FIX-10 (all CRITICAL + high-impact MAJOR).
