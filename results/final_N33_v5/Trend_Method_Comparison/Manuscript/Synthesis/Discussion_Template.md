# Discussion — Trend Method Comparison

## 5.1 Why Method Choice Matters for Monsoon Rainfall Trend Detection
Serial autocorrelation inflates Type I error rates in the Standard MK test, potentially
overstating the prevalence of significant trends. In this dataset, 10 of 12 stations
exhibited significant lag-1 autocorrelation (α = 0.05), with ρ₁ values up to [max ρ₁].
However, the MMK correction factor was modest (max CF = 1.098),
suggesting that despite the presence of autocorrelation, its practical impact on MK test
conclusions was limited in this basin.

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
Given the modest correction factors observed (CF < 1.10 for all stations), the
differences between methods are not severe. However, for publication, we recommend
reporting all four methods and noting stations where method choice changes the
conclusion. [Insert specific station names from Table M4.]
