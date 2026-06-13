"""
Runner: generate Trend_Method_Comparison_Q1.xlsx

Sources
-------
WB1  results/final_N33/excel/*_Results.xlsx   (canonical V4 pipeline output)
WB4  supplementary workbook: Pettitt CP, significant-lag columns
     Resolved in order:
       1. WB4_PATH environment variable (export WB4_PATH=/path/to/file.xlsx)
       2. data/reference/ebc6aee6-Rainfall_2Trend_Results.xlsx (repo-relative)
     If neither exists, affected columns are omitted (NaN) and execution continues.
"""
import os
import sys
from pathlib import Path

# Allow running from any working directory
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from rta.trend_method_comparison import TrendMethodComparison

WB1_GLOB = "results/final_N33/excel/*_Results.xlsx"

# WB4: resolve via env var first, then repo-relative fallback
_WB4_ENV     = os.environ.get("WB4_PATH")
_WB4_DEFAULT = ROOT / "data" / "reference" / "ebc6aee6-Rainfall_2Trend_Results.xlsx"
WB4_PATH     = Path(_WB4_ENV) if _WB4_ENV else _WB4_DEFAULT

OUT_PATH = ROOT / "results" / "final_N33_v5" / "Trend_Method_Comparison_Q1.xlsx"


def main() -> None:
    matches = sorted((ROOT / "results" / "final_N33" / "excel").glob("*_Results.xlsx"))
    if not matches:
        raise FileNotFoundError(f"No WB1 found matching {WB1_GLOB}")
    wb1 = matches[0]
    print(f"WB1 : {wb1}")

    wb4 = WB4_PATH if WB4_PATH.exists() else None
    if wb4 is None:
        print("WB4 : NOT FOUND — Pettitt CP and significant-lag columns will be omitted")
    else:
        print(f"WB4 : {wb4}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"OUT : {OUT_PATH}")

    tmc = TrendMethodComparison(wb1_path=wb1, wb4_path=wb4)
    tmc.write_workbook(OUT_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
