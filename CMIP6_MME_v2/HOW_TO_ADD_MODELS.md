# How to Add More CMIP6 Models

## Current setup
- Province: Prachuap Khiri Khan (stations 500001–500301)
- Model: ACCESS-ESM1-5 (1 model → MME = model itself)
- Scenarios: SSP2-4.5, SSP5-8.5

## Adding a second (or more) model

Place new CSV files in `data/cmip6_raw/` following the naming convention:

```
Raw  (uncorrected):  pr_day_<MODEL>_<SCENARIO>_<REALIZATION>_<GRID>_<DATES>_28sta.csv
QDM  (bias-corrected): bc_pr_day_<MODEL>_<SCENARIO>_<REALIZATION>_<GRID>_<DATES>_28sta.csv
```

Examples:
```
data/cmip6_raw/
  bc_pr_day_ACCESSESM15_ssp245_r1i1p1f1_gn_2015010121001231_28sta.csv   ← existing
  pr_day_ACCESSESM15_ssp245_r1i1p1f1_gn_2015010121001231_28sta.csv       ← existing
  bc_pr_day_MIROC6_ssp245_r1i1p1f1_gn_2015010121001231_28sta.csv         ← ADD second model
  pr_day_MIROC6_ssp245_r1i1p1f1_gn_2015010121001231_28sta.csv            ← ADD second model
  bc_pr_day_CNRMCM61_ssp245_r1i1p1f1_gn_2015010121001231_28sta.csv       ← ADD third model
  ...
```

Required files per model: historical (BC + Raw) + ssp245 (BC + Raw) + ssp585 (BC + Raw) = **6 files per model**.

## Column format
Each CSV must have columns: `YEAR`, `MONTH`, `DAY`, then station columns (numeric IDs).
The pipeline automatically filters to Prachuap stations (those present in observed data).
Non-Prachuap columns (424xxx, 438xxx, 465xxx, etc.) are ignored automatically.

## Re-running the pipeline
```bash
cd CMIP6_MME_v2
python final_run.py                    # Full run with figures
python main.py                         # Computation only (faster)
```

The pipeline will automatically:
- Discover all model CSVs in data/cmip6_raw/
- Build MME (mean/median/P25/P75 across all models)
- Compute validation metrics per model
- Generate all 7 publication figures and 7 tables

## Notes
- Scenario codes are case-insensitive: ssp245 = SSP245 = SSP2-4.5 all accepted
- Column names are case-insensitive (Station/station/STATION all OK)
- Minimum 80% daily data completeness required per season (else NaN, not zero)
- Dry season uses hydrological year convention: Nov(Y)+Dec(Y)+Jan-Apr(Y+1) → label Y+1
