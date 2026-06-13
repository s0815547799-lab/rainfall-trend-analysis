# Configuration Guide — Hydroclimatic Trend Analysis Framework

**Framework version:** 1.0

---

This guide documents the proposed `config/province.yaml` structure that will make the pipeline province-agnostic. This is a **blueprint — not yet implemented**. Currently the pipeline is configured via constants in `rta/config.py` and command-line arguments.

---

## 1. Current Configuration Mechanism

All pipeline behaviour is controlled by constants defined at the top of `rta/config.py` (lines 24–38). There is no configuration file; changing any setting requires editing Python source directly.

### 1.1 Statistical constants (`rta/config.py`)

| Constant | Value | Purpose |
|----------|-------|---------|
| `WET_MONTHS` | `[5, 6, 7, 8, 9, 10]` | Wet season months (May–Oct) |
| `DRY_MONTHS` | `[11, 12, 1, 2, 3, 4]` | Dry season months (Nov–Apr) |
| `WET_THR` | `1.0` mm/day | WMO wet-day threshold |
| `MIN_N` | `10` | Minimum years for MK test |
| `ALPHA_005` | `0.05` | Primary significance level |
| `ALPHA_001` | `0.01` | Secondary significance level |
| `Z_005` | `1.9600` | Two-tailed critical Z at α = 0.05 |
| `Z_001` | `2.5758` | Two-tailed critical Z at α = 0.01 |
| `DPI` | `600` | Figure output resolution |
| `SAVE_PDF` | `True` | Also save PDF alongside PNG |
| `MISS_FLAGS` | `[-99, -999, -9999, -9.99e+20, 9.99e+20, 1e+20]` | Missing-value sentinel values |

### 1.2 Province-specific strings embedded in source files

Province-specific text is hard-coded in several modules. Each must be edited manually when porting to a new province:

| File | Lines | Hard-coded content |
|------|-------|--------------------|
| `rta/figures/spatial_maps.py` | 244, 562 | Figure suptitles with `"Prachuap Khiri Khan Basin"` |
| `rta/markdown.py` | 86–87 | `"Phetchaburi–Prachuap Khiri Khan River Basin"` in research summary header |
| `rta/trend_comparison_analysis.py` | 1408, 1524 | Province and basin name in manuscript templates |
| `rta/trend_comparison_analysis.py` | 1633–1634 | Hard-coded station ID allowlist (`"500001"` … `"500301"`) |

### 1.3 Input/output discovery (already province-agnostic)

- **Rainfall CSV:** auto-discovered via glob — first `.csv` in the target folder not prefixed with `Output_`
- **Coordinates CSV:** auto-discovered via `*coord*.csv` or `*station*.csv` glob
- **Output directory:** same as the input CSV directory (set at runtime via command-line argument)

---

## 2. Proposed `province.yaml` Structure

The full proposed YAML with inline comments for every key is shown below. Copy this file to `config/<province_name>.yaml` for each new province.

```yaml
# config/province.yaml
# Province configuration for the Hydroclimatic Trend Analysis Framework
# All province-specific settings are controlled from this file.
# Copy this file to config/<province_name>.yaml for each new province.

# ── Province identity ────────────────────────────────────────────────────────
province:
  name: "Prachuap Khiri Khan"          # Used in figure titles and reports
  basin_name: "Phetchaburi–Prachuap Khiri Khan River Basin"  # Full basin name
  country: "Thailand"                   # Used in figure titles
  region: "Western Thailand"            # Used in reports
  epsg: 4326                            # Coordinate reference system

# ── Study period ─────────────────────────────────────────────────────────────
period:
  start_year: 1981                      # First year of analysis
  end_year: 2014                        # Last year of analysis (inclusive)
  label: "1981–2014"                    # Display label for figures and reports
  n_stations: 12                        # Number of analysis stations

# ── Input data ───────────────────────────────────────────────────────────────
data:
  rainfall_dir: "."                     # Directory containing rainfall CSV (default: repo root)
  rainfall_file: null                   # Explicit filename; null = auto-discover *.csv
  coordinates_file: null                # Explicit path; null = auto-discover *coord*.csv
  shapefile: null                       # Province boundary shapefile (.shp); null = skip spatial maps
  missing_flags: [-99, -999, -9999, -9.99e20, 9.99e20, 1.0e20]  # Missing value sentinels

# ── Season definitions ────────────────────────────────────────────────────────
seasons:
  wet_months: [5, 6, 7, 8, 9, 10]      # May–October (monsoon season)
  dry_months: [11, 12, 1, 2, 3, 4]     # November–April (dry season)
  wet_threshold_mm: 1.0                 # WMO wet-day threshold (mm/day)
  wet_label: "Wet Season (May–Oct)"    # Display label
  dry_label: "Dry Season (Nov–Apr)"    # Display label
  annual_label: "Annual (Jan–Dec)"     # Display label

# ── Statistical thresholds ────────────────────────────────────────────────────
statistics:
  alpha: 0.05                           # Primary significance level
  alpha_01: 0.01                        # Secondary significance level
  min_years: 10                         # Minimum years required for MK test
  field_sig_permutations: 10000         # LC-MC Monte Carlo permutation count
  field_sig_seed: 42                    # Random seed for reproducibility
  completeness_annual: 0.80             # Min fraction of days for annual aggregate
  completeness_seasonal: 0.80           # Min fraction for wet/dry aggregate
  completeness_monthly: 0.60            # Min fraction for monthly aggregate

# ── Outputs ──────────────────────────────────────────────────────────────────
outputs:
  output_dir: null                      # null = same directory as rainfall_file
  prefix_v3: "Output_TrendV2"           # Filename prefix for v3-style figures
  prefix_v4: "Output_TrendV4"           # Filename prefix for v4-style figures
  dpi: 600                              # Figure resolution (dots per inch)
  save_pdf: true                        # Also save PDF alongside PNG
  save_tiff: false                      # TIFF files are very large (60–150 MB); off by default

# ── Checkpoints ───────────────────────────────────────────────────────────────
checkpoints:
  enabled: true                         # Save/load 6-step checkpoints
  directory: "checkpoints"              # Subdirectory name within output_dir
```

---

## 3. Key Configuration Decisions

### 3.1 Season definitions

`WET_MONTHS = [5, 6, 7, 8, 9, 10]` and `DRY_MONTHS = [11, 12, 1, 2, 3, 4]` reflect Thailand's Southwest Monsoon calendar, where the rainy season runs from May through October and the dry season spans November through April of the following hydrological year.

For other climate regimes these must change. The month sets must be **non-overlapping** and together must cover all 12 months (see Section 4 for validation rules).

**Example — Sahelian Africa** (e.g., Burkina Faso, Mali):

```yaml
seasons:
  wet_months: [6, 7, 8, 9]             # June–September (ITCZ-driven monsoon)
  dry_months: [10, 11, 12, 1, 2, 3, 4, 5]   # October–May
  wet_label: "Wet Season (Jun–Sep)"
  dry_label: "Dry Season (Oct–May)"
```

**Example — Mediterranean climate** (e.g., southern Spain, Morocco):

```yaml
seasons:
  wet_months: [10, 11, 12, 1, 2, 3]   # October–March (winter rains)
  dry_months: [4, 5, 6, 7, 8, 9]      # April–September
  wet_label: "Wet Season (Oct–Mar)"
  dry_label: "Dry Season (Apr–Sep)"
```

Note that the **dry-season hydrological year convention** (November and December of year *Y* shifted to year *Y+1*) is hard-coded in the aggregation logic for the Thai configuration. For climates where the dry season does not straddle the calendar year boundary (e.g., April–September), this shift is unnecessary and the corresponding logic in `rta/aggregation.py` would need to be updated.

### 3.2 Missing value flags

The default flags (`-99`, `-999`, `-9999`, `-9.99×10²⁰`, `9.99×10²⁰`, `1×10²⁰`) match the Thai Meteorological Department data export format. Different data providers use different sentinel values:

| Data source | Typical missing flag |
|-------------|----------------------|
| Thai Meteorological Department | `-99`, `-9999`, `9.99e+20` |
| WMO GHCN-Daily | `-9999` |
| ERA5 reanalysis fill | `NaN` (no sentinel needed) |
| NASA GPM IMERG | `−9999.9` |

If the input data uses different flags, add them to the `missing_flags` list. Values are replaced with `NaN` during quality control before any aggregation or statistical testing.

### 3.3 Significance level

`alpha = 0.05` is standard for hydroclimatological trend analysis. Some journals or institutional guidelines use `alpha = 0.10` for trend tests because the Mann-Kendall test is conservative (low power for short series). If `alpha_01 = 0.01` secondary markers are not needed, they can be disabled by setting `alpha_01` equal to `alpha`.

### 3.4 DPI and output formats

`dpi = 600` meets the minimum requirement for most Q1 hydrology journals (e.g., *Journal of Hydrology*, *Water Resources Research*). Set `save_pdf: true` for vector-format submissions. `save_tiff: false` is the recommended default — a single 600 DPI TIFF at typical figure size (18 × 12 cm) can exceed 60 MB.

---

## 4. Config Validation

The following checks should be performed before the pipeline executes when the configuration file is implemented:

| Rule | Check |
|------|-------|
| Period ordering | `start_year < end_year` |
| Minimum period length | `end_year - start_year + 1 >= min_years` |
| Season month ranges | `wet_months` and `dry_months` are non-empty lists of integers in `[1, 12]` |
| Season non-overlap | `set(wet_months) ∩ set(dry_months) == ∅` |
| Full-year coverage | `set(wet_months) ∪ set(dry_months) == {1, 2, …, 12}` |
| Significance level | `0 < alpha < 0.5` |
| Minimum years | `min_years >= 5` |
| DPI value | `dpi ∈ {150, 300, 600, 1200}` |
| Shapefile existence | if `shapefile` is not `null`, the `.shp` file exists at the specified path |
| Completeness thresholds | `0 < completeness_monthly <= completeness_seasonal <= completeness_annual <= 1.0` |
| MC permutation count | `field_sig_permutations >= 1000` (fewer degrades p-value resolution) |

---

## 5. Configuration Examples

### Example 1: Prachuap Khiri Khan (current release — validated reference)

This is the configuration that corresponds to the reference dataset included in the repository.

```yaml
province:
  name: "Prachuap Khiri Khan"
  basin_name: "Phetchaburi–Prachuap Khiri Khan River Basin"
  country: "Thailand"
  region: "Western Thailand"
  epsg: 4326

period:
  start_year: 1981
  end_year: 2014
  label: "1981–2014"
  n_stations: 12

data:
  rainfall_dir: "."
  rainfall_file: null
  coordinates_file: null
  shapefile: "30_amarea_prachuap_khiri_khan.shp"
  missing_flags: [-99, -999, -9999, -9.99e20, 9.99e20, 1.0e20]

seasons:
  wet_months: [5, 6, 7, 8, 9, 10]
  dry_months: [11, 12, 1, 2, 3, 4]
  wet_threshold_mm: 1.0
  wet_label: "Wet Season (May–Oct)"
  dry_label: "Dry Season (Nov–Apr)"
  annual_label: "Annual (Jan–Dec)"

statistics:
  alpha: 0.05
  alpha_01: 0.01
  min_years: 10
  field_sig_permutations: 10000
  field_sig_seed: 42
  completeness_annual: 0.80
  completeness_seasonal: 0.80
  completeness_monthly: 0.60

outputs:
  output_dir: null
  prefix_v3: "Output_TrendV2"
  prefix_v4: "Output_TrendV4"
  dpi: 600
  save_pdf: true
  save_tiff: false

checkpoints:
  enabled: true
  directory: "checkpoints"
```

**Station IDs:** `500001`, `500002`, `500003`, `500004`, `500005`, `500006`, `500007`, `500008`, `500009`, `500201`, `500202`, `500301`

---

### Example 2: Chiang Mai Province (Northern Thailand — Ping River Basin)

Northern Thailand shares the Southwest Monsoon season timing but the Ping River Basin has a distinct orographic rainfall regime and a longer reliable record.

```yaml
province:
  name: "Chiang Mai"
  basin_name: "Ping River Basin"
  country: "Thailand"
  region: "Northern Thailand"
  epsg: 4326

period:
  start_year: 1980
  end_year: 2020
  label: "1980–2020"
  n_stations: 20          # Update to match actual station count

data:
  rainfall_dir: "/data/chiang_mai"
  rainfall_file: null
  coordinates_file: null
  shapefile: "/data/chiang_mai/50_chiang_mai_province.shp"
  missing_flags: [-99, -999, -9999, -9.99e20, 9.99e20, 1.0e20]

seasons:
  wet_months: [5, 6, 7, 8, 9, 10]     # Southwest Monsoon — same as Prachuap
  dry_months: [11, 12, 1, 2, 3, 4]
  wet_threshold_mm: 1.0
  wet_label: "Wet Season (May–Oct)"
  dry_label: "Dry Season (Nov–Apr)"
  annual_label: "Annual (Jan–Dec)"

statistics:
  alpha: 0.05
  alpha_01: 0.01
  min_years: 10
  field_sig_permutations: 10000
  field_sig_seed: 42
  completeness_annual: 0.80
  completeness_seasonal: 0.80
  completeness_monthly: 0.60

outputs:
  output_dir: null
  prefix_v3: "Output_TrendV2"
  prefix_v4: "Output_TrendV4"
  dpi: 600
  save_pdf: true
  save_tiff: false

checkpoints:
  enabled: true
  directory: "checkpoints"
```

**Notes for Chiang Mai:**
- The shapefile for Chiang Mai Province is available from GADM at ADM1 level (`gadm.org`, layer THA.5_1) or from DOPA Thailand.
- The station ID allowlist in `rta/trend_comparison_analysis.py` (lines 1633–1634) must be updated to list the Chiang Mai station IDs.
- No other source files require changes if season definitions remain the same as Prachuap Khiri Khan.
