# Data placement

The large input files are NOT bundled (they are your uploads). Place them here:

- `observed/observed_daily.xlsx`            — daily observed rainfall (YEAR,MONTH,DAY,<stations>)
- `station_metadata/station_metadata.xlsx`  — station, latitude, longitude, altitude
- `cmip6_raw/`                               — CMIP6 CSVs: pr_day_* (Raw) and bc_pr_day_* (BC)
- `boundary/boundary.shp`                    — study-area polygon (required ONLY for figures/GIS)

Then run:  `python main.py`  (core results)  →  `python final_run.py`  (figures + tables).
The `outputs/excel/` folder included in this package holds the REAL results from the
ACCESS-ESM1-5 + CanESM5 run for reference.

## v3.5 outputs added
- `outputs/excel/MME_daily_Raw_<area>.xlsx` — daily across-GCM MME (Raw), wide like observed
- `outputs/excel/MME_daily_BC_<area>.xlsx`  — daily across-GCM MME (BC),  wide like observed
  (sheets: historical / ssp245 / ssp585)
