# CMIP6 MME Rainfall Projection Framework v1.0 — FINAL RELEASE

Projected Near-Future Changes in Annual and Seasonal Rainfall in Prachuap Khiri
Khan Province, Thailand, Using Bias-Corrected CMIP6 Multi-Model Ensembles.

Reference run (QC PASS): RELEASE_20260531_051742

## Run
pip install -r requirements.txt
python final_run.py     # writes outputs/RELEASE_<timestamp>/ + CURRENT_RELEASE

## Figures (station-based, Q1)
F1 Taylor (corr + normalized SD) · F2 validation Cleveland (KGE/NSE/PBIAS) ·
F3 anomaly time series (continuous 1981-2050, SSP bold, spread alpha 0.12) ·
F4-6 station value maps (Annual/Wet/Dry) · F7 proportional-symbol change maps
(size proportional to |DeltaP%|). All single+double column × PNG/TIFF/PDF, 600 dpi.
Central add_panel_label() — uniform (a)(b)(c) across all figures.

## Results (3-level)
station_model/ · station_mme/ · area_summary/ · publication_tables/ (Table_01-05+S1,S2).

## Guardrails
MME = summary not member (n=7); Observed = ground truth; BC primary; station-based
(no IDW surface — honest for ~12 stations); config-driven & portable; association only.
