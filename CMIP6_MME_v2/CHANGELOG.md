# CHANGELOG — CMIP6_MME_v2

All changes that materially affect scientific validity, statistical correctness,
reproducibility, or Q1/Q2 publication readiness are recorded here.

---

## [Unreleased] — 2026-06-11

### Fixed

#### FIX-01 · `src/validation/metrics.py` · KGE ddof compliance (CLAUDE.md §12.10)
- **Issue**: `kge()` used `np.std(..., ddof=0)` (population std). CLAUDE.md §12.10
  mandates sample std (`ddof=1`) per Gupta et al. (2009).
- **Impact**: Documentation non-compliance. Numerically: KGE value is unchanged
  because α = σ_s/σ_o is a ratio (ddof cancels). However, the declared methodology
  cited Gupta et al. (2009) while using population std without noting the deviation —
  a reproducibility and peer-review risk.
- **Fix**: Changed `ddof=0` → `ddof=1` in both `std_o` and `std_s` computations.
  Added docstring note explaining the ddof choice and numerical equivalence.

#### FIX-02 · `main.py` · Change% per-model before ensemble aggregation (CLAUDE.md §12.5)
- **Issue**: Change% was computed from `bc_mme["mean"]` (the already-aggregated
  ensemble mean per year). This conflates inter-model spread with the change signal
  and prevents reporting P25/P75 uncertainty of change%.
- **Impact**: Scientific error. The published change% table had no uncertainty range;
  the single value was the change in the MME mean rather than the mean of per-model
  changes (a non-linear transformation where order of operations matters).
- **Fix**: Change% now computed from `per` DataFrame (per-model BC data, near-future
  window [f0, f1]) before ensemble aggregation. Aggregated to mean/P25/P75/n_models
  per (station, season, scenario). New columns added to the `change` DataFrame:
  `change_pct_p25`, `change_pct_p75`, `n_models`. All downstream consumers
  (`fig3`, `fig7`, `level2_station_mme`, `level3_area_summary`, `publication_tables`)
  continue to work unchanged.

#### FIX-03 · `main.py` · CMIP6 model period coverage validation (CLAUDE.md §12.5)
- **Issue**: Models loaded with partial coverage (e.g., historical data starting at
  1985 when baseline requires 1981–2014, or SSP data ending at 2049 when near-future
  window requires 2021–2050) were silently included, biasing ensemble statistics.
- **Impact**: Silent data quality issue. Incomplete models inflate or deflate MME
  statistics depending on which years are missing. Not detectable without this check.
- **Fix**: After loading each model CSV, check that Annual-season year range satisfies
  `min(years) ≤ req_start` AND `max(years) ≥ req_end`. Models failing this check are
  logged with a WARNING and excluded from the ensemble. Required period is [b0, b1]
  for historical and [f0, f1] for SSP scenarios.

#### FIX-04 · `src/figures/make.py` · Geographic map coordinate labels + north arrow (CLAUDE.md §12.9)
- **Issue**: `_map_axes_style()` removed all axis ticks (`ax.set_xticks([])`,
  `ax.set_yticks([])`). No north arrow was present. CLAUDE.md §12.9 requires every
  geographic map to include coordinate tick labels or graticule lines, plus a north
  arrow.
- **Impact**: Every spatial figure (Figures 4–7) was non-compliant with Q1/Q2
  hydroclimatology journal GIS standards (J. Hydrol., WRR, HESS, etc.).
- **Fix**: Replaced blank tick suppression with WGS84 lon/lat tick labels
  (`%.1f°E` / `%.1f°N`, MaxNLocator 3 ticks, 6pt). Added `_add_north_arrow()`
  helper and called it from both `_station_value_map()` and `_station_change_map()`.
  Graticule grid (`:`, α=0.30) replaces the previous blank grid.

#### FIX-05 · `config/config.yaml` · Add `config_version` field (CLAUDE.md §12.11)
- **Issue**: No `config_version` or `run_id` field existed. CLAUDE.md §12.11
  mandates this field and requires it to be logged to every output file.
- **Fix**: Added `config_version: "1.0.0"` at the top of `config.yaml`.
  `main.py` now logs `config_version` in the pipeline-complete INFO message,
  making it traceable in every run log.

#### FIX-06 · `requirements.txt` · Pin package versions (CLAUDE.md §12.11)
- **Issue**: All dependencies used `>=` version specifiers. CLAUDE.md §12.11
  mandates a `requirements.txt` with pinned versions for Q1 publication
  reproducibility.
- **Fix**: Pinned all packages to the tested environment
  (Python 3.11, tested 2026-06-11). See `requirements.txt` for exact versions.
  Header updated to note that `pip freeze > requirements.txt` should be re-run
  after any dependency update and test verification.

---

*All six fixes were verified: 26 unit tests + 4 pipeline smoke tests pass
(30/30 total). No regressions introduced.*
