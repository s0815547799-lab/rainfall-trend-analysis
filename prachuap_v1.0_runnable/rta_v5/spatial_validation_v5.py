"""
rta_v5.spatial_validation_v5 — LOOCV runner and field-significance loader.

All validation metrics are computed here and returned as plain dicts / DataFrames
for use in the metadata writer and Excel export.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .spatial_interpolation_v5 import loocv, select_best


# ── Column specs for each temporal scale ─────────────────────────────────────
_SCALE_COLS = {
    "Annual (Jan–Dec)":    {
        "z_cols":  [("MK_Z", "MK_sig"), ("MMK_Z", "MMK_sig"),
                    ("PW_Z", "PW_sig"), ("TFPW_Z", "TFPW_sig")],
        "slope_col": "MK_slope",
        "slope_sig": "MK_sig",
    },
    "Wet Season (May–Oct)": {
        "z_cols":  [("MK_Z", "MK_sig"), ("MMK_Z", "MMK_sig"),
                    ("PW_Z", "PW_sig"), ("TFPW_Z", "TFPW_sig")],
        "slope_col": "MK_slope",
        "slope_sig": "MK_sig",
    },
    "Dry Season (Nov–Apr)": {
        "z_cols":  [("MK_Z", "MK_sig"), ("MMK_Z", "MMK_sig"),
                    ("PW_Z", "PW_sig"), ("TFPW_Z", "TFPW_sig")],
        "slope_col": "MK_slope",
        "slope_sig": "MK_sig",
    },
}


def run_loocv_all(
    comp4_df:  pd.DataFrame,
    coords_df: pd.DataFrame,
    scale_keys: list[str] | None = None,
) -> tuple[list[dict], dict[str, str], dict[str, dict]]:
    """
    Run LOOCV for all variables × temporal scales.

    Selects best interpolation method (IDW vs RBF) per scale using MMK_Z.

    Parameters
    ----------
    comp4_df  : 4-method comparison DataFrame (from S7 sheet)
    coords_df : stations DataFrame with columns station_id, lat, lon

    Returns
    -------
    loocv_rows   : list of row dicts (Scale, Variable, Method, RMSE, MAE, Bias, R2)
    best_methods : {scale_key: 'IDW'|'RBF'}
    all_metrics  : {scale_key: {method: {RMSE,MAE,Bias,R2}}}
    """
    if scale_keys is None:
        scale_keys = list(_SCALE_COLS.keys())

    cd = dict(zip(
        coords_df["station_id"].astype(str),
        zip(coords_df["lon"].astype(float), coords_df["lat"].astype(float)),
    ))

    rows: list[dict] = []
    best_methods: dict[str, str] = {}
    all_metrics:  dict[str, dict] = {}

    for scale in scale_keys:
        df = comp4_df[comp4_df["Scale"] == scale].copy()
        if df.empty:
            continue

        stns = df["Station"].astype(str).values
        lons = np.array([cd[s][0] for s in stns])
        lats = np.array([cd[s][1] for s in stns])
        pts  = np.column_stack([lons, lats])

        # ── Select best method on MMK_Z ───────────────────────────────────
        mmk_z = df["MMK_Z"].values.astype(float)
        ok    = ~np.isnan(mmk_z)
        if ok.sum() >= 4:
            from .spatial_interpolation_v5 import idw_interpolate
            import numpy as _np
            # Minimal grid for method selection
            _n  = 30
            _gl = _np.linspace(lons.min()-0.2, lons.max()+0.2, _n)
            _gt = _np.linspace(lats.min()-0.2, lats.max()+0.2, _n)
            _gl, _gt = _np.meshgrid(_gl, _gt)
            _xi = _np.column_stack([_gl.ravel(), _gt.ravel()])
            _, best, metrics = select_best(pts[ok], mmk_z[ok], _gl, _gt, _xi)
        else:
            best    = "IDW"
            metrics = {}

        best_methods[scale] = best
        all_metrics[scale]  = metrics
        print(f"    LOOCV — {scale}: best={best}")

        # ── Z variables ───────────────────────────────────────────────────
        spec = _SCALE_COLS.get(scale, {})
        for col, _ in spec.get("z_cols", []):
            v  = df[col].values.astype(float)
            ok = ~np.isnan(v)
            if ok.sum() >= 4:
                cv = loocv(pts[ok], v[ok], best)
            else:
                cv = {"RMSE": np.nan, "MAE": np.nan, "Bias": np.nan, "R2": np.nan}
            rows.append({"Scale": scale, "Variable": col,
                         "Method": best, **cv})

        # ── Slope ─────────────────────────────────────────────────────────
        sc = spec.get("slope_col", "MK_slope")
        sv = df[sc].values.astype(float)
        ok = ~np.isnan(sv)
        if ok.sum() >= 4:
            cv_s = loocv(pts[ok], sv[ok], best)
        else:
            cv_s = {"RMSE": np.nan, "MAE": np.nan, "Bias": np.nan, "R2": np.nan}
        rows.append({"Scale": scale, "Variable": "Sen_Slope",
                     "Method": best, **cv_s})

    return rows, best_methods, all_metrics


def load_field_sig(excel_path: str) -> pd.DataFrame | None:
    """
    Load field significance table from S8 sheet of Results.xlsx.

    Returns a tidy DataFrame or None if the sheet is absent.
    """
    try:
        df = pd.read_excel(excel_path, sheet_name="S8 Field Significance",
                           header=1, skiprows=[0])
        return df[df["Scale"].notna()].copy()
    except Exception:
        return None


def format_loocv_table(loocv_rows: list[dict]) -> pd.DataFrame:
    """Convert LOOCV row list to a sorted DataFrame."""
    df = pd.DataFrame(loocv_rows)
    order = {"Annual (Jan–Dec)": 0,
             "Wet Season (May–Oct)": 1,
             "Dry Season (Nov–Apr)": 2}
    if "Scale" in df.columns:
        df["_order"] = df["Scale"].map(order).fillna(9)
        df = df.sort_values(["_order", "Variable"]).drop(columns="_order")
    return df.reset_index(drop=True)
