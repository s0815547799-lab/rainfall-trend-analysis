"""
rta_v5.spatial_export_v5 — Multi-format figure export and documentation writer.

Functions
---------
save_formats()            : save PNG / TIFF / PDF / SVG at publication DPI
write_fig_metadata()      : Fig_Metadata_Q1.txt  (RMSE, MAE, LOOCV, classification)
write_boundary_config()   : Boundary_Config_v5.md
write_spatial_methods()   : Spatial_Methods_Q1_v5.md
write_validation_excel()  : LOOCV.xlsx + Interpolation_Comparison.xlsx
"""

from __future__ import annotations

import textwrap
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Figure export                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def save_formats(fig, out_dir: Path, stem: str, dpi: int = 600) -> list[Path]:
    """
    Save figure in PNG, TIFF (LZW), PDF, and SVG formats.

    Returns list of written paths.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    formats = [
        ("png", {"dpi": dpi}),
        ("tif", {"dpi": dpi, "pil_kwargs": {"compression": "tiff_lzw"}}),
        ("pdf", {"dpi": dpi}),
        ("svg", {}),
    ]
    for fmt, kw in formats:
        p = out_dir / f"{stem}.{fmt}"
        try:
            fig.savefig(p, format=fmt, bbox_inches="tight", **kw)
            print(f"    ✓ {p.name}")
            written.append(p)
        except Exception as exc:
            warnings.warn(f"Save failed ({fmt}): {exc}")
    return written


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Fig_Metadata_Q1.txt                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def write_fig_metadata(
    out_dir:     Path,
    stem:        str,
    loocv_rows:  list[dict],
    best_methods: dict[str, str],
    all_metrics:  dict[str, dict],
    field_sig_df: "pd.DataFrame | None",
    n_stations:  int,
    n_polygons:  int,
    period:      str,
    grid_n:      int,
    z_vabs:      float,
) -> Path:
    """Write Fig_Metadata_Q1.txt alongside the figure files."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "Fig_Metadata_Q1.txt"

    def _f(v):
        try:
            return f"{float(v):.4f}" if v is not None and not np.isnan(float(v)) else "n/a"
        except Exception:
            return "n/a"

    lines = [
        "=" * 70,
        "  SPATIAL TREND ANALYSIS — Q1 PUBLICATION METADATA",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 70,
        "",
        "BOUNDARY",
        f"  Source  : boundaries/current_boundary/boundary.shp",
        f"  Polygons: {n_polygons}",
        f"  Stations: {n_stations}",
        f"  Period  : {period}",
        "",
        "INTERPOLATION METHOD  (selected per scale by LOOCV RMSE: IDW vs RBF)",
    ]
    for scale, bm in best_methods.items():
        lines.append(f"  {scale:<30}: {bm}")

    lines += ["", "IDW vs RBF COMPARISON  (reference variable: MMK_Z, annual)"]
    ann_metrics = all_metrics.get("Annual (Jan–Dec)", {})
    for mname, mets in ann_metrics.items():
        lines.append(
            f"  {mname:<6}: RMSE={_f(mets.get('RMSE'))}  "
            f"MAE={_f(mets.get('MAE'))}  "
            f"Bias={_f(mets.get('Bias'))}  "
            f"R²={_f(mets.get('R2'))}"
        )

    lines += ["", "LOOCV METRICS  (Leave-One-Out Cross-Validation)",
              f"  {'Scale':<30} {'Variable':<12} {'Method':<5} {'RMSE':>7} {'MAE':>7} {'Bias':>8} {'R²':>7}",
              "  " + "-" * 64]
    for r in loocv_rows:
        lines.append(
            f"  {r.get('Scale',''):<30} {r.get('Variable',''):<12} "
            f"{r.get('Method',''):<5} "
            f"{_f(r.get('RMSE')):>7} {_f(r.get('MAE')):>7} "
            f"{_f(r.get('Bias')):>8} {_f(r.get('R2')):>7}"
        )

    lines += ["", "FIELD SIGNIFICANCE  (Walker 1914 + Livezey-Chen MC)"]
    if field_sig_df is not None and not field_sig_df.empty:
        for _, row in field_sig_df.iterrows():
            sc = row.get("Scale", "?")
            ns = row.get("N_sig_MMK", row.get("N_sig_MK", "?"))
            nt = row.get("N_stations", "?")
            wp = row.get("Walker_p_MK", "?")
            lp = row.get("LC_p_MK", "?")
            lines.append(
                f"  {sc:<30}: N_sig={ns}/{nt}  "
                f"Walker_p={_f(wp)}  LC_p={_f(lp)}"
            )
    else:
        lines.append("  (not available)")

    lines += [
        "",
        "FIGURE DESIGN",
        f"  Layout      : 5-panel (2+2+1, panel (e) exactly centred)",
        f"  Colormap Z  : RdBu_r,  vmin={-z_vabs:.1f},  vmax={+z_vabs:.1f}",
        f"  Colormap S  : RdYlGn,  symmetric ±max(|slope|)",
        f"  DPI         : 600",
        f"  Formats     : PNG, TIFF (LZW), PDF, SVG",
        f"  Font        : Times New Roman / DejaVu Serif (serif)",
        f"  Grid        : {grid_n}×{grid_n}",
        "",
        "STATION CLASSIFICATION  (shown in figure caption, not in figure body)",
        "  ▲ green  — Increasing,  p < 0.05",
        "  ▼ red    — Decreasing,  p < 0.05",
        "  ● grey   — Not significant",
        "",
        "=" * 70,
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"    ✓ {path.name}")
    return path


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Boundary_Config_v5.md                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def write_boundary_config(out_dir: Path) -> Path:
    """Write Boundary_Config_v5.md — province-replacement workflow guide."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "Boundary_Config_v5.md"

    text = textwrap.dedent("""\
    # Boundary Configuration Guide — v5 Province-Independent System

    ## Overview

    The v5 spatial mapping system is **province-independent**. No province
    names, codes, or file paths appear inside any source file. The boundary
    is loaded from a single canonical directory:

    ```
    boundaries/current_boundary/
    ├── boundary.shp
    ├── boundary.dbf
    ├── boundary.shx
    └── boundary.prj
    ```

    ## Changing the Study Area

    To map a different province or region:

    1. Obtain a polygon shapefile for the new area (WGS84 / EPSG:4326).
    2. Rename the four companion files:
       ```
       <any_name>.shp  →  boundary.shp
       <any_name>.dbf  →  boundary.dbf
       <any_name>.shx  →  boundary.shx
       <any_name>.prj  →  boundary.prj
       ```
    3. Replace the existing files in `boundaries/current_boundary/`.
    4. Re-run `rainfall_trend_analysis_v5.py` — **no code edits required**.

    ## Validation

    The system validates boundary files at startup via
    `rta_v5.spatial_interpolation_v5.validate_boundary()`:

    - All four files must be present.
    - The shapefile must contain at least one polygon with ≥ 3 vertices.
    - If any check fails, the script stops with a descriptive error message.

    ## Current Configuration

    | Item | Value |
    |------|-------|
    | Boundary directory | `boundaries/current_boundary/` |
    | Required files | boundary.shp / .dbf / .shx / .prj |
    | Coordinate system | WGS84 (EPSG:4326) assumed |

    ## Notes

    - The map extent is computed automatically from the shapefile bounding box
      plus a configurable padding (`PAD = 0.18°`).
    - The boundary mask clips the interpolated surface to the polygon interior.
    - For multi-polygon shapefiles (e.g., multiple districts), all polygons
      are unioned for masking; each is drawn individually as a district outline.
    """)

    path.write_text(text, encoding="utf-8")
    print(f"    ✓ {path.name}")
    return path


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Spatial_Methods_Q1_v5.md                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def write_spatial_methods(
    out_dir:      Path,
    loocv_rows:   list[dict],
    best_methods: dict[str, str],
    all_metrics:  dict[str, dict],
    period:       str,
    n_stations:   int,
    scale_key:    str = "Annual (Jan–Dec)",
) -> Path:
    """Write Spatial_Methods_Q1_v5.md — manuscript methods section."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "Spatial_Methods_Q1_v5.md"

    def _f(v):
        try:
            return f"{float(v):.4f}" if v is not None and not np.isnan(float(v)) else "n/a"
        except Exception:
            return "n/a"

    best = best_methods.get(scale_key, "IDW")
    ann_metrics = all_metrics.get(scale_key, {})

    loocv_ann = [r for r in loocv_rows if r.get("Scale") == scale_key]

    lines = [
        "# Spatial Interpolation Methods — Q1 Publication (v5)",
        "",
        f"**Period:** {period}  |  **Stations:** {n_stations}",
        "",
        "## 2.5  Spatial Interpolation",
        "",
        "Spatially continuous trend fields were estimated by interpolating "
        "station-level Mann–Kendall Z statistics and Sen's slope values onto a "
        f"{120}×{120} regular grid covering the province extent. "
        "Province masking was applied using the official administrative boundary "
        "shapefile (polygon type, WGS84). "
        "Two deterministic interpolation methods were evaluated:",
        "",
        "**Inverse-Distance Weighting (IDW, power = 2)** assigns weights "
        "proportional to the reciprocal squared distance from each query point "
        "to the data stations (Shepard, 1968).",
        "",
        "**Radial-Basis Function (RBF, thin-plate spline, smoothing = 0.5)** "
        "fits a kernel-based interpolant using `scipy.interpolate.RBFInterpolator`; "
        "the thin-plate spline kernel minimises the integrated squared second "
        "derivative (Wahba, 1990).",
        "",
        "Method selection employed Leave-One-Out Cross-Validation (LOOCV) "
        "applied to Modified MK Z statistics. "
        "At each fold, one station is withheld, the surface is refitted on "
        "the remaining n−1 stations, and the withheld value is predicted. "
        "The method with the lower root-mean-square error (RMSE) is applied "
        "to all variables for that temporal scale.",
        "",
        "### Selected Methods",
        "",
        "| Scale | Method |",
        "|-------|--------|",
    ]
    for sc, bm in best_methods.items():
        lines.append(f"| {sc} | {bm} |")

    lines += [
        "",
        "### LOOCV Results — Annual Scale",
        "",
        "| Variable | Method | RMSE | MAE | Bias | R² |",
        "|----------|--------|------|-----|------|-----|",
    ]
    for r in loocv_ann:
        lines.append(
            f"| {r.get('Variable','?')} | {r.get('Method','?')} | "
            f"{_f(r.get('RMSE'))} | {_f(r.get('MAE'))} | "
            f"{_f(r.get('Bias'))} | {_f(r.get('R2'))} |"
        )

    lines += [
        "",
        "### IDW vs RBF Comparison (reference: MMK_Z, Annual)",
        "",
        "| Method | RMSE | MAE | Bias | R² |",
        "|--------|------|-----|------|-----|",
    ]
    for mname, mets in ann_metrics.items():
        lines.append(
            f"| {mname} | {_f(mets.get('RMSE'))} | {_f(mets.get('MAE'))} | "
            f"{_f(mets.get('Bias'))} | {_f(mets.get('R2'))} |"
        )

    lines += [
        "",
        "## References",
        "",
        "- Shepard, D. (1968). A two-dimensional interpolation function for "
        "irregularly-spaced data. *Proc. 23rd ACM National Conference*, 517–524.",
        "- Wahba, G. (1990). *Spline Models for Observational Data*. "
        "SIAM, Philadelphia.",
        "- Mann, H.B. (1945). Nonparametric tests against trend. "
        "*Econometrica*, 13, 245–259.",
        "- Kendall, M.G. (1975). *Rank Correlation Methods* (4th ed.). Griffin.",
        "- Hamed, K.H. & Rao, A.R. (1998). A modified Mann–Kendall trend test "
        "for autocorrelated data. *Journal of Hydrology*, 204, 182–196.",
        "- Sen, P.K. (1968). Estimates of the regression coefficient based on "
        "Kendall's tau. *JASA*, 63, 1379–1389.",
        "",
        "---",
        "*Auto-generated by rta_v5.spatial_export_v5 from results/final_N33/ archive.*",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"    ✓ {path.name}")
    return path


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Validation Excel export                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def write_validation_excel(
    loocv_rows:  list[dict],
    all_metrics: dict[str, dict],
    out_dir:     Path,
) -> None:
    """Write LOOCV.xlsx and Interpolation_Comparison.xlsx to out_dir/validation/."""
    val_dir = Path(out_dir) / "validation"
    val_dir.mkdir(parents=True, exist_ok=True)

    # LOOCV.xlsx
    df_loocv = pd.DataFrame(loocv_rows)
    p1 = val_dir / "LOOCV.xlsx"
    df_loocv.to_excel(p1, index=False)
    print(f"    ✓ {p1.name}")

    # Interpolation_Comparison.xlsx (annual IDW vs RBF)
    ann = all_metrics.get("Annual (Jan–Dec)", {})
    if ann:
        rows = [{"Method": m, **met} for m, met in ann.items()]
        df_cmp = pd.DataFrame(rows).set_index("Method")
        p2 = val_dir / "Interpolation_Comparison.xlsx"
        df_cmp.to_excel(p2)
        print(f"    ✓ {p2.name}")
