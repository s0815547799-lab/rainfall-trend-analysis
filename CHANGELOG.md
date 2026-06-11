# Changelog

All notable changes to this project are documented here.

---

## [v4.1_defect_fixes] — 2026-06-11

### Fixed

#### C-01 — PW-MK Sen's slope corrected to use original series
**File:** `rta/trend_tests.py::pw_mk()`

`standard_mk(y)` was called on the prewhitened series `y`, causing `sens_slope(y)` to
run on residuals instead of rainfall. Prewhitened residuals have expected slope β·(1−ρ₁),
not β (Yue & Wang 2004, §2).

Change: after `standard_mk(y)`, override `slope_Q/slope_lo/slope_hi` with
`sens_slope(x)` results from the original series. Z, p-value, tau, and significance
flags are unaffected — they are correctly derived from `y`.

#### C-03 — MMK field significance added to `field_sig_summary()`
**File:** `rta/field_sig.py::field_sig_summary()`

Walker and Livezey-Chen tests were run only for Standard MK. Four columns were absent
from the output DataFrame: `Walker_p_MMK`, `Walker_sig_MMK`, `LC_p_MMK`, `LC_sig_MMK`.

Change: Walker test now called for both MK and MMK using respective `n_sig_*` counts.
LC p-value for MMK derived by applying the MMK-based observed fraction against the
existing MK null distribution. Valid because permutation destroys autocorrelation,
making the null fractions method-invariant. Zero-station fallback row also updated.

#### CM-05 — Figure 3 anomaly baseline restricted to configured baseline period
**Files:** `CMIP6_MME_v2/src/figures/make.py::fig3_timeseries()`,
           `CMIP6_package/src/figures/make.py::fig3_timeseries()`

`obs.groupby("season").rainfall.mean()` used the entire obs series (historical + future
concatenated) as the anomaly baseline, producing a reference climatology that shifts
when the future window changes (non-reproducible).

Change: filter `obs` to `cfg["periods"]["baseline"]` years before computing the mean.
Baseline period `[1981, 2014]` is already defined in both `config/config.yaml` files.

---

## [v4.0_hydroclimatology_Q1] — 2026-05-27

### Summary
Full Q1-standard hydroclimatological trend analysis pipeline for the
Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand (1981–2014).
Introduces the `rta/` modular package, four trend methods, field significance,
checkpoint/resume, and true WGS84 geographic spatial maps.

### Added

#### rta/ Package (new)
- `rta/config.py` — shared constants, colour palette, `savefig` helper
- `rta/io.py` — CSV discovery, QC, checkpoint wrappers, `load_coords`
- `rta/aggregation.py` — annual / wet / dry / monthly aggregation + dry-season validation
- `rta/autocorr.py` — lag-k autocorrelation functions
- `rta/trend_tests.py` — Standard MK, Modified MK (Hamed & Rao 1998), Sen's slope
- `rta/pw.py` — Prewhitening MK (Yue & Wang 2004)
- `rta/tfpw.py` — Trend-Free Prewhitening MK (Yue et al. 2002)
- `rta/batch.py` — `run_all`, `build_comparison`, `build_4method_comparison`
- `rta/field_sig.py` — Walker (1914) binomial test + Livezey-Chen (1983) Monte Carlo
- `rta/field_significance.py` — parallel field significance implementation (v3 path)
- `rta/checkpoint.py` — 6-step pickle checkpoint/resume system
- `rta/spatial.py` — `load_coords`, `validate_coords`, `coords_to_df`
- `rta/spatial_maps.py` — top-level re-export of all spatial figure functions
- `rta/excel_output.py` — 9-sheet Excel workbook writer
- `rta/markdown.py` — paper-ready Markdown research summary writer

#### Figure Modules (new)
- `rta/figures/timeseries.py` — Fig 1, Fig 2
- `rta/figures/bars.py` — Fig 3
- `rta/figures/comparison.py` — Fig 4
- `rta/figures/heatmaps.py` — Fig 5
- `rta/figures/acf_plots.py` — Fig 6, Fig 12
- `rta/figures/climatology.py` — Fig 7
- `rta/figures/spatial.py` — Fig 8 (index-based legacy)
- `rta/figures/taylor.py` — Fig 9 (Taylor diagram)
- `rta/figures/method_comparison.py` — Fig 10, Fig 11
- `rta/figures/field_sig_plot.py` — Fig 13
- `rta/figures/spatial_maps.py` — Fig 14, Fig SpatialStation, Fig SpatialMethods,
  Fig SpatialFieldSig, Fig SpatialFull (true geographic WGS84 maps)
- `rta/figures/helpers.py` — shared rendering helpers

#### New Scripts
- `rainfall_trend_analysis_v4.py` — modular pipeline: checkpoint/resume,
  4 trend methods, field significance, 28 publication figures, 9-sheet Excel
- `station_coordinates.csv` — WGS84 coordinates for 128 stations
  (lat 11.18–12.59°N, lon 99.55–99.96°E; all 12 rainfall stations present)

#### Documentation
- `CLAUDE.md` — full project specification, module inventory, constants reference,
  execution order, statistical workflow, spatial module documentation
- `CHANGELOG.md` — this file

### Changed
- `rainfall_trend_analysis_v3.py` — extended with PW-MK, TFPW-MK, field
  significance, checkpoint/resume, 10 additional figures (Figs 9–14e),
  CLI flags `--no-resume` / `--no-pdf`; all original 8 figures preserved
- `.gitignore` — excludes runtime outputs, checkpoints, test figures

### Fixed
- `rta/spatial.py` `load_coords`: `pd.read_csv(..., dtype=str)` prevents pandas
  from reading integer station IDs as float64, eliminating `'500001.0'` key
  mismatch (v3 coordinate loader)
- `rta/io.py` `load_coords`: same `dtype=str` fix for v4 coordinate loader;
  root cause was `iterrows()` upcasting int64 to float64 via row Series widening

### Validated
- 12,418 daily records, 1981–2014, 12 stations, 0% missing
- 144/144 statistical results numerically identical v3 ↔ v4
- Dry-season hydrological year: 35 blocks (1981–2015), all PASS
- Autocorrelation-corrected MK applied to S3 (r₁=0.47), S5 (r₁=0.41), S11 (r₁=−0.35)
- Field significance: dry season Walker p < 0.05, LC-MC p < 0.05 (field-significant)
- Station coordinate coverage: 12/12 (1.0) both v3 and v4 paths
- Checkpoint recovery: all 6 steps load cleanly; figures regenerate identically

---

## [v2.0] — prior

- Initial single-file pipeline `rainfall_trend_analysis_v3.py`
- Standard MK + Modified MK (Hamed & Rao 1998) + Sen's slope
- 8 publication figures, 6-sheet Excel, Markdown summary
- Temporal scales: Annual, Wet (May–Oct), Dry (Nov–Apr hydrological year)
