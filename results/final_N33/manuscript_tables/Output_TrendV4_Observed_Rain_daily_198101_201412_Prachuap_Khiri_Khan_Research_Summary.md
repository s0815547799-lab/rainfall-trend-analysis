# Rainfall Trend Analysis — Research Summary

> **Generated**: 2026-05-27  |  **Study Period**: 1981–2014  |  **Script**: Rainfall Trend Analysis v4.0

---

## 1. Study Area and Data

- **Study area**: Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand
- **Data**: Daily observed rainfall from 12 meteorological stations
- **Period**: 1981–2014
- **Stations**: S1 (500001), S2 (500002), S3 (500003), S4 (500004), S5 (500005), S6 (500006), S7 (500007), S8 (500008), S9 (500009), S10 (500201), S11 (500202), S12 (500301)
- **Wet-day threshold**: ≥1.0 mm day⁻¹ (WMO standard)

## 2. Methods

### 2.1 Temporal Scales (Hydrological Year)

| Scale | Period | Description |
|-------|--------|-------------|
| Annual | Jan–Dec | Calendar year total |
| Wet Season | May–Oct | Monsoon / wet season (6 months) |
| Dry Season | Nov–Apr | Dry season — hydrological year approach (6 months) |

### 2.2 Statistical Methods

**Standard Mann–Kendall Test** (Mann 1945; Kendall 1975):
- Non-parametric trend test for monotonic trends in time series.
- S statistic with tie correction; Z-statistic from standard normal.
- *Limitation*: Does not account for serial autocorrelation.

**Modified Mann–Kendall Test** (Hamed & Rao 1998):
- Corrects Var(S) using autocorrelation of the ranked series.
- Effective sample size: $n^* = n / [1 + (2/n) \sum_{k=1}^{n-1}(n-k)\rho_k]$
- Adjusted variance: $\text{Var}^*(S) = \text{Var}(S) \times (n/n^*)$
- **Autocorrelation detected**: Yes → Modified MK essential

**Pre-Whitening Mann–Kendall Test** (Yue & Wang 2004):
- Removes lag-1 autocorrelation by pre-whitening the series before applying the MK test.
- $x'_t = x_t - \hat{\rho}_1 x_{t-1}$ (AR(1) pre-whitening).
- Can underestimate trends when trend and autocorrelation coexist.

**Trend-Free Pre-Whitening Mann–Kendall Test** (TFPW-MK; Yue et al. 2002):
- Removes the Sen's slope trend component before pre-whitening, then restores it.
- Reduces bias of the PW-MK method when trends are present.

**Sen's Slope Estimator** (Sen 1968):
- $Q = \text{median}\left[\frac{x_j - x_i}{j - i}\right]$ for all $j > i$
- 95% CI: rank-based method (Gilbert 1987)
- Interpretation: magnitude of change in mm per year

**Significance levels**: α = 0.05 (|Z| > 1.96) and α = 0.01 (|Z| > 2.58)

## 3. Results

### 3.1 Descriptive Statistics

| Station | Code | Mean (mm) | Std (mm) | CV (%) | Wet-days/yr |
|---------|------|-----------|----------|--------|-------------|
| 500001 | S1 | 983.7 | 266.3 | 27.1 | 81.2 |
| 500002 | S2 | 1376.2 | 222.2 | 16.1 | 123.2 |
| 500003 | S3 | 1100.0 | 217.4 | 19.8 | 83.7 |
| 500004 | S4 | 1106.0 | 221.7 | 20.0 | 96.2 |
| 500005 | S5 | 1147.2 | 234.4 | 20.4 | 175.2 |
| 500006 | S6 | 1203.1 | 161.3 | 13.4 | 181.8 |
| 500007 | S7 | 1133.6 | 180.7 | 15.9 | 177.7 |
| 500008 | S8 | 1206.3 | 115.9 | 9.6 | 228.8 |
| 500009 | S9 | 1176.5 | 114.4 | 9.7 | 219.7 |
| 500201 | S10 | 1108.2 | 271.7 | 24.5 | 90.2 |
| 500202 | S11 | 944.1 | 223.4 | 23.7 | 78.6 |
| 500301 | S12 | 1064.8 | 237.6 | 22.3 | 92.5 |

*Regional mean annual rainfall: 1129.1 mm/yr (range: 944.1–1376.2 mm/yr)*

### 3.2 Autocorrelation Results

| Station | Code | r₁ (Annual) | Significant? | → Modified MK? |
|---------|------|-------------|--------------|----------------|
| 500001 | S1 | 0.2599 | No | Optional |
| 500002 | S2 | 0.0259 | No | Optional |
| 500003 | S3 | 0.4739 | Yes *** | Recommended |
| 500004 | S4 | 0.2103 | No | Optional |
| 500005 | S5 | 0.4130 | Yes *** | Recommended |
| 500006 | S6 | 0.1820 | No | Optional |
| 500007 | S7 | 0.1527 | No | Optional |
| 500008 | S8 | 0.0141 | No | Optional |
| 500009 | S9 | 0.1814 | No | Optional |
| 500201 | S10 | 0.0642 | No | Optional |
| 500202 | S11 | -0.3525 | Yes *** | Recommended |
| 500301 | S12 | -0.1062 | No | Optional |

### 3.3 Trend Analysis — Annual Scale

| Station | Code | MK Z | MK p | MMK Z | MMK p | β (mm/yr) | Trend | Sig. |
|---------|------|------|------|-------|-------|-----------|-------|------|
| 500001 | S1 | 1.142 | 0.2536 | 1.142 | 0.2536 | +7.41 | No trend | ns |
| 500002 | S2 | 2.253 | 0.0242 | 2.253 | 0.0242 | +9.18 | Increasing ↑ | * |
| 500003 | S3 | -1.453 | 0.1463 | -1.260 | 0.2075 | -5.93 | No trend | ns |
| 500004 | S4 | 0.534 | 0.5936 | 0.534 | 0.5936 | +2.35 | No trend | ns |
| 500005 | S5 | -0.237 | 0.8125 | -0.237 | 0.8125 | -1.09 | No trend | ns |
| 500006 | S6 | 0.534 | 0.5936 | 0.534 | 0.5936 | +1.35 | No trend | ns |
| 500007 | S7 | -0.830 | 0.4064 | -0.830 | 0.4064 | -2.25 | No trend | ns |
| 500008 | S8 | -0.267 | 0.7896 | -0.267 | 0.7896 | -0.65 | No trend | ns |
| 500009 | S9 | 0.460 | 0.6458 | 0.460 | 0.6458 | +0.58 | No trend | ns |
| 500201 | S10 | 0.623 | 0.5335 | 0.623 | 0.5335 | +3.51 | No trend | ns |
| 500202 | S11 | -1.156 | 0.2476 | -1.156 | 0.2476 | -4.38 | No trend | ns |
| 500301 | S12 | -0.296 | 0.7669 | -0.296 | 0.7669 | -0.62 | No trend | ns |

### 3.4 Trend Analysis — Wet Season (May–Oct)

| Station | Code | MK Z | MMK Z | MMK p | β (mm/yr) | Trend | Sig. |
|---------|------|------|-------|-------|-----------|-------|------|
| 500001 | S1 | 0.504 | 0.504 | 0.6142 | +2.90 | No trend | ns |
| 500002 | S2 | 0.296 | 0.296 | 0.7669 | +0.93 | No trend | ns |
| 500003 | S3 | -1.868 | -1.131 | 0.2578 | -7.77 | No trend | ns |
| 500004 | S4 | -0.919 | -0.919 | 0.3580 | -3.09 | No trend | ns |
| 500005 | S5 | -2.105 | -1.625 | 0.1041 | -6.48 | No trend | ns |
| 500006 | S6 | -2.164 | -1.657 | 0.0976 | -6.54 | No trend | ns |
| 500007 | S7 | -1.631 | -1.631 | 0.1030 | -4.41 | No trend | ns |
| 500008 | S8 | -0.207 | -0.207 | 0.8356 | -0.39 | No trend | ns |
| 500009 | S9 | -0.237 | -0.237 | 0.8125 | -0.54 | No trend | ns |
| 500201 | S10 | 0.889 | 0.889 | 0.3738 | +3.06 | No trend | ns |
| 500202 | S11 | -0.356 | -0.356 | 0.7220 | -1.22 | No trend | ns |
| 500301 | S12 | 0.207 | 0.207 | 0.8356 | +0.73 | No trend | ns |

### 3.5 Trend Analysis — Dry Season (Nov–Apr)

| Station | Code | MK Z | MMK Z | MMK p | β (mm/yr) | Trend | Sig. |
|---------|------|------|-------|-------|-----------|-------|------|
| 500001 | S1 | 1.565 | 1.565 | 0.1176 | +2.34 | No trend | ns |
| 500002 | S2 | 2.773 | 2.773 | 0.0055 | +5.77 | Increasing ↑ | ** |
| 500003 | S3 | 0.232 | 0.232 | 0.8162 | +0.51 | No trend | ns |
| 500004 | S4 | 2.154 | 2.154 | 0.0313 | +5.22 | Increasing ↑ | * |
| 500005 | S5 | 0.883 | 0.883 | 0.3771 | +2.65 | No trend | ns |
| 500006 | S6 | 3.083 | 2.396 | 0.0166 | +6.78 | Increasing ↑ | * |
| 500007 | S7 | 0.945 | 0.945 | 0.3446 | +2.56 | No trend | ns |
| 500008 | S8 | 0.139 | 0.139 | 0.8891 | +0.32 | No trend | ns |
| 500009 | S9 | 0.883 | 0.883 | 0.3771 | +1.52 | No trend | ns |
| 500201 | S10 | 0.418 | 0.418 | 0.6757 | +1.06 | No trend | ns |
| 500202 | S11 | -0.790 | -0.790 | 0.4294 | -1.07 | No trend | ns |
| 500301 | S12 | -0.325 | -0.325 | 0.7449 | -0.61 | No trend | ns |

### 3.6 MK vs Modified MK Comparison

| Metric | Value |
|--------|-------|
| Total comparisons (station × scale) | 36 |
| Agreement (same trend conclusion) | 34 (94.4%) |
| Changed by autocorrelation correction | 2 (5.6%) |
| Stations with significant autocorr. (annual) | 3 / 12 |
| Sig. trends (Standard MK, p<0.05) | 6 / 36 |
| Sig. trends (Modified MK, p<0.05) | 4 / 36 |

### 3.7 Key Findings

- **Annual increasing trend**: S2 show significant increasing trends (mean β = +9.18 mm/yr, p<0.05).
- **Wet season**: No significant trends detected.
- **Dry season**: No significant trends detected.
- **Autocorrelation effect**: Serial autocorrelation was significant in several stations. Modified MK corrects for this bias; 2 trend conclusions changed after applying the correction.

### 3.8 4-Method Comparison

Summary of agreement across all four methods (MK, MMK, PW-MK, TFPW-MK) per temporal scale:

| Scale | N rows | All-agree | Partial | None-agree |
|-------|--------|-----------|---------|------------|
| Annual (Jan–Dec) | 12 | 12 | -11 | 11 |
| Wet Season (May–Oct) | 12 | 12 | -9 | 9 |
| Dry Season (Nov–Apr) | 12 | 12 | -9 | 9 |

**Interpretation**: rows where `all_agree = Yes` indicate robust trend conclusions unaffected by autocorrelation correction method. Disagreement warrants deeper inspection.

### 3.9 Field Significance

Tests whether the number of locally-significant stations exceeds the rate expected by chance alone (Walker 1914; Livezey & Chen 1983):

| Scale | N_stations | N_sig_MK | Frac_sig_MK | Walker_sig | LC_sig |
|-------|------------|----------|-------------|-----------|--------|
| Annual (Jan–Dec) | 12 | 1 | 0.083 | No | No |
| Wet Season (May–Oct) | 12 | 2 | 0.167 | No | No |
| Dry Season (Nov–Apr) | 12 | 3 | 0.250 | Yes* | Yes* |

**Note**: Field significance corrects for the multiplicity of simultaneous hypothesis tests. A result is field-significant when the fraction of locally-significant stations exceeds the 5 % level under the Walker / Livezey–Chen criterion.

## 4. Discussion Points

- The Modified Mann–Kendall test (Hamed & Rao 1998) is the recommended approach when serial autocorrelation is present in hydro-climatic time series data.
- Positive serial autocorrelation inflates the Standard MK Z-statistic, leading to false positive trend detection (Type I error inflation).
- Sen's slope provides a physically meaningful estimate of the rate of change, which is essential for water resource planning.
- Wet/dry season separation is hydrologically important: changes in wet season rainfall affect flood risk, while dry season trends affect irrigation demand and reservoir management.
- The 95% CI of Sen's slope should be reported alongside trend significance to convey the uncertainty in the magnitude of change.

## 5. Suggested Paper Language

### Methods Section (Draft)

Long-term trends in daily, annual, and seasonal rainfall were analysed using the Modified Mann–Kendall (MMK) trend test proposed by Hamed and Rao (1998), which accounts for the effect of positive serial autocorrelation commonly found in hydro-climatic time series. The standard Mann–Kendall test (Mann 1945; Kendall 1975) was also applied for comparison. To further assess the influence of autocorrelation on trend detection, two additional methods were employed: the Pre-Whitening Mann–Kendall test (PW-MK; Yue & Wang 2004) and the Trend-Free Pre-Whitening Mann–Kendall test (TFPW-MK; Yue et al. 2002). The magnitude of detected trends was quantified using the non-parametric Sen's slope estimator (Sen 1968), together with its 95% confidence interval derived from the rank-based method of Gilbert (1987). All analyses were conducted separately for the annual (1981–2014) and two hydrological seasons: the wet season (May–October) and the dry season (November–April). Significance was assessed at the 5% (α = 0.05) and 1% (α = 0.01) levels.

### Results Section (Template)

Of the 36 station–scale combinations tested, 4 showed statistically significant trends (p < 0.05) according to the Modified MK test. The serial autocorrelation analysis indicated that 3 stations exhibited significant Lag-1 autocorrelation at the annual scale, justifying the use of the Modified MK correction. Agreement between Standard MK and Modified MK was high (34/36 combinations, 94.4%), indicating that autocorrelation had a limited but non-negligible effect on trend conclusions.

## 6. References

- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*, 13, 245–259.
- Kendall, M. G. (1975). *Rank Correlation Methods* (4th ed.). Griffin, London.
- Sen, P. K. (1968). Estimates of regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63, 1379–1389.
- Hamed, K. H., & Rao, A. R. (1998). A modified Mann–Kendall trend test for autocorrelated data. *Journal of Hydrology*, 204, 182–196.
- Gilbert, R. O. (1987). *Statistical Methods for Environmental Pollution Monitoring*. Van Nostrand Reinhold, New York.
- Önöz, B., & Bayazit, M. (2003). The power of statistical tests for trend detection. *Hydrological Sciences Journal*, 48, 93–98.
- Yue, S., Pilon, P., Phinney, B., & Cavadias, G. (2002). The influence of autocorrelation on the ability to detect trend in hydrological series. *Hydrological Processes*, 16, 1807–1829.
- Yue, S., & Wang, C. (2004). The Mann–Kendall test modified by effective sample size to detect trend in serially correlated hydrological series. *Water Resources Research*, 40, W08307.
- WMO (2008). *Guide to Hydrological Practices* (WMO-No. 168). World Meteorological Organization, Geneva.

---
*End of Research Summary  |  Generated: 2026-05-27  |  Script v4.0*