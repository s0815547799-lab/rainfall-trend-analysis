# Discussion Template Validation
**Repository:** `s0815547799-lab/rainfall-trend-analysis`  
**Date:** 2026-05-29  
**Purpose:** H-3 remediation evidence — all placeholders resolved, all replacements traced to validated outputs

---

## Placeholders Resolved

### Placeholder 1 — `[max ρ₁]` in Discussion_Template.md

| Attribute | Value |
|---|---|
| File | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/Discussion_Template.md` |
| Original line | `with ρ₁ values up to [max ρ₁].` |
| Replacement value | `0.583` |
| Source workbook | `results/final_N33/excel/Output_TrendV4_..._Results.xlsx` |
| Source sheet | `S7 4-Method Comparison` |
| Source column | `rho_1` |
| Derivation | `max(abs(rho_1))` across all 36 station-scale rows |
| Verification | Station S3 (500003), Wet Season: ρ₁ = 0.5827 |
| Replaced with | `"0.583 (Station S3, Wet Season)"` — full context sentence |

### Placeholder 2 — `[Insert specific station names from Table M4.]` in Discussion_Template.md

| Attribute | Value |
|---|---|
| File | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/Discussion_Template.md` |
| Original line | `conclusion. [Insert specific station names from Table M4.]` |
| Source workbook | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Disagreement_Stations.xlsx` |
| Source CSV | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M4_Station_Disagreement_Inventory.csv` |
| Source sheet | `01_All_Disagreements` |

**Four station-scale combinations from Table M4:**

| Station | Scale | MK | MMK | PW-MK | TFPW-MK | Effect |
|---|---|---|---|---|---|---|
| S5 (500005) | Wet Season | Decreasing* | ns | ns | Decreasing* | MMK and PW-MK suppress significance |
| S6 (500006) | Wet Season | Decreasing* | ns | ns | Decreasing** | MMK and PW-MK suppress significance |
| S3 (500003) | Wet Season | ns | ns | ns | Decreasing* | TFPW-MK gains significance; others agree |
| S4 (500004) | Dry Season | Increasing* | Increasing* | ns | Increasing* | PW-MK alone suppresses significance |

**Replaced with:** Full narrative sentence identifying all four station-scale disagreements with direction and method context.

### Placeholder 3 — `[Insert Walker (1914) and Livezey-Chen (1983) results from Table M5.]` in Results_Template.md

| Attribute | Value |
|---|---|
| File | `results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/Results_Template.md` |
| Original line | `[Insert Walker (1914) and Livezey-Chen (1983) results from Table M5.]` |
| Source CSV | `results/final_N33_v5/Trend_Method_Comparison/Tables/Table_M5_Field_Significance_Comparison.csv` |
| Source workbook | `results/final_N33_v5/Trend_Method_Comparison/Excel/Master/Disagreement_Stations.xlsx` |
| Fixed seed | 42 (deterministic; confirmed in `rta/field_sig.py:124`) |

**Values from Table M5:**

| Scale | N sig / 12 | Walker p | Walker sig | LC-MC p | LC-MC sig |
|---|---|---|---|---|---|
| Annual | 1 | 0.4596 | No | 0.4364 | No |
| Wet Season | 2 | 0.1184 | No | 0.0991 | No |
| Dry Season | 3 | 0.0196 | **Yes*** | 0.0160 | **Yes*** |

**Replaced with:** Full narrative paragraph citing Walker and LC-MC p-values per scale, with field significance result for Dry Season confirmed by both tests.

---

## Additional Correction — Inconsistent CF Statement in Discussion_Template.md

In addition to the three `[bracket]` placeholders, the regenerated Discussion_Template.md contained the following incorrect statement inherited from the previous WB4-based run:

**Before (incorrect):**
> Given the modest correction factors observed (CF < 1.10 for all stations), the differences between methods are not severe.

**After H-2 fix, the correct CF range is 1.000 to 2.725.** This statement was updated to:
> Despite correction factors as large as 2.725 for strongly autocorrelated stations, the overall pattern of detected trends was robust.

**Source:** Master DB `Correction_Factor` column, sourced from S2 (Sheet: `S2 Modified MK (H&R98)`) of the primary v4 Results workbook. Range 1.0000–2.7251 (S3 Wet Season).

---

## Verification

```bash
grep -n "\[" results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/Discussion_Template.md
# Expected: no output (all brackets resolved)

grep -n "\[" results/final_N33_v5/Trend_Method_Comparison/Manuscript/Synthesis/Results_Template.md
# Expected: no output (all brackets resolved)
```

**Result:** Both commands return empty output. Zero unresolved placeholders confirmed.

---

## Related Fixes

| Fix | Issue | Resolution |
|---|---|---|
| H-2 | WB4 provenance gap for CF/n_eff | CF/n_eff now derived from S2 (WB1); CF range corrected from 1.000–1.098 to 1.000–2.725 |
| H-3 | Three bracket placeholders | All replaced with values from committed workbooks |
| H-3 additional | "CF < 1.10 for all stations" incorrect statement | Corrected to reflect actual CF range |

*No new calculations were performed. All replacement values read from committed, validated workbooks.*
