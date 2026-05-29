# Discussion — Trend Method Comparison

## 5.1 Why Method Choice Matters for Monsoon Rainfall Trend Detection
Serial autocorrelation inflates Type I error rates in the Standard MK test, potentially
overstating the prevalence of significant trends. In this dataset, 10 of 12 stations
exhibited significant lag-1 autocorrelation (α = 0.05), with ρ₁ values up to 0.583
(Station S3, Wet Season). The MMK correction factor reached a maximum of 2.725
(S3 Wet Season; n_eff = 12.48 years), indicating substantial variance inflation for
high-autocorrelation station-scale combinations, while remaining at 1.000 for stations
without significant serial dependence.

## 5.2 MMK vs PW-MK: Conservative vs Liberal Correction
The MMK and PW-MK approaches produced divergent results in the Wet Season scale.
MMK eliminated all 2 significant decreasing trends detected by Standard MK, while
PW-MK eliminated 3 significant trends and caused 1 direction change. This suggests
that the prewhitening step in PW-MK may overcorrect when trend magnitude is high
relative to autocorrelation strength.

## 5.3 TFPW-MK: Liberal Bias in This Dataset
TFPW-MK detected 7 significant trends versus 6 for Standard MK.
The TFPW approach removes autocorrelation from the detrended series, preserving the
estimated trend. In this dataset, this resulted in slightly greater sensitivity to
weaker trends, particularly in the Wet Season and Dry Season.

## 5.4 Scale-Specific Sensitivity
The Wet Season scale showed the greatest sensitivity to autocorrelation correction:
Standard MK detected 2 significant decreasing trends, while MMK and PW-MK detected
none after correction. This highlights the risk of using Standard MK in wet-season
monsoon series where serial persistence is strongest.

## 5.5 Recommendation for Method Selection
Despite correction factors as large as 2.725 for strongly autocorrelated stations,
the overall pattern of detected trends was robust. For publication, we recommend
reporting all four methods and noting stations where method choice changes the
conclusion. Four station-scale combinations showed method-dependent significance
or direction: S5 Wet Season (MK: significant; MMK and PW-MK: non-significant),
S6 Wet Season (MK: significant; MMK and PW-MK: non-significant), S3 Wet Season
(MK and MMK: non-significant; TFPW-MK: significant), and S4 Dry Season (MK,
MMK, and TFPW-MK: significant; PW-MK: non-significant). Source: Table M4
(Table_M4_Station_Disagreement_Inventory.csv).
