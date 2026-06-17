# Package Manifest — FINAL_RELEASE.zip

**Package:** Comparative_4MMK — v2.1  
**Date:** 2026-06-17  
**MD5 (src/Comparative_4MMK.py):** f5102159a7643976c105c5f6287765e3

---

## Directory Structure

```
FINAL_RELEASE/
├── src/
│   └── Comparative_4MMK.py          # Production source (2161 lines, 109 KB)
├── tests/
│   └── test_validation.py           # Formal pytest validation suite (T01–T24)
├── docs/
│   └── AUDIT_LOG.md                 # Scientific audit log (FIX-1 through FIX-9)
├── FINAL_RELEASE_REPORT.md          # Comprehensive release report
├── VALIDATION_SUMMARY.md            # Test results summary (27/27 PASS)
├── PACKAGE_MANIFEST.md              # This file
├── requirements.txt                 # Pinned Python dependencies
├── REFERENCE_EXECUTION_OUTPUTS/
│   ├── figures/                     # 13 figures × 2 formats (PNG + PDF) = 26 files
│   │   ├── Figure_01_Station_Map.{png,pdf}
│   │   ├── Figure_02_Climatology.{png,pdf}
│   │   ├── Figure_03_ACF_PACF.{png,pdf}
│   │   ├── Figure_04_Method_Comparison.{png,pdf}
│   │   ├── Figure_05_TypeI_Error.{png,pdf}
│   │   ├── Figure_06_Power.{png,pdf}
│   │   ├── Figure_07_Variance_Distortion.{png,pdf}
│   │   ├── Figure_08_MC_Distributions.{png,pdf}
│   │   ├── Figure_09_False_Positive_Heatmap.{png,pdf}
│   │   ├── Figure_09b_FDR_BH_Corrected.{png,pdf}
│   │   ├── Figure_10_Sensitivity.{png,pdf}
│   │   ├── Figure_11_Effective_Sample_Size.{png,pdf}
│   │   ├── Figure_12_Decision_Framework.{png,pdf}
│   │   └── Figure_13_Summary_Dashboard.{png,pdf}
│   ├── tables/                      # 9 tables × 2 formats (CSV + XLSX) = 18 files
│   │   ├── Table_01_Station_Metadata.{csv,xlsx}
│   │   ├── Table_02_Climatology.{csv,xlsx}
│   │   ├── Table_03_Autocorrelation.{csv,xlsx}
│   │   ├── Table_04_Trends.{csv,xlsx}
│   │   ├── Table_05_TypeI_Error_MC.{csv,xlsx}
│   │   ├── Table_06_Power.{csv,xlsx}
│   │   ├── Table_07_Variance_Distortion.{csv,xlsx}
│   │   ├── Table_08_Sensitivity.{csv,xlsx}
│   │   └── Table_09_FDR_BH_Corrected.{csv,xlsx}
│   ├── processed/                   # 10 intermediate CSV files
│   │   ├── annual_rainfall.csv
│   │   ├── fdr_analysis_bh_corrected.csv
│   │   ├── montecarlo_power.csv
│   │   ├── montecarlo_type_i.csv
│   │   ├── monthly_rainfall.csv
│   │   ├── seasonal_rainfall.csv
│   │   ├── sensitivity_sample_size.csv
│   │   ├── sensitivity_variance.csv
│   │   ├── station_metadata.csv
│   │   └── variance_distortion.csv
│   ├── simulations/                 # 2 simulation output CSVs
│   │   ├── power_analysis.csv
│   │   └── type_i_error.csv
│   ├── All_Tables_Publication.xlsx  # Combined publication workbook
│   ├── QA_QC_Report.txt             # Data quality report
│   └── pipeline_log.txt             # Full execution log
└── TEST_RESULTS/
    └── validation_results.txt       # 27/27 PASS output from validation run
```

---

## File Counts

| Category | Files |
|---|---|
| Source code | 1 |
| Tests | 1 |
| Documentation | 3 |
| Figures (PNG) | 14 |
| Figures (PDF) | 14 |
| Tables (CSV) | 9 |
| Tables (XLSX) | 9 |
| Processed CSVs | 10 |
| Simulation CSVs | 2 |
| Publication workbook | 1 |
| QA/logs | 2 |
| Manifest/requirements | 2 |
| **Total** | **68** |

---

## Corrections Integrated

| Fix | Classification | Description |
|---|---|---|
| FIX-1 | CRITICAL | FDR analysis: BH correction properly applied |
| FIX-2 | CRITICAL | AR1Generator: independence between MC iterations |
| FIX-3/9 | CRITICAL | VIF clamp: numerically essential for negative AC |
| FIX-4 | MODERATE | PW-MK: slope from original series |
| FIX-5 | MINOR | CI: t-distribution replaces z=1.96 |
| FIX-6 | MINOR | AR1Generator: 50-step burn-in added |
| FIX-7 | CRITICAL | MMK: significant-lag filter per H&R98 Eq.(3) |
| FIX-8 | REDESIGNED | PW/TFPW: MIN_N=10 removed; n≥5 algorithm minimum |
| FIX-9 | CRITICAL | VIF clamp reclassified CRITICAL after MC validation |

---

## Python Environment

| Package | Version |
|---|---|
| Python | 3.11.15 |
| numpy | 2.4.6 |
| pandas | 3.0.3 |
| scipy | 1.17.1 |
| matplotlib | 3.11.0 |
| statsmodels | 0.14.6 |
| openpyxl | 3.1.5 |

---

## Reproducibility

- Random seed: `SEED = 42` (hardcoded throughout)
- Monte Carlo n_iter: 10,000 (production); 300 (CI/reference outputs)
- All outputs are deterministic given the same seed and n_iter
