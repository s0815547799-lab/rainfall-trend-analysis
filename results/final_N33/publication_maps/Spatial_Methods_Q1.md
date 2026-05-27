# Spatial Interpolation Methods — Q1 Publication Notes

**Analysis period:** 1981–2014
**Province:** Prachuap Khiri Khan, Western Thailand
**Stations:** 12
**Boundary source:** Official province shapefile (30_amarea_prachuap_khiri_khan.shp, polygon type)

## 2.5 Spatial Interpolation

Spatially continuous rainfall trend fields were estimated by interpolating station-level Mann–Kendall Z statistics and Sen's slope estimates onto a 120×120 regular grid covering the province extent. Two methods were evaluated:

**Inverse-Distance Weighting (IDW, power = 2):** A deterministic method assigning weights proportional to the reciprocal squared distance from each query point to the data stations (Shepard, 1968).

**Radial-Basis Function (RBF, thin-plate spline, smoothing = 0.5):** A kernel-based interpolant fitted via `scipy.interpolate.RBFInterpolator`; the thin-plate spline kernel minimises bending energy and provides smooth gradients (Wahba, 1990).

Method selection used Leave-One-Out Cross-Validation (LOOCV). At each iteration, one station is withheld, the surface is refit on the remaining n−1 stations, and the withheld value is predicted. The method with the lower root-mean-square error (RMSE) was applied for all variables and scales.

**Selected method: IDW**

### LOOCV Results — Annual Scale

| Variable | RMSE | MAE | Bias | R² |
|----------|------|-----|------|-----|
| MK_Z | 1.0771 | 0.8898 | -0.0441 | -0.1839 |
| MMK_Z | 1.0484 | 0.8646 | -0.0482 | -0.1784 |
| PW_Z | 0.9610 | 0.7920 | -0.0578 | -0.1352 |
| TFPW_Z | 1.0196 | 0.8322 | -0.0571 | -0.1429 |
| Sen_Slope | 5.0469 | 3.7344 | -0.2296 | -0.4344 |

### IDW vs RBF comparison (reference variable: MMK_Z)

| Method | RMSE | MAE | Bias | R² |
|--------|------|-----|------|-----|
| IDW | 1.0837 | 0.9148 | -0.1165 | -0.2591 |
| RBF | 1.0484 | 0.8646 | -0.0482 | -0.1784 |

## References

- Shepard, D. (1968). A two-dimensional interpolation function for irregularly-spaced data. *Proc. 23rd ACM National Conference*, 517–524.
- Wahba, G. (1990). *Spline Models for Observational Data*. SIAM, Philadelphia.
- Mann, H.B. (1945). Non-parametric tests against trend. *Econometrica*, 13, 245–259.
- Kendall, M.G. (1975). *Rank Correlation Methods* (4th ed.). Griffin, London.
- Hamed, K.H. & Rao, A.R. (1998). A modified Mann–Kendall trend test for autocorrelated data. *Journal of Hydrology*, 204, 182–196.
- Yue, S. & Wang, C. (2004). The Mann–Kendall test modified by effective sample size to detect trend in serially correlated hydrological series. *Water Resources Research*, 40, W08307.
- Yue, S., Pilon, P., Phinney, B. & Cavadias, G. (2002). The influence of autocorrelation on the ability to detect trend in hydrological series. *Hydrological Processes*, 16, 1807–1829.
- Sen, P.K. (1968). Estimates of the regression coefficient based on Kendall's tau. *JASA*, 63, 1379–1389.

---
*Generated automatically by rta.spatial_publication_q1 from results/final_N33/ publication archive.*