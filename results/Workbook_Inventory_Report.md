# Workbook Inventory Report
**Project:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan  
**Audit date:** 2026-05-29  
**Auditor:** Automated inspection via pandas + openpyxl  

---

## Phase 1 — Workbook Inventory

### Workbooks Identified

| # | Workbook | Location | Role |
|---|----------|----------|------|
| WB1 | `Output_TrendV4_..._Results.xlsx` | `results/final_N33/excel/` | **Canonical pipeline output — PRIMARY SOURCE for V5** |
| WB2 | `LOOCV.xlsx` | `results/final_N33_v5/validation/` | Spatial interpolation LOOCV validation |
| WB3 | `Interpolation_Comparison.xlsx` | `results/final_N33_v5/validation/` | IDW vs RBF head-to-head |
| WB4 | `ebc6aee6-Rainfall_2Trend_Results.xlsx` | (user-uploaded) | External; different pipeline; predates PW/TFPW |

---

### WB1 — `Output_TrendV4_..._Results.xlsx` (9 sheets)

**Header structure:** Rows 0–1 = title/subtitle (merged cells). Row 2 = column headers. Data starts row 3.  
**Read correctly with:** `pd.read_excel(..., header=0, skiprows=[0,1])`

---

#### S1 — Standard MK
| Field | Value |
|-------|-------|
| Rows | 36 (12 stations × 3 scales) |
| Columns | 13 |
| Column names | `Station` · `Code` · `Scale` · `N` · `S` · `Var(S)` · `Z` · `τ (Kendall)` · `p-value` · `Trend` · `* p<0.05` · `** p<0.01` · `rho_1` |
| Primary key | `(Station, Scale)` |
| Scale values | `Annual (Jan–Dec)` · `Wet Season (May–Oct)` · `Dry Season (Nov–Apr)` |
| Null columns | None |
| Duplicates on (Station,Scale) | 0 |
| Detected method | Standard Mann-Kendall |
| Sample row | Station=500001, Scale=Annual, N=34, S=78, Z=1.1416, p=0.2536, rho_1=0.2599 |

---

#### S2 — Modified MK (H&R98)
| Field | Value |
|-------|-------|
| Rows | 36 |
| Columns | 15 |
| Column names | `Station` · `Code` · `Scale` · `N` · `S` · `Var(S)` · `Var*(S)` · `n_eff` · `ρ₁` · `Z` · `τ (Kendall)` · `p-value` · `Trend` · `* p<0.05` · `** p<0.01` |
| Primary key | `(Station, Scale)` |
| Scale values | Same 3 as S1 |
| Null columns | None |
| Duplicates on (Station,Scale) | 0 |
| Detected method | Modified MK — Hamed & Rao (1998) |
| Additional fields vs S1 | `Var*(S)` (autocorr-adjusted variance) · `n_eff` (effective sample size) |
| Notes | `ρ₁` is lag-1 autocorrelation of **ranked** series (per H&R98). When no significant autocorrelation: Var*(S) = Var(S), n_eff = N. |

---

#### S3 — MK vs MMK Comparison
| Field | Value |
|-------|-------|
| Rows | 36 |
| Columns | 17 |
| Column names | `Station` · `Code` · `Scale` · `ρ₁` · `Sig.AC` · `MK Z` · `MK p` · `MK Trend` · `MK *` · `MMK Z` · `MMK p` · `MMK Trend` · `MMK *` · `ΔZ` · `Δp` · `Agree` · `Note` |
| Primary key | `(Station, Scale)` |
| Null columns | `Note` (26/36 null — filled only when `Agree=No` or `Sig.AC=Yes`) |
| Detected method | MK vs MMK head-to-head |
| Key derived fields | `ΔZ = Z_MMK − Z_MK` · `Δp = p_MMK − p_MK` · `Agree = (MK Trend == MMK Trend)` |
| Notes | All 36 rows have `Agree=Yes` in current dataset. `Sig.AC` = `Yes*` for 3 stations (500003, 500005, 500202). |

---

#### S4 — Sen's Slope
| Field | Value |
|-------|-------|
| Rows | 144 (12 stations × 3 scales × 4 methods) |
| Columns | 11 |
| Column names | `Station` · `Code` · `Scale` · `Method` · `N` · `β (mm/yr)` · `CI_Lower (mm/yr)` · `CI_Upper (mm/yr)` · `Z` · `p-value` · `Trend` |
| Primary key | `(Station, Scale, Method)` |
| Method values | `Standard MK` · `Modified MK` · `PW-MK` · `TFPW-MK` |
| Scale values | Same 3 as S1 |
| Duplicates on (Station,Scale) | 108 (expected — 4 rows per (Station,Scale)) |
| Duplicates on (Station,Scale,Method) | 0 |
| Notes | Long format. CIs computed per-method using the corresponding variance (MK → Var(S), MMK → Var*(S)). |

---

#### S5 — Descriptive Statistics
| Field | Value |
|-------|-------|
| Rows | 12 (one per station, annual scale only) |
| Columns | 11 |
| Column names | `Station` · `Code` · `N (yr)` · `Mean (mm)` · `Median (mm)` · `Max (mm)` · `Min (mm)` · `Std (mm)` · `CV (%)` · `Wet-days/yr` · `Skewness` |
| Primary key | `Station` |
| Scale | None — annual aggregation only |
| Notes | No Scale column. N (yr) = 34 for all stations. |

---

#### S6 — Methods & References
| Field | Value |
|-------|-------|
| Rows | 8 |
| Columns | 3 |
| Column names | Method name · Citation · Description |
| Notes | Free-text reference table. Not for computational use. |

---

#### S7 — 4-Method Comparison ⬅ PRIMARY JOIN TABLE
| Field | Value |
|-------|-------|
| Rows | 36 |
| Columns | 33 |
| Column names | `Station` · `Code` · `Scale` · `rho_1` · `Sig_AC` · `MK_Z` · `MK_p` · `MK_slope` · `MK_sig` · `MK_trend` · `MMK_Z` · `MMK_p` · `MMK_slope` · `MMK_sig` · `MMK_trend` · `PW_Z` · `PW_p` · `PW_slope` · `PW_sig` · `PW_trend` · `TFPW_Z` · `TFPW_p` · `TFPW_slope` · `TFPW_sig` · `TFPW_trend` · `dZ_MMK` · `dZ_PW` · `dZ_TFPW` · `dSlope_MMK` · `dSlope_PW` · `dSlope_TFPW` · `all_agree` · `n_sig_methods` |
| Primary key | `(Station, Scale)` |
| Null columns | None |
| Duplicates on (Station,Scale) | 0 |
| Detected methods | MK + MMK + PW-MK + TFPW-MK — all 4, wide format |
| PW differentiation | PW_Z ≠ MK_Z for 10/36 rows · TFPW_Z ≠ MK_Z for 7/36 rows |
| `sig` column encoding | `'ns'` · `'*'` (p<0.05) · `'**'` (p<0.01) (string) |
| `all_agree` range | All 36 = `'Yes'` in current dataset |
| `n_sig_methods` range | 0 to 4 |
| **Role** | **This is the ONLY sheet read by the V5 spatial pipeline (`sheet_name="S7 4-Method Comparison"`).** PW and TFPW data exist only here — no dedicated S-sheets. |

---

#### S8 — Field Significance
| Field | Value |
|-------|-------|
| Rows | 3 (one per scale) |
| Columns | 12 |
| Column names | `Scale` · `N_stations` · `N_sig_MK` · `N_sig_MMK` · `Frac_sig_MK` · `Frac_sig_MMK` · `Walker_p_MK` · `Walker_sig_MK` · `LC_p_MK` · `LC_sig_MK` · `LC_null_mean` · `LC_null_95th` |
| Primary key | `Scale` |
| Scale notation | Short: `annual` · `wet` · `dry` (not full string) |
| Notes | Walker(1914) + Livezey-Chen(1983) MC tests. LC_null_mean/95th = '—' string (MC not run). None field-significant. |

---

#### S9 — Dry Season Validation
| Field | Value |
|-------|-------|
| Rows | 4 (narrative only) |
| Columns | 2 |
| Notes | Non-tabular status report. Status: PASSED. 35 years (1981–2015) validated. Not for computational join. |

---

### WB2 — `LOOCV.xlsx` (1 sheet)

| Field | Value |
|-------|-------|
| Sheet | `Sheet1` |
| Rows | 15 (5 variables × 3 scales) |
| Columns | 7 |
| Column names | `Scale` · `Variable` · `Method` · `RMSE` · `MAE` · `Bias` · `R2` |
| Primary key | `(Scale, Variable)` |
| Variable values | `MK_Z` · `MMK_Z` · `PW_Z` · `TFPW_Z` · `Sen_Slope` |
| Method values | `IDW` (all rows — IDW won LOOCV selection) |
| Notes | Spatial interpolation validation only. RMSE range: 1.00–1.11. R2 range: −0.25 to −0.26 (poor — expected for sparse network). |

---

### WB3 — `Interpolation_Comparison.xlsx` (1 sheet)

| Field | Value |
|-------|-------|
| Sheet | `Sheet1` |
| Rows | 2 |
| Columns | 5 |
| Column names | `Method` · `RMSE` · `MAE` · `Bias` · `R2` |
| Method values | `IDW` · `RBF` |
| Notes | Annual scale, MMK_Z only. IDW: RMSE=1.084, R2=−0.259. RBF: RMSE=1.110, R2=−0.321. |

---

### WB4 — `ebc6aee6-Rainfall_2Trend_Results.xlsx` (8 sheets)

**Pipeline origin:** Different/older pipeline. No PW or TFPW. Scale notation differs.  
**Header structure:** Row 0 = column headers. Data starts row 1 (no title rows).  
**Read correctly with:** `pd.read_excel(..., header=0)`

| Sheet | Rows | Cols | Column Names | Primary Key | Notes |
|-------|------|------|-------------|-------------|-------|
| `1_Descriptive` | 36 | 8 | Scale · Station · Mean · Std · CV% · Min · Max · Wet-days/yr | (Station,Scale) | Includes wet/dry breakdown; V4 S5 is annual-only |
| `2_Standard_MK` | 36 | 7 | Scale · Station · S · Var(S) · Z · p-value · Tau | (Station,Scale) | Missing Code, N, rho_1 vs V4 S1 |
| `3_Modified_MK` | 36 | 12 | Scale · Station · S · Var(S) · Var_adj · Z · p-value · Tau · n_eff · Correction_Factor · Significant_Lags · Significant | (Station,Scale) | `Significant_Lags` = Python repr string |
| `4_Pettitt_CP` | 36 | 5 | Scale · Station · Change_Point_Year · Pettitt_p · Homogeneity | (Station,Scale) | **NOT in V4 pipeline** |
| `5_Sens_Slope` | 36 | 9 | Scale · Station · Slope_mm_per_year · CI_Low_MK · CI_High_MK · CI_Low_MMK · CI_High_MMK · CI_Low · CI_High | (Station,Scale) | Single slope; dual CIs; no Method column |
| `6_Comparison` | 36 | 4 | Scale · Station · p-value_MK · p-value_MMK | (Station,Scale) | **Minimal** — only p-values, no Z, ΔZ, Agree |
| `7_Research_Summary` | 6 | 3 | Scale · Significant · Count | (Scale,Significant) | Count table; Scale has 3 NaN from merged cells |
| `QC_Report` | 12 | 7 | [Station_ID] · Missing_Count · Missing_% · Interpolated_Count · Max_Gap_Length · Outlier_Count · Upper_Outlier_Fence | Station | Station col = `Unnamed: 0`; all Missing* = 0 |

---

## Phase 2 — Schema Validation

### Method → Source Sheet Mapping

| Method | Dedicated Sheet | Also in S7? | PK | Status |
|--------|----------------|-------------|-----|--------|
| Standard MK | S1 Standard MK | ✅ MK_Z, MK_p, MK_slope, MK_sig, MK_trend | (Station,Scale) | ✅ Complete |
| Modified MK | S2 Modified MK (H&R98) | ✅ MMK_Z, MMK_p, MMK_slope, MMK_sig, MMK_trend | (Station,Scale) | ✅ Complete |
| PW-MK | **None** | ✅ PW_Z, PW_p, PW_slope, PW_sig, PW_trend | (Station,Scale) | ⚠️ S7-only — no dedicated sheet |
| TFPW-MK | **None** | ✅ TFPW_Z, TFPW_p, TFPW_slope, TFPW_sig, TFPW_trend | (Station,Scale) | ⚠️ S7-only — no dedicated sheet |
| Sen's Slope | S4 Sens Slope | ✅ Slopes only (no CIs) | (Station,Scale,Method) | ✅ Complete |
| ACF/Autocorr | Embedded in S1/S2/S3 | ✅ rho_1, Sig_AC | (Station,Scale) | ⚠️ No dedicated ACF sheet |
| Field Significance | S8 Field Significance | Partial (all_agree, n_sig_methods) | Scale | ✅ Walker+LC present |
| Pettitt CP | **NOT IN V4** | ❌ Absent | — | ❌ Missing from canonical pipeline |
| LOOCV | WB2 LOOCV.xlsx | ❌ Absent | (Scale,Variable) | ✅ Separate file |
| Descriptive Stats | S5 | ❌ Absent | Station | ⚠️ Annual only; no wet/dry breakdown |

### Required Fields for `Trend_Method_Comparison_Analysis`

**Source: S7 (all available)**

| Field Group | Columns | Source |
|-------------|---------|--------|
| Identity | Station, Code, Scale | S7 |
| Autocorrelation | rho_1, Sig_AC | S7 |
| MK full | MK_Z, MK_p, MK_slope, MK_sig, MK_trend | S7 |
| MMK full | MMK_Z, MMK_p, MMK_slope, MMK_sig, MMK_trend | S7 |
| PW full | PW_Z, PW_p, PW_slope, PW_sig, PW_trend | S7 |
| TFPW full | TFPW_Z, TFPW_p, TFPW_slope, TFPW_sig, TFPW_trend | S7 |
| Deltas | dZ_MMK, dZ_PW, dZ_TFPW, dSlope_MMK, dSlope_PW, dSlope_TFPW | S7 |
| Consensus | all_agree, n_sig_methods | S7 |

**Fields derivable but not stored (must compute):**

| Derived Field | Formula | Source data |
|---------------|---------|-------------|
| `sig_MK` (bool) | `abs(MK_Z) >= 1.960` | S7.MK_Z |
| `sig_MMK` (bool) | `abs(MMK_Z) >= 1.960` | S7.MMK_Z |
| `sig_PW` (bool) | `abs(PW_Z) >= 1.960` | S7.PW_Z |
| `sig_TFPW` (bool) | `abs(TFPW_Z) >= 1.960` | S7.TFPW_Z |
| `correction_factor` | `Var*(S) / Var(S)` = `n_eff` ratio | S2 (not in S7) |
| `n_eff` (MMK) | from S2 directly | S2 |
| `Var_adj` | from S2 directly | S2 |
| `agreement_mk_mmk` | `MK_trend == MMK_trend` | S7 |
| `agreement_all_4` | All 4 trends equal | S7 |
| `Z_spread` | max(Z_all) − min(Z_all) | S7 |
| `n_sig_01` | count of methods with `\|Z\| >= 2.576` | S7 |

**Fields missing from V4 canonical pipeline (need separate source):**

| Missing field | Available where? | Action |
|--------------|-----------------|--------|
| `Correction_Factor` explicit | WB4 `3_Modified_MK` or derivable from S2 | Compute from S2: `Var*(S)/Var(S)` |
| `n_eff` (effective sample size) | S2 `n_eff` column | Join from S2 |
| Pettitt change-point | WB4 `4_Pettitt_CP` only | Import from WB4 if needed |
| Per-scale descriptive stats | WB4 `1_Descriptive` (wet/dry) | Import from WB4 if needed |
| QC per-station summary | WB4 `QC_Report` | Import from WB4 if needed |

### Join Key Compatibility

| Sheet pair | Common key | Compatible? |
|-----------|-----------|-------------|
| S7 ↔ S1 | (Station, Scale) — same string values | ✅ |
| S7 ↔ S2 | (Station, Scale) — same string values | ✅ |
| S7 ↔ S3 | (Station, Scale) — same string values | ✅ |
| S7 ↔ S4 | (Station, Scale, Method) — need method filter | ⚠️ S4 has Method column |
| S7 ↔ S5 | Station only (S5 has no Scale) | ⚠️ Limited join |
| S7 ↔ S8 | Scale only (S8 has no Station) | ⚠️ Scale aggregate only |
| S7 ↔ WB4 | Station + mapped Scale | ⚠️ Scale must be remapped: `annual`→`Annual (Jan–Dec)` |

---

## Phase 3 — Table Mapping

### Manuscript Tables → Source Sheets

| Manuscript Table | Source Workbook | Source Sheet | Columns Used | Rows | Transformation |
|-----------------|----------------|-------------|-------------|------|---------------|
| Table 1: Descriptive Stats | WB1 | S5 | Station, Code, Mean, Std, CV(%), Wet-days/yr, Skewness | 12 | None — direct |
| Table 2: Autocorrelation | WB1 | S1 (rho_1), S2 (ρ₁), S7 (Sig_AC) | Station, Scale, rho_1, Sig_AC | 36 | Filter by scale |
| Table 3: MK Results | WB1 | S1 or S7 (MK_* cols) | Station, Scale, Z, p-value, Trend, * | 36 | Filter by scale |
| Table 4: MMK Results | WB1 | S2 or S7 (MMK_* cols) | Station, Scale, Z, p-value, n_eff, Trend | 36 | Filter by scale |
| Table 5: PW-MK Results | WB1 | **S7 only** | PW_Z, PW_p, PW_slope, PW_sig, PW_trend | 36 | Filter by scale |
| Table 6: TFPW-MK Results | WB1 | **S7 only** | TFPW_Z, TFPW_p, TFPW_slope, TFPW_sig, TFPW_trend | 36 | Filter by scale |
| Table 7: 4-Method Comparison | WB1 | S7 | All Z/p/slope/sig + dZ_* + all_agree | 36 | Wide format — no transform |
| Table 8: Sen's Slope | WB1 | S4 | β, CI_Lower, CI_Upper, Z, p-value, Method | 144 | Pivot by Method or filter |
| Table 9: Field Significance | WB1 | S8 | Scale, N_sig_MK, N_sig_MMK, Walker_p, LC_p | 3 | Scale label remap |
| Table 10: Research Summary | WB1 | S7 (derived) | n_sig_methods by scale | computed | Group-by Scale |
| Table 11: LOOCV Validation | WB2 | Sheet1 | Scale, Variable, RMSE, MAE, Bias, R2 | 15 | None — direct |

---

## Phase 4 — Gap Analysis

### What already exists in S7 (reusable as-is)

| Category | Status |
|----------|--------|
| All 4 method Z-statistics | ✅ Present: MK_Z, MMK_Z, PW_Z, TFPW_Z |
| All 4 method p-values | ✅ Present: MK_p, MMK_p, PW_p, TFPW_p |
| All 4 method slopes | ✅ Present: MK_slope, MMK_slope, PW_slope, TFPW_slope |
| All 4 significance flags (string) | ✅ Present: MK_sig, MMK_sig, PW_sig, TFPW_sig (`ns`/`*`/`**`) |
| All 4 trend direction strings | ✅ Present: MK_trend, MMK_trend, PW_trend, TFPW_trend |
| Z deltas (vs MK baseline) | ✅ Present: dZ_MMK, dZ_PW, dZ_TFPW |
| Slope deltas | ✅ Present: dSlope_MMK, dSlope_PW, dSlope_TFPW |
| Consensus flags | ✅ Present: all_agree, n_sig_methods |
| Autocorrelation | ✅ Present: rho_1, Sig_AC |

### What is missing and must be computed

| Gap | Source needed | Derivation |
|-----|--------------|-----------|
| Boolean sig flags | S7.MK_Z etc | `sig_bool = abs(Z) >= 1.960` |
| `correction_factor` | S2 | `Var*(S) / Var(S)` or direct S2 join |
| `n_eff` | S2.n_eff | Direct S2 join |
| Significance at α=0.01 separately | S7 Z cols | `abs(Z) >= 2.576` |
| Z_spread (method sensitivity) | S7 Z cols | `max(MK_Z,MMK_Z,PW_Z,TFPW_Z) − min(...)` |
| Direction consensus (bool) | S7 trend cols | 4-way string comparison |
| Method robustness score | S7 sig cols | count of `*`/`**` across 4 methods |
| Per-scale descriptive stats (wet/dry) | WB4 or recompute | Import from WB4 1_Descriptive |
| Pettitt change-point | WB4 4_Pettitt_CP | Import from WB4 |

### What must NOT be recomputed

- MK/MMK/PW/TFPW Z-statistics (exist in S7 — validated)
- Sen's slope values (exist in S4/S7)
- Field significance (exists in S8)
- Autocorrelation coefficients (embedded in S1/S2/S7)

### What can be reused directly (no transform)

- S7 entire DataFrame after `skiprows=[0,1]`
- S2 for n_eff and Var*(S) (join on Station, Scale)
- S8 for field significance (join on Scale)
- WB2 LOOCV.xlsx for interpolation validation

---

## Phase 5 — Implementation Plan

### Module: `rta/trend_method_comparison.py`

#### Files to create

```
rta/trend_method_comparison.py
```

#### Files NOT to modify

```
rta/excel_output.py          — existing output writer; untouched
rta_v5/                      — spatial pipeline; untouched
results/final_N33/excel/     — canonical results; NOT overwritten
```

#### Module architecture

```python
class TrendMethodComparison:
    """
    Load, join, and analyse 4-method comparison data from the validated
    V4 pipeline Results workbook.

    DATA SOURCE: S7 4-Method Comparison (primary)
                 S2 Modified MK (H&R98) (for n_eff, Var*(S))
                 S8 Field Significance (for Walker/LC tests)

    NO recomputation of MK/MMK/PW/TFPW statistics.
    """
    SCALE_MAP = {
        'annual': 'Annual (Jan–Dec)',
        'wet':    'Wet Season (May–Oct)',
        'dry':    'Dry Season (Nov–Apr)',
    }
    SIG_COLS_STR = ['MK_sig', 'MMK_sig', 'PW_sig', 'TFPW_sig']
    Z_COLS       = ['MK_Z', 'MMK_Z', 'PW_Z', 'TFPW_Z']
    P_COLS       = ['MK_p', 'MMK_p', 'PW_p', 'TFPW_p']
    SLOPE_COLS   = ['MK_slope', 'MMK_slope', 'PW_slope', 'TFPW_slope']
    TREND_COLS   = ['MK_trend', 'MMK_trend', 'PW_trend', 'TFPW_trend']
    DZ_COLS      = ['dZ_MMK', 'dZ_PW', 'dZ_TFPW']

    def __init__(self, excel_path: str | Path): ...
    # Loads S7, S2, S8 — merges on (Station, Scale)

    def load(self) -> pd.DataFrame: ...
    # Returns enriched df; caches as self.df

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame: ...
    # Adds: sig_bool_* · sig_01_* · Z_spread · direction_consensus
    #       · correction_factor · n_eff · robustness_score

    def summary_by_scale(self) -> pd.DataFrame: ...
    # Per-scale: N_sig per method at α=0.05 and α=0.01
    # n_all_agree, n_any_sig, n_none_sig
    # mean/max |dZ_MMK|, |dZ_PW|, |dZ_TFPW|
    # mean correction_factor, mean n_eff

    def agreement_matrix(self) -> pd.DataFrame: ...
    # Pairwise agreement rate (Station,Scale) pairs
    # Methods: MK/MMK, MK/PW, MK/TFPW, MMK/PW, MMK/TFPW, PW/TFPW

    def sensitivity_table(self) -> pd.DataFrame: ...
    # Per station: Z_spread (max-min across 4 methods)
    # Flags stations where method choice changes conclusion

    def field_significance_summary(self) -> pd.DataFrame: ...
    # Loads S8; returns Scale, Walker_p, LC_p, Walker_sig, LC_sig
    # Merged with N_sig counts from S7

    def to_excel(self, out_path: str | Path) -> None: ...
    # Writes: Sheet1=EnrichedData, Sheet2=Summary_by_Scale,
    #         Sheet3=Agreement_Matrix, Sheet4=Sensitivity,
    #         Sheet5=Field_Significance
```

#### Required joins

```
S7.load(skiprows=[0,1]) → base (Station str, Scale str, all 33 cols)
  LEFT JOIN S2.load(skiprows=[0,1])[Station, Scale, n_eff, Var*(S)]
  LEFT JOIN S8.load(skiprows=[0,1])[Scale, Walker_p_MK, LC_p_MK, ...]
             (remapped Scale: annual → Annual (Jan–Dec))
```

#### Expected outputs

| Output | Rows | Columns |
|--------|------|---------|
| EnrichedData | 36 | ~50 (S7 + derived) |
| Summary_by_Scale | 3 | ~20 |
| Agreement_Matrix | 3 (scales) | 7 (method pairs + scale) |
| Sensitivity | 36 | 8 |
| Field_Significance | 3 | 10 |

---

## Appendix — Scale Notation Mapping

| V4 Results (long form) | WB4 user-uploaded (short form) | V5 spatial pipeline |
|------------------------|-------------------------------|-------------------|
| `Annual (Jan–Dec)` | `annual` | `Annual (Jan–Dec)` |
| `Wet Season (May–Oct)` | `wet` | `Wet Season (May–Oct)` |
| `Dry Season (Nov–Apr)` | `dry` | `Dry Season (Nov–Apr)` |

## Appendix — `MK_sig` String Encoding

| String value | Meaning |
|-------------|---------|
| `'ns'` | Not significant (p ≥ 0.05) |
| `'*'` | Significant at α = 0.05 (|Z| ≥ 1.960) |
| `'**'` | Significant at α = 0.01 (|Z| ≥ 2.576) |

**Note:** `all_agree = 'Yes'` for all 36 rows in current dataset because PW/TFPW corrections are small enough not to change trend direction conclusions.
