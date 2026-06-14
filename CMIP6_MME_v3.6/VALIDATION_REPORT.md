# VALIDATION REPORT — CMIP6_MME_v3.6

**Date**: 2026-06-13  
**Python**: 3.12 (core pipeline)  
**config_version: 3.6.0  
**Data**: **7 GCMs** (ACCESS-ESM1-5, CESM2, CanESM5, EC-Earth3, FGOALS-g3,
MIROC6, MRI-ESM2-0), Raw + BC, historical + SSP245 + SSP585 (42 CSVs),
12 observed stations, Prachuap Khiri Khan, baseline 1981–2014,
near future 2021–2050.

---

## 1. Test execution

| Suite | Passed | Skipped | Failed |
|-------|-------:|--------:|-------:|
| Original computational tests | 22 | 8† | 0 |
| New v3.5 fix tests | 21 | 0 | 0 |
| **Total** | **43** | **8** | **0** |

† 8 skipped tests exercise the figure/GIS stage (need geopandas + boundary shapefile).

Offline runners: `python tests/test_v35_fixes.py` · `python tests/_run_original.py`

---

## 2. Real-data results (7-GCM ensemble)

### Validation skill (median across 12 stations, 7-GCM MME, real data)

| Season | n_years | median KGE_Raw | median KGE_BC | median \|PBIAS_Raw\| | median \|PBIAS_BC\| |
|--------|--------:|---------------:|--------------:|-------------------:|------------------:|
| Annual | 34 | 0.03 | 0.06 | 8.7% | 1.4% |
| Wet | 34 | 0.12 | 0.17 | 14.8% | 0.9% |
| Dry | 33 | -0.24 | -0.08 | 10.5% | 3.6% |

### Projected Annual change — 7-GCM MME mean across stations (delta vs each model's BC-historical)

| Scenario | MME mean Δ% | inter-station range | typical inter-model P25–P75 |
|----------|------------:|---------------------|------------------------------|
| ssp245 | 0.5% | -2.5% … 3.0% | -4.9% … 4.9% |
| ssp585 | -5.0% | -8.8% … -1.7% | -13.7% … 4.1% |

**Reading:**
- Bias correction improves median KGE in every season and cuts median |PBIAS|
  from 9–15% (Raw) to ~1–4% (BC).
- With 7 GCMs the Annual signal is modest: ~0% under SSP245 and ~−5% under
  SSP585, with an inter-model P25–P75 that **straddles zero** — i.e. the models
  do not agree on the sign at many stations. This is the honest ensemble
  message and **differs markedly from a 2-GCM subset** (which had shown ~−14%),
  illustrating why ensemble size and inter-model spread must be reported, not
  just the mean.

---

## 3. Multi-GCM correctness verified

| Aspect | Result |
|--------|--------|
| Models discovered | 7 distinct GCMs from filenames (incl. EC-Earth3 `gr` grid, CESM2 `r11i1p1f1`) |
| Mixed calendars | ACCESS/EC-Earth3/MIROC6/MRI Gregorian vs CESM2/CanESM5/FGOALS-g3 noleap → all aligned to a common 365-day grid (29 Feb stripped); common = union = 12 410 days |
| Ensemble rule | one model, one vote; realizations pre-averaged; `n_models` = distinct models |
| Change% reference | per-model delta vs that model's own BC-historical baseline; all 7 contribute (each has historical + future) |
| Daily MME export | 6 self-describing workbooks + manifest (see §4) |

---

## 4. Output files (self-describing names)

`MME_daily_{dataset}_{scenario}_{N}GCM_{area}.xlsx` — sheet INFO (model list,
period, calendar, aggregation) + sheet `data` (wide YEAR/MONTH/DAY/stations,
like observed). `N` is per (dataset, scenario).

```
MME_daily_Raw_historical_7GCM_prachuap.xlsx   (1981–2014)
MME_daily_Raw_ssp245_7GCM_prachuap.xlsx       (2015–2100)
MME_daily_Raw_ssp585_7GCM_prachuap.xlsx       (2015–2100)
MME_daily_BC_historical_7GCM_prachuap.xlsx    (1981–2014)
MME_daily_BC_ssp245_7GCM_prachuap.xlsx        (2015–2100)
MME_daily_BC_ssp585_7GCM_prachuap.xlsx        (2015–2100)
MME_daily_manifest_prachuap.csv               (index of all the above)
```

Master workbook `MASTER_RESULTS_prachuap.xlsx` now carries a **Models** sheet
documenting the ensemble composition per dataset/scenario.

---

## 5. Generalising to other areas / inputs

Fully config-driven — to run another province/basin: set `study_area`,
`paths`, `seasons`, `periods`, `scenarios` in `config.yaml`. The CSV discovery,
station auto-detection, calendar alignment and naming all adapt automatically.
A 360-day-calendar model (none here) triggers a warning, since it would need
upstream calendar conversion before daily averaging.

---

## 6. Manuscript actions (not code)

- Fill `provenance.bias_correction` (method, software+version, DOI).
- Report ensemble size (7) AND inter-model agreement (P25/P75, sign agreement) — do not report only the MME mean.
- Justify the 1981–2014 baseline; document the equal-weighting choice and any model-family redundancy.
- Run the figure/GIS stage with a boundary shapefile and pass figure-QC before submission.
