# Rainfall Trend Analysis v1.0 — Release Package

**Repository:** `s0815547799-lab/rainfall-trend-analysis`  
**Release:** v1.0.0  
**Commit:** `ede43b2f199a702ba56312ef8f5a533cf9c402ee`  
**Release date:** 2026-05-29  
**Status:** APPROVED FOR JOURNAL SUBMISSION

---

## What is This Release?

This is the archival release package for the publication-ready hydroclimatological trend analysis of daily rainfall data from the Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand (1981–2014).

**Scientific scope:** 12 rain-gauge stations, 34-year record, four Mann-Kendall-based trend methods (MK, MMK, PW-MK, TFPW-MK), Sen's slope, field significance (Walker + Livezey-Chen), geographic spatial analysis.

---

## Repository Structure

```
code/            Pipeline scripts and rta/ package (symlinked to repo root)
data/            Raw input files (symlinked to repo root)
results/         Published results (symlinked to results/)
figures/         Archived publication figures (symlinked to results/archive_figures/)
docs/            Audit and certification documents (symlinked to repo root)
```

---

## Quick Reproduction

```bash
# 1. Clone
git clone https://github.com/s0815547799-lab/rainfall-trend-analysis.git
cd rainfall-trend-analysis
git checkout ede43b2f199a702ba56312ef8f5a533cf9c402ee

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run primary pipeline
python3 rainfall_trend_analysis_v4.py . --no-resume

# 4. Run trend comparison analysis
python3 generate_trend_comparison_analysis.py

# Outputs are written to the same directory as the input CSV.
```

---

## Verified Results (v1.0)

| Method | Significant trends (p<0.05, 36 tests) |
|---|---|
| Standard MK | 6 |
| Modified MK (H&R98) | 4 |
| PW-MK (Yue & Wang 2004) | 3 |
| TFPW-MK (Yue et al. 2002) | 7 |

| Scale | Field significance (Dry Season) |
|---|---|
| Annual | Not significant (Walker p=0.460, LC-MC p=0.436) |
| Wet Season | Not significant (Walker p=0.118, LC-MC p=0.099) |
| Dry Season | **Significant** (Walker p=0.020, LC-MC p=0.016) |

Max correction factor: **2.725** (S3 Wet Season, n_eff=12.48 years)

---

## Audit Trail

| Document | Purpose |
|---|---|
| `RELEASE_CERTIFICATION_v1.0.md` | Final release decision and readiness scores |
| `FINAL_RELEASE_AUDIT.md` | Post-remediation audit (0 blocking, 0 high issues) |
| `REPRODUCIBILITY_FINAL_CHECK.md` | Clean-environment pipeline verification |
| `RELEASE_READINESS_REPORT.md` | Pre-remediation issue identification |
| `REPRODUCIBILITY_AUDIT.md` | Full reproducibility audit |
| `PIPELINE_VALIDATION_REPORT.md` | End-to-end validation |
| `DATA_DICTIONARY.md` | Field-level documentation for all outputs |
| `FIGURE_INVENTORY.md` | Figure archive inventory |
| `TECHNICAL_DEBT_REGISTER.md` | Classified open issues |
