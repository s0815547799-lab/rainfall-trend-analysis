"""
Runner: generate Trend Method Comparison Analysis outputs.

Produces:
  results/final_N33_v5/Trend_Method_Comparison/
    Excel/Master/           Trend_Method_Comparison_Master.xlsx
                            Trend_Method_Comparison_Tables.xlsx
    Excel/MK_Analysis/      MK_Analysis.xlsx
    Excel/MMK_Analysis/     MMK_Analysis.xlsx  +  MMK_vs_MK_Comparison.xlsx
    Excel/PW_MK_Analysis/   PW_MK_Analysis.xlsx  +  PW_MK_vs_MK_Comparison.xlsx
    Excel/TFPW_MK_Analysis/ TFPW_MK_Analysis.xlsx + TFPW_MK_vs_MK_Comparison.xlsx
    Tables/                 7 × (.xlsx + .csv)
    Figures/                10 × (.png + .tiff + .pdf + .svg)
    Manuscript/             9 × .md templates
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from rta.trend_comparison_analysis import TrendComparisonAnalysis

WB1_DIR = ROOT / "results" / "final_N33" / "excel"
WB4_PATH = Path(
    "/root/.claude/uploads/ac030f2a-04ee-4515-ae9b-e04aa5a4cfb7"
    "/ebc6aee6-Rainfall_2Trend_Results.xlsx"
)
OUT_DIR = ROOT / "results" / "final_N33_v5"


def main() -> None:
    matches = sorted(WB1_DIR.glob("*_Results.xlsx"))
    if not matches:
        raise FileNotFoundError(f"No WB1 found in {WB1_DIR}")
    wb1 = matches[0]
    print(f"WB1 : {wb1}")

    wb4 = WB4_PATH if WB4_PATH.exists() else None
    if wb4 is None:
        print("WB4 : NOT FOUND — n_eff / CF / Lag columns will be NaN")
    else:
        print(f"WB4 : {wb4}")

    print(f"OUT : {OUT_DIR / 'Trend_Method_Comparison'}")

    tca = TrendComparisonAnalysis(wb1_path=wb1, wb4_path=wb4, out_dir=OUT_DIR)
    tca.run_all()


if __name__ == "__main__":
    main()
