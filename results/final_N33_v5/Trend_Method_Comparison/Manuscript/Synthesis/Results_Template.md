# Results — Trend Method Comparison

## 4.1 Study Design
This study applied four Mann-Kendall-based trend analysis methods to 12 daily rainfall
gauging stations in the Phetchaburi–Prachuap Khiri Khan River Basin, Thailand (1981–2014).
The four methods evaluated were: Standard Mann-Kendall (MK), Modified Mann-Kendall
(MMK, Hamed & Rao 1998), Prewhitening MK (PW-MK, Yue & Wang 2004), and
Trend-Free Prewhitening MK (TFPW-MK, Yue et al. 2002).

## 4.2 Autocorrelation Structure
Significant lag-1 autocorrelation (α = 0.05) was detected in 10 of 12 stations
(83.3%). The MMK correction factor ranged from
1.000 to 2.725
(mean: 1.1137), indicating modest variance inflation
in most cases. The effective sample size n_eff ranged from
12.5 to 34.0 years
(actual N = 34 for all stations).

## 4.3 Detected Trends by Method and Scale

| Method | Annual | Wet Season | Dry Season | Total |
|--------|--------|-----------|-----------|-------|
| Standard MK | 1 | 2 | 3 | 6 |
| Modified MK | 1 | 0 | 3 | 4 |
| PW-MK | 1 | 0 | 2 | 3 |
| TFPW-MK | 1 | 3 | 3 | 7 |

Significance threshold: α = 0.05 (|Z| ≥ 1.96).

## 4.4 Method Comparison
Across all 36 station-scale combinations, 4 showed a change in
significance status when comparing any alternative method to Standard MK. Direction
changes were observed in 4 case(s) — primarily in the Wet Season scale.

The PW-MK correction produced the largest magnitude ΔZ (max |ΔZ| =
1.129, Station S5, Wet Season), driven by high
lag-1 autocorrelation (ρ₁ = 0.456).

TFPW-MK detected 7 significant trends compared to 6 for
Standard MK, suggesting that prewhitening without trend removal may retain or amplify
the trend signal.

## 4.5 Field Significance
Field significance was assessed using both the Walker (1914) binomial test and the
Livezey-Chen (1983) Monte Carlo permutation test (10,000 iterations, seed=42).
For the Annual scale (1/12 stations significant under MK), neither test reached
field significance (Walker p = 0.460, LC-MC p = 0.436). For the Wet Season
(2/12 under MK), neither test was significant (Walker p = 0.118, LC-MC p = 0.099).
For the Dry Season (3/12 under MK), both tests indicated field significance
(Walker p = 0.020, LC-MC p = 0.016), suggesting that the dry-season increasing
trends are unlikely to be due to chance alone. Source: Table M5
(Table_M5_Field_Significance_Comparison.csv).

## 4.6 Key Findings
1. 4 of 36 station-scale combinations changed significance across methods.
2. PW-MK showed the largest deviation from Standard MK (mean ΔZ = 0.0572).
3. TFPW-MK detected the most trends (7); PW-MK the fewest (3).
4. The Dry Season scale was most consistently detected by all four methods (N_sig_MK = 3).
5. Autocorrelation correction (MMK) primarily affected Wet Season results.
