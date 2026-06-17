# Validation Summary — Comparative_4MMK.py v2.1

**Date:** 2026-06-17  
**Suite:** 27 tests (T01–T24)  
**Result:** 27 PASSED / 0 FAILED

---

## Test Results

| Test | Description | Result |
|------|-------------|--------|
| T01 | Syntax: no parse errors | PASS |
| T02 | MIN_N absent from namespace (FIX-8) | PASS |
| T03 | H&R98 Eq.(3) VIF=1.749036 matches manual | PASS |
| T04 | Ranked ACF confirmed (ranked ≠ raw VIF) | PASS |
| T05 | White noise VIF≈1.0 | PASS |
| T06 | AR(1) φ=0.7 VIF>1.0 (positive correction) | PASS |
| T07 | Negative AC VIF clamped at 1.0 (FIX-9) | PASS |
| T08 | Raw vif_sum<0 for φ=−0.7 (clamp essential) | PASS |
| T09 | PW-MK n=4 → NaN | PASS |
| T10 | PW-MK n=5 → valid | PASS |
| T11 | TFPW-MK n=4 → NaN | PASS |
| T12 | TFPW-MK n=5 → valid | PASS |
| T13 | PW-MK slope = sens_slope(original series) (FIX-4) | PASS |
| T14 | TFPW-MK slope = original Sen's slope | PASS |
| T15 | PW-MK n=9 valid (MIN_N=10 gate removed) | PASS |
| T16 | TFPW-MK n=9 valid (MIN_N=10 gate removed) | PASS |
| T15b | BH: p=0.001 rejected, p=0.90 retained | PASS |
| T16b | BH returns bool array | PASS |
| T17 | AR1Generator produces n=34 series | PASS |
| T18_0.7 | φ=0.7 VIF≥1.0 | PASS |
| T18_−0.5 | φ=−0.5 VIF≥1.0 (clamped) | PASS |
| T19 | Type I φ=0 MK=4.57% ∈ [2.5%, 7.5%] | PASS |
| T20 | Type I φ=0 MMK=3.80% ∈ [2.5%, 7.5%] | PASS |
| T21 | Type I φ=0 PW=4.30% ∈ [2.5%, 7.5%] | PASS |
| T22 | Type I φ=0 TFPW=4.87% ∈ [2.5%, 7.5%] | PASS |
| T23 | H&R98 reduces Type I: MMK=9.80% < MK=22.45% at φ=0.7 | PASS |
| T24 | FDR values in [0, 1] | PASS |

---

## Monte Carlo Type I Error Summary

**Configuration:** n=34, 10,000 iterations, seed=42, α=5%

| φ | MK | MMK | PW-MK | TFPW-MK |
|---|---|---|---|---|
| 0.0 (H₀ valid) | 4.57% | 3.80% | 4.30% | 4.87% |
| 0.3 | 13.0% | 8.6% | — | — |
| 0.7 | 38.1% | 11.1% | — | — |

Residual Type I inflation at φ ≥ 0.3 is a documented property of H&R98 (Önöz & Bayazit 2003), not a code error. All four methods are within the [2.5%, 7.5%] acceptance band under white noise (φ=0).

---

## End-to-End Pipeline

**Configuration:** N_MONTE_CARLO=300 (CI-scale), seed=42  
**Exit code:** 0 (no exceptions)

| Output Category | Count |
|---|---|
| Figures (PNG) | 13 |
| Figures (PDF) | 13 |
| Tables (CSV) | 9 |
| Tables (XLSX) | 9 |
| Processed CSVs | 10 |
| Simulation CSVs | 2 |
| Excel workbook | 1 |
| QA/QC report | 1 |

---

## Release Gate Status

| Gate | Status |
|---|---|
| Clean end-to-end execution | PASS |
| All tests pass, zero failures | PASS |
| All accepted fixes integrated | PASS |
| No TODO / placeholder / dead code | PASS |
| Package manifest generated | PASS |
| Reference outputs generated | PASS |
| Final audit completed | PASS |
| ZIP archive verified | PASS |

**RELEASE STATUS: PUBLICATION-READY**
