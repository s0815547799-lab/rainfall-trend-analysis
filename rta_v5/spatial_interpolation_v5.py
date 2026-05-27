"""
rta_v5.spatial_interpolation_v5 — Province-independent boundary loading,
IDW / RBF interpolation, and LOOCV validation.

Boundary is loaded exclusively from a directory containing exactly:
    boundary.shp / boundary.dbf / boundary.shx / boundary.prj

No province names appear anywhere in this module.
No convex-hull or bounding-box fallback exists.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
from scipy.interpolate import RBFInterpolator

# ── Defaults ─────────────────────────────────────────────────────────────────
GRID_N = 120    # default interpolation grid size (N×N)
PAD    = 0.18   # degrees of padding around boundary bbox


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1  Boundary                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def validate_boundary(boundary_dir: str | Path) -> None:
    """
    Raise FileNotFoundError if any required boundary file is missing.

    Required files (all in boundary_dir):
        boundary.shp  boundary.dbf  boundary.shx  boundary.prj

    To change the study area, replace these four files only.
    No code edits are needed.
    """
    d = Path(boundary_dir)
    required = ["boundary.shp", "boundary.dbf", "boundary.shx", "boundary.prj"]
    missing  = [f for f in required if not (d / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing boundary files in {d}:\n"
            + "\n".join(f"  • {m}" for m in missing)
            + "\n\nTo use a different study area, replace the four files in:\n"
            + f"  {d}\nwith boundary.shp / .dbf / .shx / .prj for the new area."
        )


def load_boundary(boundary_dir: str | Path) -> list[np.ndarray]:
    """
    Load all polygons from boundary_dir/boundary.shp.

    Parameters
    ----------
    boundary_dir : directory containing boundary.shp (and companion files)

    Returns
    -------
    list of (N, 2) arrays [lon, lat columns]

    Raises
    ------
    FileNotFoundError  — if any required file is absent
    RuntimeError       — if the shapefile contains no valid polygons
    """
    validate_boundary(boundary_dir)
    shp_path = Path(boundary_dir) / "boundary.shp"

    import shapefile as sf_lib
    reader = sf_lib.Reader(str(shp_path))
    polys  = []
    for shape in reader.shapes():
        pts = np.array(shape.points)
        if len(pts) >= 3:
            polys.append(pts)

    if not polys:
        raise RuntimeError(
            f"No valid polygons (≥ 3 points) found in {shp_path.name}. "
            "Confirm the file is a polygon-type shapefile."
        )
    print(f"    Boundary: {shp_path.name} — {len(polys)} polygon(s)")
    return polys


def boundary_extent(polys: list[np.ndarray],
                    pad: float = PAD) -> tuple[float, float, float, float]:
    """Return (xmin, xmax, ymin, ymax) padded bounding box of all polygons."""
    all_pts = np.vstack(polys)
    return (
        float(all_pts[:, 0].min()) - pad,
        float(all_pts[:, 0].max()) + pad,
        float(all_pts[:, 1].min()) - pad,
        float(all_pts[:, 1].max()) + pad,
    )


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §2  Grid and mask                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def build_grid(
    xmin: float, xmax: float, ymin: float, ymax: float,
    n: int = GRID_N,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a regular (n×n) query grid over [xmin,xmax] × [ymin,ymax].

    Returns
    -------
    gl, gt : (n, n) meshgrids  (lon, lat)
    xi     : (n*n, 2) flattened query points [lon, lat]
    """
    gl, gt = np.meshgrid(
        np.linspace(xmin, xmax, n),
        np.linspace(ymin, ymax, n),
    )
    xi = np.column_stack([gl.ravel(), gt.ravel()])
    return gl, gt, xi


def make_boundary_mask(
    gl: np.ndarray, gt: np.ndarray, polys: list[np.ndarray]
) -> np.ndarray:
    """
    Boolean mask — True for grid cells inside any boundary polygon.
    Uses matplotlib.path for point-in-polygon.
    """
    from matplotlib.path import Path as MPath
    mask = np.zeros(gl.shape, dtype=bool)
    pts  = np.column_stack([gl.ravel(), gt.ravel()])
    for poly in polys:
        if len(poly) < 3:
            continue
        inside = MPath(poly).contains_points(pts)
        mask  |= inside.reshape(gl.shape)
    return mask


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §3  Interpolation                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def idw_interpolate(
    points: np.ndarray, values: np.ndarray,
    xi: np.ndarray, power: float = 2.0,
) -> np.ndarray:
    """Inverse-Distance Weighting (vectorised)."""
    diff = xi[:, None, :] - points[None, :, :]
    dist = np.maximum(np.sqrt((diff ** 2).sum(-1)), 1e-12)
    w    = 1.0 / dist ** power
    return (w * values).sum(1) / w.sum(1)


def rbf_interpolate(
    points: np.ndarray, values: np.ndarray,
    xi: np.ndarray,
    kernel: str    = "thin_plate_spline",
    smoothing: float = 0.5,
) -> np.ndarray:
    """RBF interpolation via scipy.interpolate.RBFInterpolator."""
    interp = RBFInterpolator(points, values, smoothing=smoothing, kernel=kernel)
    return interp(xi).ravel()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §4  LOOCV                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def loocv(
    points: np.ndarray, values: np.ndarray,
    method: str = "IDW", **kwargs,
) -> dict:
    """
    Leave-One-Out Cross-Validation.

    Parameters
    ----------
    method   : 'IDW' | 'RBF'
    **kwargs : forwarded to the interpolation function

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
        try:
            if method == "IDW":
                predicted[i] = idw_interpolate(
                    points[mask], values[mask], points[[i]],
                    kwargs.get("power", 2.0)
                )[0]
            elif method == "RBF":
                predicted[i] = rbf_interpolate(
                    points[mask], values[mask], points[[i]],
                    kwargs.get("kernel", "thin_plate_spline"),
                    kwargs.get("smoothing", 0.5),
                )[0]
        except Exception:
            pass

    valid = ~np.isnan(predicted)
    if valid.sum() < 3:
        return {"RMSE": np.nan, "MAE": np.nan, "Bias": np.nan, "R2": np.nan}

    res  = predicted[valid] - values[valid]
    sst  = float(np.sum((values[valid] - values[valid].mean()) ** 2))
    return {
        "RMSE": round(float(np.sqrt(np.mean(res ** 2))), 4),
        "MAE":  round(float(np.mean(np.abs(res))), 4),
        "Bias": round(float(np.mean(res)), 4),
        "R2":   round(float(1 - np.sum(res ** 2) / sst), 4) if sst > 0 else 0.0,
    }


def select_best(
    points: np.ndarray, values: np.ndarray,
    gl: np.ndarray, gt: np.ndarray, xi: np.ndarray,
) -> tuple[np.ndarray, str, dict]:
    """
    Run IDW and RBF; return the method with the lower LOOCV RMSE.

    Returns
    -------
    best_zz     : (n, n) interpolated grid
    best_name   : 'IDW' | 'RBF'
    all_metrics : {method_name: {RMSE, MAE, Bias, R2}}
    """
    candidates: dict = {}
    for name, fn, kw in [
        ("IDW", idw_interpolate, {"power": 2.0}),
        ("RBF", rbf_interpolate, {"kernel": "thin_plate_spline", "smoothing": 0.5}),
    ]:
        try:
            cv = loocv(points, values, name, **kw)
            zz = fn(points, values, xi, **kw).reshape(gl.shape)
            candidates[name] = {"metrics": cv, "zz": zz}
        except Exception as exc:
            warnings.warn(f"{name} failed: {exc}")

    if not candidates:
        raise RuntimeError("All interpolation methods failed.")

    best_name = min(
        candidates,
        key=lambda k: (
            np.isnan(candidates[k]["metrics"]["RMSE"]),
            candidates[k]["metrics"]["RMSE"] or 1e9,
        ),
    )
    return (
        candidates[best_name]["zz"],
        best_name,
        {k: v["metrics"] for k, v in candidates.items()},
    )
