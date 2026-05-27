"""
rta.spatial_interpolation — Spatial interpolation and LOOCV validation.

Methods implemented:
  IDW  — Inverse-Distance Weighting (power=2)
  RBF  — Radial-Basis Function via scipy.interpolate.RBFInterpolator
            (thin_plate_spline kernel, moderate smoothing)

Kriging is not included: pykrige is not installed in this environment.

Entry points
------------
build_grid(lons, lats)           → grid_lon, grid_lat, xi
load_boundary(folder, coords)    → list of (N,2) polygon arrays  [lon,lat]
make_boundary_mask(gl, gt, poly) → boolean mask array
idw_interpolate(pts, vals, xi)   → 1-D result array
rbf_interpolate(pts, vals, xi)   → 1-D result array
loocv(pts, vals, method)         → {RMSE, MAE, Bias, R2}
select_best(pts, vals, gl, gt, xi) → zz, method_name, all_metrics_dict
save_validation_tables(metrics, detail, out_dir)
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import RBFInterpolator
from scipy.spatial import ConvexHull

# ── module-level defaults ─────────────────────────────────────────────────────
GRID_N  = 90       # NxN interpolation grid
BUFFER  = 0.10     # degrees of padding around station extent for grid/hull


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1  Grid                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def build_grid(lons: np.ndarray, lats: np.ndarray,
               n: int = GRID_N) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Regular lon/lat grid padded by BUFFER around the station extent.

    Returns
    -------
    grid_lon, grid_lat : (n, n) meshgrids
    xi                 : (n*n, 2) query points [lon, lat]
    """
    gl = np.linspace(lons.min() - BUFFER, lons.max() + BUFFER, n)
    gt = np.linspace(lats.min() - BUFFER, lats.max() + BUFFER, n)
    grid_lon, grid_lat = np.meshgrid(gl, gt)
    xi = np.column_stack([grid_lon.ravel(), grid_lat.ravel()])
    return grid_lon, grid_lat, xi


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §2  Boundary polygon                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def load_boundary(folder: str | Path,
                  station_lons: np.ndarray | None = None,
                  station_lats: np.ndarray | None = None,
                  expand: float = 0.18) -> list[np.ndarray]:
    """
    Try to load a shapefile boundary from folder; fall back to a
    convex-hull polygon around the supplied station coordinates.

    Parameters
    ----------
    folder       : directory to search for *.shp
    station_lons : 1-D lon array of the analysis stations
    station_lats : 1-D lat array of the analysis stations
    expand       : fractional hull expansion for the fallback polygon

    Returns
    -------
    list of closed (N, 2) arrays  [lon, lat columns]
    """
    folder = Path(folder)
    shp_files = sorted(folder.glob("*.shp"))

    if shp_files:
        try:
            import shapefile as sf_lib
            reader = sf_lib.Reader(str(shp_files[0]))
            polys = []
            for shape in reader.shapes():
                pts = np.array(shape.points)
                if len(pts) >= 3:
                    polys.append(pts)
            if polys:
                print(f"    ✓ Boundary: loaded {shp_files[0].name} "
                      f"({len(polys)} polygon(s))")
                return polys
        except Exception as exc:
            warnings.warn(f"Shapefile load failed ({exc}); using convex-hull fallback.")

    # ── Fallback: convex hull of station coordinates ──────────────────────
    if station_lons is not None and station_lats is not None and len(station_lons) >= 3:
        pts = np.column_stack([station_lons, station_lats])
        try:
            hull  = ConvexHull(pts)
            verts = pts[hull.vertices]
            # Expand radially from centroid
            centroid = verts.mean(0)
            expanded = centroid + (verts - centroid) * (1.0 + expand)
            # Close the polygon
            poly = np.vstack([expanded, expanded[[0]]])
            print(f"    ↳ Boundary: convex-hull fallback ({len(verts)} vertices, "
                  f"expand={expand:.0%})")
            return [poly]
        except Exception as exc:
            warnings.warn(f"ConvexHull failed ({exc}); using bounding box.")

    # ── Last resort: bounding box ─────────────────────────────────────────
    if station_lons is not None:
        m  = BUFFER
        lo, hi = station_lons.min() - m, station_lons.max() + m
        bo, to = station_lats.min() - m, station_lats.max() + m
        box = np.array([[lo, bo], [hi, bo], [hi, to], [lo, to], [lo, bo]])
        return [box]
    return []


def make_boundary_mask(grid_lon: np.ndarray, grid_lat: np.ndarray,
                       polys: list[np.ndarray]) -> np.ndarray:
    """
    Boolean mask: True for grid cells inside any polygon.
    Uses matplotlib.path for point-in-polygon.
    """
    from matplotlib.path import Path as MPath
    mask = np.zeros(grid_lon.shape, dtype=bool)
    pts  = np.column_stack([grid_lon.ravel(), grid_lat.ravel()])
    for poly in polys:
        if len(poly) < 3:
            continue
        inside = MPath(poly).contains_points(pts)
        mask  |= inside.reshape(grid_lon.shape)
    return mask


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §3  Interpolation                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def idw_interpolate(points: np.ndarray, values: np.ndarray,
                    xi: np.ndarray, power: float = 2.0) -> np.ndarray:
    """
    Inverse-Distance Weighting.

    Parameters
    ----------
    points : (n, 2)  known [lon, lat]
    values : (n,)    known values
    xi     : (m, 2)  query [lon, lat]
    power  : IDW exponent (default 2)
    """
    diff = xi[:, None, :] - points[None, :, :]   # (m, n, 2)
    dist = np.sqrt((diff ** 2).sum(-1))           # (m, n)
    dist = np.maximum(dist, 1e-12)
    w    = 1.0 / dist ** power                    # (m, n)
    return (w * values).sum(1) / w.sum(1)


def rbf_interpolate(points: np.ndarray, values: np.ndarray,
                    xi: np.ndarray,
                    kernel: str    = "thin_plate_spline",
                    smoothing: float = 0.5) -> np.ndarray:
    """
    RBF interpolation via scipy.interpolate.RBFInterpolator.

    smoothing=0.5 balances fit accuracy vs. overshoot with 12 points.
    """
    interp = RBFInterpolator(points, values,
                             smoothing=smoothing, kernel=kernel)
    return interp(xi).ravel()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §4  LOOCV                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def loocv(points: np.ndarray, values: np.ndarray,
          method: str = "IDW", **kwargs) -> dict:
    """
    Leave-One-Out Cross-Validation.

    Parameters
    ----------
    method : "IDW" | "RBF"
    **kwargs passed to the interpolation function.

    Returns
    -------
    dict with keys RMSE, MAE, Bias, R2
    """
    n = len(values)
    if n < 4:
        return {"RMSE": np.nan, "MAE": np.nan, "Bias": np.nan, "R2": np.nan}

    predicted = np.full(n, np.nan)
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        p_tr, v_tr = points[mask], values[mask]
        p_q        = points[[i]]

        try:
            if method == "IDW":
                predicted[i] = idw_interpolate(
                    p_tr, v_tr, p_q, kwargs.get("power", 2.0))[0]
            elif method == "RBF":
                predicted[i] = rbf_interpolate(
                    p_tr, v_tr, p_q,
                    kwargs.get("kernel", "thin_plate_spline"),
                    kwargs.get("smoothing", 0.5))[0]
        except Exception:
            pass

    valid = ~np.isnan(predicted)
    if valid.sum() < 3:
        return {"RMSE": np.nan, "MAE": np.nan, "Bias": np.nan, "R2": np.nan}

    res  = predicted[valid] - values[valid]
    rmse = float(np.sqrt(np.mean(res ** 2)))
    mae  = float(np.mean(np.abs(res)))
    bias = float(np.mean(res))
    sst  = float(np.sum((values[valid] - values[valid].mean()) ** 2))
    r2   = float(1 - np.sum(res**2) / sst) if sst > 0 else 0.0
    return {"RMSE": round(rmse, 4), "MAE": round(mae, 4),
            "Bias": round(bias, 4), "R2": round(r2, 4)}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §5  Best method selection                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def select_best(points: np.ndarray, values: np.ndarray,
                grid_lon: np.ndarray, grid_lat: np.ndarray,
                xi: np.ndarray
                ) -> tuple[np.ndarray, str, dict]:
    """
    Run IDW and RBF; select the method with lowest LOOCV RMSE.

    Returns
    -------
    best_zz      : (n, n) interpolated grid of the winning method
    best_name    : "IDW" | "RBF"
    all_metrics  : {method_name: {RMSE, MAE, Bias, R2}}
    """
    candidates: dict = {}

    for name, fn, kw in [
        ("IDW", idw_interpolate, {"power": 2.0}),
        ("RBF", rbf_interpolate, {"kernel": "thin_plate_spline", "smoothing": 0.5}),
    ]:
        try:
            cv = loocv(points, values, name, **kw)
            zz = fn(points, values, xi, **kw).reshape(grid_lon.shape)
            candidates[name] = {"metrics": cv, "zz": zz}
        except Exception as exc:
            warnings.warn(f"{name} failed: {exc}")

    if not candidates:
        raise RuntimeError("All interpolation methods failed.")

    best_name = min(
        candidates,
        key=lambda k: (np.isnan(candidates[k]["metrics"]["RMSE"]),
                       candidates[k]["metrics"]["RMSE"] or 1e9)
    )
    all_metrics = {k: v["metrics"] for k, v in candidates.items()}
    return candidates[best_name]["zz"], best_name, all_metrics


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §6  Validation export                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def save_validation_tables(all_metrics: dict,
                           loocv_detail: list[dict],
                           out_dir: Path) -> None:
    """
    Write Interpolation_Comparison.xlsx and LOOCV.xlsx to out_dir/validation/.

    Parameters
    ----------
    all_metrics  : {method_name: {RMSE, MAE, Bias, R2}}
    loocv_detail : list of row dicts with keys Scale, Method, RMSE, …
    """
    val_dir = Path(out_dir) / "validation"
    val_dir.mkdir(parents=True, exist_ok=True)

    # Interpolation comparison
    rows = [{"Method": m, **met} for m, met in all_metrics.items()]
    df   = pd.DataFrame(rows).set_index("Method")
    path = val_dir / "Interpolation_Comparison.xlsx"
    df.to_excel(path)
    print(f"    ✓ {path.name}")

    # Per-variable LOOCV detail
    if loocv_detail:
        df2  = pd.DataFrame(loocv_detail)
        path2 = val_dir / "LOOCV.xlsx"
        df2.to_excel(path2, index=False)
        print(f"    ✓ {path2.name}")
