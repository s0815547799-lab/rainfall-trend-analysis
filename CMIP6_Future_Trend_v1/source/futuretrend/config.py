"""
cmip6_trend.config — Scalar constants and season definitions.

Reused after audit from rainfall-trend-analysis (frozen baseline), rta/config.py.
ONLY audit-passed scalar constants and season definitions are carried over.
Excel stylers, colour palette, and matplotlib publication style from the
baseline are NOT reused here (out of Module-0 scope; added later only if a
later module requires them).
"""

# Wet-day threshold (WMO)
WET_THR = 1.0                       # mm/day

# Season definitions (LOCKED — Directive). Water Year = May(Y) -> Apr(Y+1).
WET_MONTHS = [5, 6, 7, 8, 9, 10]    # Rainy season: May-October
DRY_MONTHS = [11, 12, 1, 2, 3, 4]   # Dry season:   November-April
WATER_YEAR_START_MONTH = 5          # Water year begins in May

# Mann-Kendall test constants
MIN_N     = 10                      # minimum years for MK test
ALPHA_005 = 0.05
ALPHA_001 = 0.01
Z_005     = 1.9600
Z_001     = 2.5758

# Missing-value flags
MISS_FLAGS = [-99, -999, -9999, -9.99e+20, 9.99e+20, 1e+20]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  ETCCDI constants (this framework)                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# Wet-day threshold for percentile indices (ETCCDI standard)
ETCCDI_WET_THR = 1.0          # mm/day

# Percentile baseline period (LOCKED — directive): freeze thresholds on 1981-2010
PERCENTILE_BASELINE = (1981, 2010)

# Frequency-index fixed thresholds (mm/day)
FREQ_THRESHOLDS = {"R10mm": 10.0, "R20mm": 20.0, "R50mm": 50.0}

# ETCCDI core indices (Phase 1).
# Main analysis uses RxxpTOT (precip totals); RxxpDays are a supplement.
ETCCDI_INDICES = [
    "Rx1day", "Rx5day",            # absolute intensity
    "R10mm", "R20mm", "R50mm",     # frequency
    "CDD", "CWD",                  # duration
    "SDII",                        # intensity
    "R95pTOT", "R99pTOT",          # percentile totals (mm) — MAIN
    "R95pDays", "R99pDays",        # percentile day counts — SUPPLEMENT
]

# Indices used for the full map system (all core indices)
MAP_INDICES_FULL = [
    "Rx1day", "Rx5day", "R10mm", "R20mm", "R50mm",
    "CDD", "CWD", "SDII", "R95pTOT", "R99pTOT",
]

# Optional seasonal subset (regional supplement)
SEASONAL_INDICES = ["Rx1day", "Rx5day", "CDD", "R95pTOT", "R99pTOT"]
