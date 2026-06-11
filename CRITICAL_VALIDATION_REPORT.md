# CRITICAL FINDING VALIDATION REPORT

**Date:** 2026-06-11  
**Scope:** All 8 CRITICAL defects — rainfall pipeline (C-01 to C-05) and CMIP6 sub-projects (CC-01 to CC-03)  
**Basis:** Static code analysis; all assessments are grounded in direct code evidence

---

## How to Read This Report

Each finding is assessed across five dimensions:

| Dimension | Description |
|-----------|-------------|
| Scientific validity | Is the finding technically correct? Is the code actually wrong? |
| Impact on results | What numerical values are wrong, and by how much? |
| Impact on conclusions | Can the paper's claims survive this defect? |
| Risk if left unfixed | What happens at review / post-publication? |
| Scope | Which outputs (calculations / figures / tables / interpretation) are affected? |

---

## Rainfall Pipeline Critical Defects

---

### C-01 — PW-MK Sen's Slope Computed on Prewhitened Series

**File:** `rta/pw.py:82`, `rta/trend_tests.py:265`  
**Function:** `pw_mk()`

---

#### 1. Scientific Validity

**Confirmed. The finding is correct.**

The prewhitening operation `y[t] = x[t+1] − ρ₁·x[t]` produces a first-difference-like residual
series. For a series with true slope β (mm/yr) and lag-1 autocorrelation ρ₁, the expected
slope of the prewhitened residuals is approximately:

```
E[slope(y)] ≈ β·(1 − ρ₁)
```

This follows because the linear trend contributes `β·(1 − ρ₁)` to the prewhitened series,
not `β`. The prewhitened series is not rainfall; it is an autocorrelation-corrected residual
whose magnitudes have no direct physical interpretation as mm/yr.

Yue & Wang (2004) state explicitly (§2): "the Sen's slope is estimated from the original
series." The Z statistic is the only quantity that should be derived from the prewhitened
series.

The code calls `standard_mk(y)` (where `y` is the prewhitened series), and `standard_mk`
calls `sens_slope(x)` on whatever was passed to it — which in this call is `y`, not the
original `x`.

---

#### 2. Impact on Results

**Quantitative bias (systematic, direction-dependent):**

| ρ₁ value | Reported PW slope / True slope | Direction of error |
|----------|-------------------------------|-------------------|
| +0.1 | ≈ 0.90 × β | Underestimates magnitude |
| +0.2 | ≈ 0.80 × β | Underestimates magnitude |
| +0.3 | ≈ 0.70 × β | Underestimates magnitude |
| +0.4 | ≈ 0.60 × β | Underestimates magnitude |
| −0.1 | ≈ 1.10 × β | Overestimates magnitude |

For stations with significant positive autocorrelation (the case that triggers prewhitening),
ρ₁ ≈ 0.2–0.4 is typical for rainfall annual series. The reported PW-MK slope would be
20–40% smaller than the true rainfall trend.

The 95% CI bounds (`slope_lo`, `slope_hi`) are also wrong — they are CIs of the prewhitened
residual slopes, not CIs of the rainfall trend.

**Scope:** The error applies only to stations/scales where `pw_applied = True` (significant
lag-1 autocorrelation detected). For stations with no significant autocorrelation, `pw_mk`
returns `standard_mk(x)` — the original series — and the slope is correct.

The `rta/batch.py:12` imports `pw_mk` from `rta.trend_tests` (the version without the
MIN_N post-PW check). The `PW_slope` and `dSlope_PW` columns in the 4-method comparison
table are derived from this wrong value.

---

#### 3. Impact on Publication Conclusions

**High.** Three specific harms:

1. **Method comparison is falsified.** The paper will show PW-MK slopes systematically lower
   than Standard MK slopes for autocorrelated stations. The 4-method comparison table will
   show artificial discrepancies (`dSlope_PW` non-zero) that will be mis-attributed to a
   methodological difference when they reflect a coding error.

2. **Quantitative conclusions may reverse for borderline stations.** If a station has a true
   trend of 1.0 mm/yr but ρ₁ = 0.4, the reported PW slope is 0.6 mm/yr. If the paper
   describes trends by magnitude category (e.g., "five stations show trends > 0.8 mm/yr"),
   the categorisation may be wrong.

3. **The paper presents PW-MK as a robustness check against autocorrelation.** If the slopes
   disagree with MMK/Standard MK (which they will, due to this bug), a reader may incorrectly
   conclude that the choice of prewhitening method changes the trend estimate — when it should
   not.

---

#### 4. Risk if Left Unfixed

**Very high.** The Yue & Wang (2004) reference is cited in the manuscript. Any reviewer
familiar with that paper will check that Sen's slope is computed on the original series. This
is also checkable numerically: the PW-MK slope should be close to the Standard MK slope
for the same station. If reported values diverge by 20–40%, a reviewer will query it.

**Post-publication risk:** If discovered after acceptance, all tables and figures containing
PW-MK slope values require correction. Correction notices for computational errors in
published hydrology papers are common and reputationally costly.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Yes** | `slope_Q`, `slope_lo`, `slope_hi` wrong for all `pw_applied=True` rows |
| Figures | **Yes** | Any figure displaying PW-MK slopes (Fig 3, Fig 10 / Fig 11 in v4, spatial maps if slope-coloured) |
| Tables | **Yes** | Excel sheets containing PW-MK slope columns; 4-method comparison `PW_slope`, `dSlope_PW` |
| Interpretation | **Yes** | Method comparison conclusions; magnitude-based trend categorisation |
| Z statistic / p-value / sig flags | **No** | These are correctly derived from prewhitened series |

---

---

### C-02 — Duplicate Module Implementations with Divergent Behaviour

**Files:** `rta/pw.py`, `rta/trend_tests.py`, `rta/field_sig.py`, `rta/field_significance.py`, `rta/io.py`, `rta/checkpoint.py`  
**Functions:** `pw_mk`, `livezey_chen_mc`, `field_sig_summary`, checkpoint I/O

---

#### 1. Scientific Validity

**Confirmed. The finding is correct and the divergences are real.**

Three scientifically material divergences exist between paired implementations:

**Divergence A — Post-prewhitening MIN_N:**  
`rta/pw.py:79` checks `len(y) < MIN_N` after constructing the prewhitened series.  
`rta/trend_tests.py:263–265` constructs `y` and immediately calls `standard_mk(y)` with
no such check. The v4 pipeline uses `rta.trend_tests.pw_mk` (via `rta/batch.py:12`).

**Divergence B — Field significance MMK coverage:**  
`rta/field_sig.py::field_sig_summary()` returns Walker/LC results only for Standard MK.  
`rta/field_significance.py::field_sig_summary()` returns Walker/LC results for both MK
and MMK. The v4 pipeline uses `rta.field_sig`.

**Divergence C — Station eligibility threshold:**  
`rta/field_sig.py:131` uses `len(a) >= 4`.  
`rta/field_significance.py:131` uses `len(v) >= MIN_N`.

The non-scientific divergence (checkpoint API names) does not affect results.

---

#### 2. Impact on Results

**Divergence A** affects only stations with exactly `MIN_N = 10` valid years and significant
autocorrelation. In this dataset (1981–2014, 34 years), very few if any stations fall in
this range for annual/wet/dry scales. Practical impact on this dataset is likely zero, but
the inconsistency is a structural defect.

**Divergence B** is the proximate cause of C-03 (MMK field significance gap). The impact
is documented under C-03.

**Divergence C** is addressed under C-05.

The primary risk from C-02 is **propagation of fixes**: if C-01 is fixed in `rta/pw.py`
but not in `rta/trend_tests.py`, or vice versa, the two pipelines diverge further. The
CHANGELOG claims v3 and v4 are numerically identical (144/144 results match). After fixing
C-01 in one module only, this claim becomes false.

---

#### 3. Impact on Publication Conclusions

**Moderate.** If the paper is produced by a single pipeline (v4), Divergence A has no
current impact. Divergence B produces the C-03 gap. The main risk is during revision or
re-analysis: a future fix applied to only one duplicate silently breaks parity.

---

#### 4. Risk if Left Unfixed

**Medium for current submission; High for long-term maintenance.** Any bug fix or
methodological refinement must be applied twice. With two implementations drifting, the
"v3/v4 parity" claim in the CHANGELOG becomes an unverifiable assertion rather than a
testable property.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Yes** | v3 and v4 field significance outputs diverge for MMK; PW-MK n=10 edge case |
| Figures | **Indirect** | Via C-03 and C-05 |
| Tables | **Yes** | Excel Sheet S8 differs between v3 and v4 runs |
| Interpretation | **Yes** | "Results are identical between v3 and v4" claim becomes false after any single-module fix |

---

---

### C-03 — MMK Field Significance Absent from v4 `field_sig_summary()`

**File:** `rta/field_sig.py:258–282`  
**Function:** `field_sig_summary()`

---

#### 1. Scientific Validity

**Confirmed. The finding is correct.**

`field_sig_summary()` in `rta/field_sig.py` counts `n_sig_mmk` (lines 258–260) but never
passes that count to `walker_test()` or `livezey_chen_mc()`. The Walker and LC tests are
run only for Standard MK (lines 263–267). No Walker or LC results for Modified MK exist
anywhere in the returned DataFrame.

The function docstring (lines 207–212) lists the returned columns explicitly and confirms:
no `Walker_p_MMK`, `Walker_sig_MMK`, `LC_p_MMK`, or `LC_sig_MMK` columns are produced.

This contrasts with `rta/field_significance.py::field_sig_summary()`, which correctly runs
Walker and LC for both MK and MMK.

---

#### 2. Impact on Results

**Complete output gap, not a numerical error.** The Walker p-value and LC p-value for MMK
are not computed at all. The output DataFrame has `N_sig_MMK` and `Frac_sig_MMK` (counts)
but no test statistics.

This means Excel Sheet S8 (Field Significance) from the v4 pipeline contains:
- `Walker_p_MK` — present
- `Walker_sig_MK` — present
- `LC_p_MK` — present
- `LC_sig_MK` — present
- `Walker_p_MMK` — **absent**
- `Walker_sig_MMK` — **absent**
- `LC_p_MMK` — **absent**
- `LC_sig_MMK` — **absent**

---

#### 3. Impact on Publication Conclusions

**High.** The Modified MK test is recommended specifically for time series with serial
autocorrelation. Field significance under MMK (i.e., whether the pattern of locally
significant trends across the station network is itself significant) is therefore the most
relevant field significance result for this study. Without it, the paper can only state
field significance under the Standard MK test, which does not account for autocorrelation.

A reviewer will ask: "Are the MMK trends field-significant?" The paper cannot answer this
question from the v4 output.

---

#### 4. Risk if Left Unfixed

**High.** Field significance is a standard reporting requirement for multi-station trend
studies (Walker 1914; Livezey & Chen 1983 are cited in the manuscript). The absence of
the MMK result is immediately apparent in Sheet S8. A reviewer examining the Excel workbook
will see `N_sig_MMK` with a non-zero count but no associated test p-value, and will query
the omission.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Yes** | Walker_p_MMK and LC_p_MMK are never computed |
| Figures | **Yes** | Any figure rendering field significance results will have no MMK bar/panel |
| Tables | **Yes** | Excel Sheet S8 is missing four columns for the primary test method |
| Interpretation | **Yes** | Cannot make field-significance conclusions under the autocorrelation-corrected test |

---

---

### C-04 — No Post-Prewhitening MIN_N Check in `rta/trend_tests.py::pw_mk()`

**File:** `rta/trend_tests.py:263–265`  
**Function:** `pw_mk()`

---

#### 1. Scientific Validity

**Confirmed as a structural defect; practical impact is dataset-specific.**

After prewhitening, `y = x[1:] − ρ₁·x[:-1]` has length `n−1`. For a series of exactly
`n = MIN_N = 10` observations, `y` has 9 observations. Calling `standard_mk(y)` with
n=9 triggers the internal null return: `if n < MIN_N: return null`. The null dict is
returned with all-NaN statistics. `pw_mk` then writes `pw_applied=True`, `rho_1_used=ρ₁`,
and `method="PW-MK"` onto the null dict and returns it.

The returned result is numerically equivalent to a null result — all statistics are NaN,
slope fields are NaN, and no trend conclusion is drawn. However, the dict does carry
`pw_applied=True` and `rho_1_used` populated, which may give a false impression that
prewhitening was applied and a test was run when it was not.

`rta/pw.py:79` handles this cleanly by checking `len(y) < MIN_N` before calling
`standard_mk`, returning `_null` immediately with `pw_applied=False`.

**Practical impact for this dataset:** For 1981–2014 (34 years), stations would need to
lose ≥25 years to the 80% completeness gate before hitting n=10. This is unlikely for
annual totals with complete station records. For wet/dry seasons the gate is stricter, but
even so, reaching n=10 with significant autocorrelation simultaneously is a rare edge case
in this specific dataset.

---

#### 2. Impact on Results

**Edge-case numerical impact, not universal.** Only affects stations/scales where:
- The annual (or seasonal) series has exactly 10 complete years, AND
- The lag-1 autocorrelation is statistically significant.

For such stations, `rta/trend_tests.py::pw_mk()` returns a dict with NaN statistics but
`pw_applied=True`. `rta/pw.py::pw_mk()` returns the null base dict with `pw_applied=False`.
The two pipelines produce different `pw_applied` values for the same station, potentially
causing discrepancies in the Excel output column "pw_applied" and in the 4-method
comparison table.

---

#### 3. Impact on Publication Conclusions

**Low for this specific dataset.** No station in this study is likely to have exactly 10
valid annual or seasonal years. The defect is a maintenance and cross-implementation
consistency issue rather than an active error in the publication.

---

#### 4. Risk if Left Unfixed

**Low for this submission.** The structural risk is that future use of the pipeline on
shorter records (e.g., 12-year regional studies) would silently produce misleading output.
As a maintenance defect, it should be fixed before the code is released as a general tool.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Edge case** | Only stations with n=10 and significant autocorrelation |
| Figures | **Unlikely** | No figure likely shows affected stations for this dataset |
| Tables | **Edge case** | `pw_applied` column inconsistency between v3 and v4 for edge-case stations |
| Interpretation | **No** | No station in this study is expected to trigger the edge case |

---

---

### C-05 — `rta/field_sig.py` Uses `len >= 4` Instead of `MIN_N`

**File:** `rta/field_sig.py:131`, `rta/field_sig.py:228`  
**Functions:** `livezey_chen_mc()`, `field_sig_summary()`

---

#### 1. Scientific Validity

**Confirmed as a defect; quantitative impact depends on the dataset.**

Two locations use `>= 4` as the station eligibility threshold:

1. `livezey_chen_mc():131` — stations with ≥4 valid years enter the LC null distribution.
2. `field_sig_summary():228` — stations with ≥4 valid years enter both `mk_series` and
   `n_stn` (used as the Walker test denominator).

For any station in `station_arrays` with 4–9 valid years:
- `standard_mk(a)` is called on it, returning a null dict with `p_value = NaN`
- `NaN < alpha` evaluates to `False` in Python
- The station is counted in `n_stations` (denominator) but NOT in `n_sig_obs` (numerator)
- In every MC iteration, the same station always contributes 0 to the significant count

**Walker test bias:** `walker_test(n_stn, n_sig_mk)` receives an inflated `n_stn` (includes
4–9 year stations) and an accurate `n_sig_mk` (short stations never pass). The expected
count under H₀ is `n_stn × α`, which is inflated. Walker's p-value is based on
`P(X ≥ n_sig_mk | Binomial(n_stn, α))`. An inflated `n_stn` makes it harder to achieve
significance (larger denominator, same numerator), biasing toward non-significance.

**LC test bias:** Both `S_obs` and `null_fracs` are divided by the same inflated
`n_stations`. The fraction observed and the null distribution fractions are both deflated
by the same factor. The p-value `P(null_fracs ≥ S_obs)` is approximately unbiased in
relative terms, but `S_obs` is mis-reported (too low), and the `n_stations` count in the
output is misleading.

**Practical impact for this dataset:** The 1981–2014 record spans 34 calendar years. For
annual totals, a station would need to fail the 80% completeness gate in ≥25 of 34 years
to fall below MIN_N=10. This is implausible. For wet/dry seasons the same logic applies.
Unless stations have very poor records, no station in this specific study has 4–9 valid
years and the `>= 4` threshold does not trigger.

---

#### 2. Impact on Results

**Latent; likely zero impact on this specific dataset.** If confirmed that all stations
have ≥10 valid annual, wet, and dry years, the two thresholds select identical station sets
and produce identical results. The defect becomes material only if stations with 4–9 valid
years exist in the analysed scales.

---

#### 3. Impact on Publication Conclusions

**Low for this dataset.** If no station has 4–9 valid years on any scale, field significance
results are unaffected. The defect's publication risk is that it cannot be confirmed as
harmless without explicitly checking the minimum valid-year count per station per scale —
which the paper's methods section should report regardless.

---

#### 4. Risk if Left Unfixed

**Medium as a code quality issue.** The discrepancy with `rta/field_significance.py` (which
correctly uses `MIN_N`) means the v4 pipeline uses a less conservative station eligibility
filter than the v3 pipeline. Any dataset with short-record stations would produce different
field significance outputs from v3 and v4 without explanation. For this study specifically
the risk is low.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Conditionally** | If any station has 4–9 valid years: Walker p-value biased upward; LC n_stations inflated |
| Figures | **Conditionally** | Field significance figure affected if Walker/LC values are wrong |
| Tables | **Conditionally** | Excel Sheet S8 n_stations count wrong if short-record stations exist |
| Interpretation | **Conditionally** | Field significance conclusion may be under-powered if short stations inflate denominator |

---

---

## CMIP6 Sub-Project Critical Defects

---

### CC-01 — No CMIP6 Calendar Harmonisation Code

**Files:** All Python source in `CMIP6_package/` and `CMIP6_MME_v2/`  
**Function:** N/A (codebase-wide absence)

---

#### 1. Scientific Validity

**Confirmed as a documentation gap; confirmed as a potential correctness defect depending
on which models were used.**

CMIP6 models use at least four calendar systems. The two practically relevant ones for
annual and seasonal rainfall totals are:

| Calendar | Days/year | Feb 29 | Impact if ingested as Gregorian |
|----------|-----------|--------|---------------------------------|
| `standard` | 365.25 avg | Yes | None — identical to Gregorian |
| `noleap` (365_day) | 365 fixed | No | Missing ~8.5 days over 34 years; annual totals essentially identical but seasonal boundaries drift by ≤1 day |
| `360_day` | 360 fixed | N/A | Months have 30 days each. Day 31 doesn't exist; `pd.to_datetime()` will fail or produce NaT for day 31 of any month with 31 days |

For `360_day` models: if stored as CSV with `[YEAR, MONTH, DAY]` columns using the model's
internal calendar, months 1, 3, 5, 7, 8, 10, 12 have only 30 days in the model but 31
in Gregorian. `pd.to_datetime()` will either raise or produce NaT values for days 31 of
those months. The resulting daily series would have gaps that propagate through annual and
seasonal aggregation.

For `noleap` models: the difference is only the absence of February 29. Over 34 years
(1981–2014), there are 8–9 leap years, meaning 8–9 days missing from `noleap` model data.
Annual totals are negligibly affected; seasonal boundaries unchanged.

**Key unknown:** Whether any `360_day` models are included. If all models use `standard` or
`noleap` calendars, the quantitative impact is small. If any `360_day` models are included
without correction, annual and seasonal totals are systematically biased.

---

#### 2. Impact on Results

**Indeterminate without knowing the model list.** For `noleap` models: negligible impact on
annual totals (~0.025% error per year from 1 missing day). For `360_day` models: potentially
large systematic gaps in daily data, corrupting seasonal totals by up to 100% of the 1
missing day per month.

---

#### 3. Impact on Publication Conclusions

**High for reproducibility regardless of actual impact on numbers.** A Q1 reviewer will
ask: "Which calendar convention was used for each model, and how were calendar differences
handled?" Without an answer in the methods section, the analysis cannot be independently
reproduced, which is a standard rejection criterion in climate science journals.

---

#### 4. Risk if Left Unfixed

**High.** Climate journals routinely reject or require major revision for papers that do
not document calendar handling. The CMIP6 protocol (Eyring et al. 2016) requires that
calendar metadata be recorded. The methods section must state which calendars were
encountered and how they were handled.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Potentially** | Seasonal totals wrong for `360_day` models without correction |
| Figures | **Potentially** | Temporal anomaly figures (Fig 3) wrong for affected models |
| Tables | **Potentially** | All MME statistics wrong if `360_day` model data has NaT gaps |
| Interpretation | **Yes** | Reproducibility: independent replication is impossible without documented calendar handling |

---

---

### CC-02 — No Bias Correction Implementation

**Files:** All Python source in `CMIP6_package/` and `CMIP6_MME_v2/`  
**Function:** N/A (codebase-wide absence)

---

#### 1. Scientific Validity

**Confirmed as a documentation gap; potentially a correctness issue depending on what
inputs are actually used.**

No bias correction code exists in either package. Both packages accept pre-processed CSVs
as their primary input. If those CSVs contain bias-corrected values, the pipeline is
computationally correct but undocumented. If those CSVs contain raw CMIP6 model output,
the pipeline is both undocumented and scientifically invalid for impact assessment.

Raw CMIP6 model output at the station scale typically has systematic biases in:
- Mean annual rainfall (often 50–200% of observed, depending on model)
- Seasonal distribution (monsoon onset/withdrawal timing)
- Wet-day frequency and intensity distribution

Without bias correction, the change% values (e.g., "SSP5-8.5 projects a 15% increase in
annual rainfall") are computed relative to a model-simulated baseline that does not match
the observed baseline. The change signal mixes model bias with genuine climate change signal.

---

#### 2. Impact on Results

**If BC was applied externally:** Computationally, there is no impact on the numbers — the
pipeline operates correctly on whatever CSVs are provided. The impact is entirely on
reproducibility and methods transparency.

**If BC was NOT applied:** All absolute projected values and change% statistics are biased
by the systematic difference between raw model climatology and observed climatology.
KGE/NSE/PBIAS validation metrics lose their interpretation as bias-correction skill scores
and instead measure raw model performance — a different and less policy-relevant quantity.

---

#### 3. Impact on Publication Conclusions

**High in both scenarios.** If BC was applied: the methods section is incomplete and peer
review will require it to be filled before acceptance. If BC was not applied: all
quantitative projections in the results section are methodologically indefensible for a
hydrological impact assessment. Q1 hydroclimatology journals require BC to be documented
and justified.

---

#### 4. Risk if Left Unfixed

**Very high.** Absence of bias correction documentation is a standard major-revision or
rejection criterion for projected rainfall impact studies in Q1 journals (e.g., Journal of
Hydrology, Water Resources Research, Climatic Change, Journal of Climate). The methods
section must name the BC method, cite the implementation, state the reference period, and
either archive the corrected data or provide a reproducible script.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Potentially** | If raw CMIP6 used: all projected means, change%, KGE/NSE/PBIAS are biased |
| Figures | **Potentially** | Fig 3 (anomaly), Fig 4–6 (spatial), Fig 7 (change maps) all depend on BC outputs |
| Tables | **Yes** | Change% table and validation metrics table require documented BC inputs |
| Interpretation | **Yes** | All quantitative projections and "BC improves validation metrics" claims require BC documentation |

---

---

### CC-03 — `CMIP6_package` (v1) MME Percentiles Have No NaN Guard

**File:** `CMIP6_package/src/ensemble/mme.py:10–12`  
**Function:** `build_mme()`

---

#### 1. Scientific Validity

**Confirmed. The finding is correct.**

```python
# CMIP6_package/src/ensemble/mme.py:11
p25=lambda s:np.percentile(s,25),p75=lambda s:np.percentile(s,75),
```

`np.percentile(s, 25)` where `s` is a pandas Series containing NaN values exhibits
NumPy-version-dependent behaviour:
- NumPy < 1.22: silently propagates NaN (percentile of a series with NaN is NaN)
- NumPy ≥ 1.22: raises a `TypeError` because passing a generator/Series to `np.percentile`
  is deprecated and the NaN handling changed

In the groupby-agg context, pandas calls the lambda with each group's `rainfall` Series.
If any model has a missing year within the aggregation window (station-year-season
combination), that year's `rainfall` value is NaN. The percentile call then produces a
NaN result or raises, depending on NumPy version.

The v2 fix in `CMIP6_MME_v2/src/ensemble/mme.py:36–37` is correct:
```python
p25 = lambda s: float(np.percentile(s.dropna(), 25)) if s.notna().any() else np.nan,
```

---

#### 2. Impact on Results

**All P25 and P75 ensemble spread values in v1 outputs are unreliable.** Any station-year
where at least one model has a missing value produces NaN P25/P75 rather than the
correct inter-quartile spread. The ensemble mean and median (which use pandas built-ins)
are unaffected — they handle NaN correctly by default.

The N-models count (`n_models = "count"`) uses pandas `count` which excludes NaN, so
it is also unaffected. Only P25 and P75 are wrong.

**Scope of corruption:** If any CMIP6 model in the ensemble has gaps (e.g., missing years
within the historical or future period), P25/P75 values are NaN for every affected
station-year. In practice, multi-model CMIP6 ensembles commonly have models with
incomplete historical runs (e.g., a model providing only 1985–2014 rather than 1981–2014).
The prevalence of NaN in P25/P75 depends on ensemble completeness.

---

#### 3. Impact on Publication Conclusions

**Moderate if v1 is used for publication; Low if v2 is used.**

If the published figures and tables were generated from `CMIP6_MME_v2` (v2), P25/P75 are
computed correctly and this defect does not affect the publication. If any output was
generated from `CMIP6_package` (v1), all ensemble spread statistics (P25, P75, IQR
shading in Fig 3) may contain NaN values or incorrect values.

The uncertainty envelope shading in the anomaly time-series figure (Fig 3 in the CMIP6
package, using `p25` and `p75` columns) is directly driven by these values. If P25/P75
are NaN, the shading is absent rather than wrong — visually obvious.

---

#### 4. Risk if Left Unfixed

**Medium for v1 outputs; Low for v2 outputs.** If both packages are archived in the
repository and a reviewer runs v1, they will encounter either missing uncertainty envelopes
(NaN P25/P75) or a runtime error. This undermines the reproducibility claim. Since v2
fixes the issue, the fix is to ensure only v2 is used for final outputs and v1 is either
removed or corrected.

---

#### 5. Scope

| Output | Affected? | Detail |
|--------|-----------|--------|
| Calculations | **Yes (v1 only)** | P25 and P75 in MME output are NaN wherever any model has a missing year |
| Figures | **Yes (v1 only)** | Ensemble spread shading in Fig 3 (anomaly time series) absent or wrong |
| Tables | **Yes (v1 only)** | P25/P75 columns in all results tables wrong for incomplete-ensemble stations |
| Interpretation | **Yes (v1 only)** | Inter-model uncertainty envelope cannot be reported if P25/P75 are NaN |
| v2 outputs | **No** | The NaN-safe lambda in CMIP6_MME_v2 correctly handles missing models |

---

---

## Cross-Defect Risk Summary

| ID | Finding | Validity | Result impact | Conclusion impact | Risk unfixed |
|----|---------|----------|--------------|-------------------|-------------|
| C-01 | PW slope on prewhitened series | Confirmed | 20–40% slope underestimate for autocorrelated stations | High — method comparison falsified | Very high |
| C-02 | Duplicate implementations | Confirmed | Edge-case divergence; future fix propagation risk | Moderate | Medium |
| C-03 | MMK field significance absent | Confirmed | MMK Walker/LC results do not exist | High — primary test method has no field sig | High |
| C-04 | Missing post-PW MIN_N check | Confirmed | Edge case: n=10 stations with significant AC | Low for this dataset | Low |
| C-05 | `len >= 4` vs MIN_N threshold | Confirmed | Walker p-value biased upward if short-record stations exist | Low for this dataset | Low–Medium |
| CC-01 | No calendar harmonisation code | Confirmed as absence | Indeterminate: zero for `noleap`; potentially large for `360_day` | High for reproducibility | High |
| CC-02 | No bias correction code | Confirmed as absence | Indeterminate: depends on whether BC was applied upstream | Very high — standard Q1 requirement | Very high |
| CC-03 | v1 MME NaN percentile | Confirmed | P25/P75 wrong or NaN in v1 outputs | Moderate if v1 used; none if v2 used | Medium |

### Minimum Pre-Submission Remediation

**Must fix before submission:**
- **C-01** — Wrong PW-MK slopes in all tables and figures containing PW-MK results
- **C-03** — MMK field significance entirely absent from primary pipeline output
- **CC-01** — Calendar handling must be documented regardless of numerical impact
- **CC-02** — Bias correction method must be documented regardless of whether code exists

**Should fix before submission:**
- **C-02** — Consolidate to prevent divergence post-fix
- **CC-03** — Fix v1 or exclude it from archived outputs

**Can defer to revision with justification:**
- **C-04** — No station in this study expected to be affected
- **C-05** — No station in this study expected to have 4–9 valid years per scale
