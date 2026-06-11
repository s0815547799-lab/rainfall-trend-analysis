# CMIP6 Scientific Review Report

**Date:** 2026-06-11  
**Scope:** `CMIP6_MME_v2/` and `CMIP6_package/` subdirectories  
**Reviewer:** Automated audit — static code analysis only  
**Purpose:** Pre-submission scientific review targeting Q1/Q2 hydroclimatology journal standards  
**Status:** Read-only — no code was modified

---

## Executive Summary

The two CMIP6 packages (`CMIP6_package/` v1 and `CMIP6_MME_v2/` v2) share the same conceptual architecture but differ substantially in robustness. Version 2 fixes several critical deficiencies present in version 1. However, **both versions share two fundamental omissions** that prevent Q1 publication without remediation: (1) **no calendar harmonisation code** for CMIP6 calendar variants (`noleap`, `360_day`, `proleptic_gregorian`), and (2) **no bias correction implementation** — the documentation and code both assume that bias correction has been applied externally before any CSV files are generated. These two omissions are not simple bugs; they represent entire methodological components that must either be implemented or explicitly documented as out-of-scope pre-processing steps with full methodological traceability.

**Severity counts:**

| Severity | Count |
|----------|-------|
| CRITICAL  | 3     |
| MAJOR     | 7     |
| MINOR     | 5     |

---

## Review Areas

---

### Area 1 — CMIP6 Data Handling

**Verdict: MAJOR concern**

Both packages ingest CMIP6 output via CSV files auto-discovered by filename regex. The discovery logic in `CMIP6_MME_v2/src/utils/io.py::discover_csv()` uses `re.search(r"station.*\.csv", f, re.IGNORECASE)`, which is more robust than the v1 equivalent. Station metadata is loaded via `load_metadata()`, which accepts both `.xlsx` and `.csv` in v2 but **only `.xlsx`** in `CMIP6_package/src/utils/io.py` — a v1 deficiency documented separately as MINOR-01.

The core assumption is that raw NetCDF CMIP6 files have been pre-processed into per-station CSVs with columns `[Year, Month, Day, <ModelName>_<Scenario>]`. No NetCDF reading, spatial regridding, or point-extraction code exists anywhere in the repository. This is a legitimate architectural boundary, but it must be stated explicitly in the methods section.

**Critical documentation gap:** The methods must state (a) what tool extracted station-level time series from CMIP6 NetCDF grids, (b) what spatial interpolation method was used (nearest-neighbour, bilinear, or distance-weighted?), (c) whether point values represent grid-cell centres or interpolated estimates, and (d) the temporal resolution of the raw CMIP6 output before daily aggregation.

---

### Area 2 — Historical and Future Period Definitions

**Verdict: MINOR concern**

Both packages read period boundaries from `config/config.yaml`:
```yaml
periods:
  baseline:    {start: 1981, end: 2014}
  near_future: {start: 2021, end: 2050}
  far_future:  {start: 2071, end: 2100}
```

The baseline period `1981–2014` matches the observed rainfall dataset exactly, which is scientifically appropriate for bias-corrected comparisons. The near-future `2021–2050` and far-future `2071–2100` are standard 30-year WMO climatological normal periods under SSP scenarios.

**Minor concern:** The configuration does not define a `mid_future` (2041–2070) window. Many Q1 hydrology papers include three future windows. This is a completeness issue, not an error.

**Minor concern:** No code validates that the loaded CMIP6 time series actually spans the configured periods. If a model's data terminates before 2100, the aggregation silently produces partial results without raising a warning.

---

### Area 3 — SSP Scenario Implementation

**Verdict: MAJOR concern (v1 only; resolved in v2)**

**CMIP6_MME_v2 (v2):** Scenarios are read dynamically from `cfg["scenarios"]` throughout all functions. `make_all_figures()` accepts `scenarios` as a parameter and passes it down. This is correct.

**CMIP6_package (v1) — MAJOR-01:** `CMIP6_package/src/figures/make.py` hardcodes scenarios in at least three separate places:
```python
SCEN = ["ssp245", "ssp585"]
# ...
for scn in ["historical", "ssp245", "ssp585"]:
```
If a user configures `config.yaml` with `scenarios: [ssp126, ssp370]`, the figures will silently produce wrong output (missing scenarios or KeyErrors). This is a correctness defect, not a style issue.

**Recommendation (v1):** Replace all hardcoded scenario lists with `cfg["scenarios"]` reads, as v2 already does.

---

### Area 4 — Calendar Handling

**Verdict: CRITICAL — CC-01**

**Finding:** Neither `CMIP6_package/` nor `CMIP6_MME_v2/` contains any code to handle CMIP6 calendar variants. A systematic search of all Python source files in both packages reveals no references to:
- `noleap` / `365_day` calendars
- `360_day` calendars
- `proleptic_gregorian` calendars
- `cftime`, `xarray.cftime_range`, or any calendar-aware datetime library
- Leap-day filtering, day-count normalisation, or February-29 handling

**Scientific significance:** CMIP6 models use at least four different calendar conventions:
| Calendar | Description | Leap years |
|----------|-------------|------------|
| `standard` | Gregorian | Yes |
| `proleptic_gregorian` | Standard, extended backward | Yes |
| `noleap` / `365_day` | Fixed 365 days/yr | No |
| `360_day` | Fixed 360 days/yr (12×30) | N/A |

When a `noleap` model series is ingested as if it were Gregorian, every year after the first contains an off-by-day accumulation. Over a 30-year period this can shift annual totals and seasonal boundaries by up to 30 days, producing systematically biased wet/dry season aggregations.

For daily rainfall specifically: a `360_day` model produces 360 values per year. If these are stored as `[YEAR, MONTH, DAY]` CSV columns using the model's internal calendar days (months of 30 days each), any code that uses `pd.to_datetime()` will fail silently on day 30 of months with 28/29/31 days in the Gregorian calendar, producing `NaT` values or dropped rows.

**Current workaround assumption:** The code presumably receives CSVs that have already been calendar-harmonised during the NetCDF extraction step. If so, this assumption **must be documented explicitly** and the extraction script must be included in the repository or referenced with a DOI/URL.

**Recommendation:** Either (a) document unambiguously in the methods that calendar harmonisation was applied during data extraction and describe the method used, or (b) implement calendar-aware ingestion using `xarray` + `cftime` before CSV generation. Without one of these, the analysis is not reproducible.

---

### Area 5 — Missing-Value Handling

**Verdict: MAJOR concern (v1 only for percentiles; both versions for period validation)**

**v2 — Temporal completeness gate:** `CMIP6_MME_v2/src/rainfall/seasonal.py::_wide_to_yearly()` applies a `min_completeness` parameter (default 0.8) correctly: years where the fraction of non-NaN values falls below the threshold are set to `NaN`. This matches the 80% gate used in the observed rainfall pipeline. ✓

**v1 — Same function exists with the same gate.** ✓

**CMIP6_package v1 — CRITICAL-02 (MME NaN propagation):**  
`CMIP6_package/src/ensemble/mme.py` uses `agg()` with lambda functions that do **not** guard against all-NaN slices:
```python
p25=lambda s: np.percentile(s, 25)
p75=lambda s: np.percentile(s, 75)
```
`np.percentile` on a series containing NaN returns NaN-contaminated results without error on older NumPy (< 1.22), and raises on newer NumPy with `nanpercentile` semantics. The v2 version correctly uses:
```python
p25=lambda s: float(np.percentile(s.dropna(), 25)) if s.notna().any() else np.nan
```

**v2 — Validation metrics (MAJOR-02):** `CMIP6_MME_v2/src/validation/metrics.py::validation_metrics()` performs a three-way intersection of observed, simulated, and period indices before computing KGE/NSE/PBIAS. This correctly handles missing years. ✓

**Both versions — model-year gap detection absent (MINOR-02):** No code warns when a specific CMIP6 model has large gaps within a period (e.g., missing years 2030–2035 within a 2021–2050 window). These gaps are silently treated as NaN and excluded from the completeness denominator, potentially producing misleading multi-model statistics.

---

### Area 6 — Bias Correction Methodology

**Verdict: CRITICAL — CC-02**

**Finding:** No bias correction code exists anywhere in `CMIP6_package/` or `CMIP6_MME_v2/`. A comprehensive search for the following methods found no implementations:

| Method | Search terms | Found |
|--------|-------------|-------|
| Quantile Delta Mapping (QDM) | `qdm`, `quantile_delta`, `delta_map` | Not found |
| Quantile Mapping (QM) | `quantile_map`, `empirical_cdf`, `transfer_func` | Not found |
| Delta Change / Delta Scaling | `delta_change`, `delta_scal`, `additive_bias` | Not found |
| BCSD | `bcsd`, `spatial_disagg` | Not found |
| Distribution mapping | `gamma_fit`, `fit_dist` | Not found |

**Scientific significance:** Bias correction is a standard prerequisite for CMIP6 impact assessments of rainfall at the station scale. Raw CMIP6 models have systematic wet/dry biases at the grid-cell level, particularly for daily rainfall intensity distributions. Without bias correction:
1. Absolute projected change values (mm/yr) are not meaningful against observed baselines.
2. Wet-day counts and extremes are not comparable between historical model output and observations.
3. KGE/NSE/PBIAS validation metrics, which are computed in the code, measure raw model skill rather than bias-corrected skill — these two are conceptually different quantities and must be clearly distinguished.

**Current assumption:** Like calendar handling, bias correction is presumed to have been applied before CSV generation. This is methodologically valid only if:
- The bias correction method is explicitly named (e.g., QDM per Cannon et al. 2015),
- The reference period, training/validation split, and software used are stated,
- The bias-corrected data files are archived or downloadable,
- The methods section does not imply that the raw CMIP6 output was used directly.

**Recommendation:** Add a dedicated §2 "Data Pre-Processing" subsection to the manuscript covering: NetCDF extraction method, spatial regridding scheme, calendar harmonisation approach, and bias correction method with full citation and parameter values.

---

### Area 7 — Ensemble Methodology

**Verdict: MAJOR concern (v1); Acceptable for v2 with minor caveats**

**v2 — `build_mme()` in `CMIP6_MME_v2/src/ensemble/mme.py`:**  
Computes `mean`, `median`, `p25`, `p75` across available models per station-year-season using `groupby().agg()` with NaN-safe lambda functions. ✓

The choice of multi-model statistics (mean + median + IQR envelope) is standard for CMIP6 ensembles and follows the IPCC AR6 approach.

**v1 — CRITICAL-02 (re-stated):** v1 uses non-NaN-safe percentile functions as noted in Area 5.

**MAJOR-03 — No model independence / weighting:**  
Neither version implements model independence testing or performance-based weighting. For an ensemble of CMIP6 models that share parameterisation schemes (e.g., multiple ACCESS or CESM variants), equal weighting overrepresents particular model families. This is a known bias in MME methodology (Knutti et al. 2017; Sanderson et al. 2015).

**Recommendation:** At minimum, document that equal weighting is used and acknowledge that model family redundancy is not corrected. For Q1 publication, consider citing the Climate Model Weighting by Independence and Performance (ClimWIP) approach or a simpler correlation-based independence metric.

**MAJOR-04 — Change% averaging level mismatch:**  
The `compute_change_pct()` function in the results tables computes percentage change relative to the baseline mean. However, the baseline mean is computed across all years in the baseline window **before** being passed into multi-model aggregation. The correct approach for change% in MME contexts is to compute change% per model first, then take the MME statistics of the change% values — not to compute MME statistics on absolute values and then compute the single change% of the MME mean. These two procedures produce different results whenever inter-model spread is asymmetric.

---

### Area 8 — Temporal Aggregation

**Verdict: Acceptable with minor caveats**

Both versions implement annual, wet-season (May–Oct), and dry-season (Nov–Apr hydrological year) aggregation consistently with the observed rainfall pipeline. The `_wide_to_yearly()` function applies the same 80% completeness gate. The hydrological year shifting (Nov/Dec of year Y → year Y+1) is implemented correctly. ✓

**MINOR-03 — Leap-day stripping inconsistency:**  
`CMIP6_MME_v2/src/rainfall/seasonal.py` calls `.loc[~((df.index.month==2) & (df.index.day==29))]` to strip leap days before aggregation. This is appropriate when comparing against `noleap` model calendars, but it means the observed series also loses February 29 data. This choice should be documented explicitly; alternatively, retain leap days throughout (CMIP6 models with `standard` calendars include them).

**MINOR-04 — Monthly aggregation absent:**  
The observed pipeline produces a `monthly` aggregation for climatology figures. The CMIP6 packages do not compute monthly aggregates. This means Fig 7 (monthly climatology) cannot be directly compared between observed and projected series unless monthly aggregation is added.

---

### Area 9 — Trend Analysis Validity After Bias Correction

**Verdict: MAJOR concern**

**MAJOR-05 — No MK trend analysis on projected CMIP6 series:**  
Neither package runs Mann-Kendall, Modified MK, PW-MK, or Sen's slope tests on the projected future time series (2021–2050, 2071–2100). The only trend quantification provided is the percentage change in the period mean:
```
change% = 100 × (future_mean − baseline_mean) / baseline_mean
```

This is a **static comparison of period means**, not a trend analysis. It answers "does the mean change between periods?" but not "is there a monotonic trend within the future period?" For Q1 publication in hydroclimatology, the lack of projected trend analysis is a significant gap.

**Validity of MK on bias-corrected GCM output:**  
Applying MK to 30-year future windows (2021–2050) is methodologically sound provided the bias-corrected series preserves temporal variability. QDM and BCSD both preserve temporal sequencing, so MK applied to the annual time series within each future window would be valid. The minimum sample size constraint (MIN_N = 10) is easily met by 30-year windows.

**Recommendation:** Add `run_all()` (or equivalent MK test loop) applied to each model's annual/wet/dry projected time series. Report Sen's slope (mm/yr/decade) within 2021–2050 and 2071–2100 windows alongside the period-mean change%.

---

### Area 10 — Reproducibility

**Verdict: Acceptable for deterministic methods; one concern**

**Deterministic methods — No seeds required:**
- IDW interpolation: fully deterministic given fixed station coordinates and power parameter ✓
- Ordinary Kriging: deterministic given fixed variogram parameters (`sill`, `range`, `nugget` from config) ✓  
- Ensemble statistics (mean, median, percentiles): deterministic ✓
- All MK/MMK tests: deterministic ✓

**MAJOR-06 — No archived bias-corrected input files:**  
As noted in Area 6, the bias-corrected CSV files are the primary input to both packages. These are not archived in the repository (correctly excluded from git given file size). However, without a DOI-linked data archive or a fully deterministic processing script that generates them from raw CMIP6 NetCDFs, the analysis is not independently reproducible. This is a Q1 journal standard requirement.

**MINOR-05 — `config.yaml` version tag absent:**  
Neither `config/config.yaml` has a `version` field. If the configuration is changed between runs, there is no way to determine which configuration produced a given set of outputs. A `run_version` or `config_hash` field should be logged to output files.

**Positive:** Both packages log the config snapshot at the start of each run via `config_to_dict()`, which is saved to the Excel output. This is good practice. ✓

---

### Area 11 — Q1/Q2 Publication Readiness

**Verdict: Partially ready; four items require remediation**

#### Figures

| Aspect | v2 Status |
|--------|-----------|
| Resolution | 600 DPI ✓ |
| Format | PNG + PDF (when `SAVE_PDF=True`) ✓ |
| Font | DejaVu Serif (serif) ✓ |
| Colorblind-safe palette | Wong (2011) for scenarios; RdBu diverging; YlGnBu sequential ✓ |
| Panel labels | `(a)`, `(b)`, … ✓ |
| Single-column width | ~88 mm (configurable) — not checked |
| Taylor diagram | Implemented in v2 using Taylor (2001) construction ✓ |
| Spatial maps | Station-based bubble maps with IDW/OK interpolated surfaces ✓ |

**MAJOR-07 — Figure 3 anomaly baseline:**  
`CMIP6_MME_v2/src/figures/make.py::fig3_anomaly_ts()` computes anomalies relative to the grand mean of the entire time series (historical + future concatenated), rather than relative to the baseline period mean (`1981–2014`). This produces systematically different anomaly magnitudes depending on the length and composition of the future period included, making the figure non-reproducible if the scenario time window changes.

**Correct approach:** Compute the baseline climatology exclusively over `periods.baseline` years, then subtract this from all periods (historical and future alike). This is the IPCC standard for anomaly figures.

#### Tables

| Aspect | Status |
|--------|--------|
| 3-level column headers (Station / Season / Metric) | v2 ✓ |
| Publication table with bold/italic | v2 ✓ |
| KGE / NSE / PBIAS validation | Both ✓ |
| Ensemble spread (P25–P75) in tables | v2 ✓ |
| MK trend analysis of future series | **Absent — MAJOR-05** |

#### Methods Traceability

| Requirement | Status |
|-------------|--------|
| Calendar harmonisation documented | **Missing — CC-01** |
| Bias correction method cited | **Missing — CC-02** |
| Model list with versions/runs documented | Not confirmed in code |
| Spatial extraction method stated | **Missing** |
| Equal model weighting justified | **Missing — MAJOR-03** |

---

## Defect Summary

### CRITICAL

| ID | Location | Description |
|----|----------|-------------|
| CC-01 | Both packages | No CMIP6 calendar handling code (noleap/360_day/proleptic_gregorian). Entire analysis is non-reproducible without external calendar harmonisation documented in the methods. |
| CC-02 | Both packages | No bias correction implementation (QDM/QM/Delta Change). If BC was applied externally, this must be fully documented with method, software, reference period, and archived outputs. |
| CC-03 | `CMIP6_package/src/ensemble/mme.py` | `np.percentile` used without NaN guard; will produce incorrect P25/P75 values when any models have missing years in the aggregation window. Fixed in v2 but unfixed in v1. |

### MAJOR

| ID | Location | Description |
|----|----------|-------------|
| CM-01 | `CMIP6_package/src/figures/make.py` | Hardcoded `SCEN = ["ssp245", "ssp585"]` throughout figures module; ignores `cfg["scenarios"]`. Breaks for any other scenario configuration. |
| CM-02 | Both packages | No model independence or performance weighting. Equal-weight MME overrepresents model families with multiple variants. Must be acknowledged or corrected. |
| CM-03 | Both packages `compute_change_pct()` | Change% computed on MME statistics rather than per-model change% aggregated to MME. Produces biased results when inter-model spread is asymmetric. |
| CM-04 | Both packages | No MK/MMK/Sen's slope trend analysis on projected future time series. Period-mean change% is reported instead. Inadequate for Q1 hydroclimatology. |
| CM-05 | `CMIP6_MME_v2/src/figures/make.py::fig3_anomaly_ts()` | Anomaly baseline uses grand mean of entire concatenated series instead of baseline period mean. Non-reproducible across different future windows. |
| CM-06 | Both packages | No archived or reproducible pipeline to generate bias-corrected CSV inputs from raw CMIP6 NetCDFs. Analysis is not independently reproducible. |
| CM-07 | `CMIP6_MME_v2/src/validation/metrics.py` | KGE uses population standard deviation (`ddof=0`) undocumented. Standard KGE formulation (Gupta et al. 2009) uses sample std (`ddof=1`). Must be stated or corrected. |

### MINOR

| ID | Location | Description |
|----|----------|-------------|
| Cm-01 | `CMIP6_package/src/utils/io.py::load_metadata()` | Only accepts `.xlsx` input; v2 version accepts both `.xlsx` and `.csv`. Should be updated for consistency. |
| Cm-02 | Both packages `descriptive_stats()` | Standard deviation reported as `0.0` for stations with only one valid year (n=1), instead of `NaN`. Misleading in publication tables. Fix: `std = np.nan if n <= 1 else np.std(vals, ddof=1)`. |
| Cm-03 | Both packages `config/config.yaml` | No `version` or `run_id` field in configuration. Outputs cannot be traced back to the configuration that produced them. |
| Cm-04 | Both packages | No monthly aggregation of projected series. Prevents direct comparison of observed vs projected monthly climatology (Fig 7 equivalent). |
| Cm-05 | Both packages | Future period validation absent: no check that loaded model series actually spans the full configured window. Partial coverage is silently accepted. |

---

## Priority Remediation Sequence

For Q1 submission, the following sequence is recommended:

1. **CC-01 (Calendar)** — Document calendar harmonisation method in full. If handled externally, add a dedicated "Data Pre-Processing" section to the manuscript and archive the extraction script.

2. **CC-02 (Bias correction)** — Document bias correction method, reference period, and software. Archive bias-corrected input CSVs with a data DOI or provide a fully deterministic generation script.

3. **CC-03 (v1 NaN percentile)** — Copy the NaN-safe lambda functions from v2 `mme.py` to v1 `mme.py`.

4. **CM-05 (Anomaly baseline)** — Fix `fig3_anomaly_ts()` to use the configured `baseline` period for anomaly computation.

5. **CM-03 (Change%)** — Refactor `compute_change_pct()` to compute per-model change%, then aggregate.

6. **CM-04 (No trend on projections)** — Add MK/Sen's slope tests within each future window and report in the results.

7. **CM-07 (KGE ddof)** — Confirm or correct the standard deviation convention in KGE; document explicitly.

8. **CM-01 (Hardcoded scenarios in v1)** — Replace with dynamic config reads (pattern already exists in v2).

9. **CM-02 (Model weighting)** — Add acknowledgement of equal weighting or implement performance-based weighting.

---

## Scientific References

| Topic | Reference |
|-------|-----------|
| CMIP6 overview | Eyring et al. (2016) *Geosci. Model Dev.* 9:1937–1958 |
| Calendar harmonisation | CF Conventions v1.10, §4.4; Juckes et al. (2020) |
| Quantile Delta Mapping | Cannon et al. (2015) *J. Climate* 28:6938–6959 |
| KGE formulation | Gupta et al. (2009) *J. Hydrol.* 377:80–91 |
| Model independence weighting | Knutti et al. (2017) *Earth's Future* 5:1292–1295 |
| Multi-model mean vs. median | Tebaldi & Knutti (2007) *Phil. Trans. R. Soc. A* 365:2053–2075 |
| Anomaly computation | IPCC AR6 WGI Technical Summary (2021), Box TS.2 |
| Field significance | Livezey & Chen (1983) *Mon. Wea. Rev.* 111:46–59 |
| Sen's slope | Sen (1968) *JASA* 63:1379–1389; Gilbert (1987) |
