"""gis.interp — IDW/Kriging interpolation + boundary clip (config-driven).

การปรับใช้กับพื้นที่ใหม่:
  - เปลี่ยน paths.boundary ใน config.yaml ให้ชี้ไปยัง shapefile ของพื้นที่ใหม่
  - ปรับ gis.interpolation ใน config.yaml (idw หรือ kriging)
  - ปรับ gis.grid_n สำหรับความละเอียด (200 = ดี, 400 = ดีมากแต่ช้ากว่า)
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep

log = logging.getLogger(__name__)


def load_boundary(path: str, target_crs: str = "EPSG:4326"):
    """Load study-area boundary shapefile and return (geometry, bounds).

    Accepts any CRS — reprojects to target_crs automatically.
    Returns (shapely geometry, (x_min, y_min, x_max, y_max)).
    """
    b = gpd.read_file(path).to_crs(target_crs)
    geom = b.union_all() if hasattr(b, "union_all") else b.unary_union
    return geom, tuple(b.total_bounds)


def idw(xy: np.ndarray, vals: np.ndarray,
        gx: np.ndarray, gy: np.ndarray,
        power: float = 2.0) -> np.ndarray:
    """Inverse Distance Weighting interpolation.

    Parameters
    ----------
    xy    : (n_stations, 2) array of [lon, lat]
    vals  : (n_stations,) array of values
    gx,gy : meshgrid arrays of prediction points
    power : IDW power parameter (default 2.0)
    """
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    d   = np.sqrt(((pts[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2))
    d   = np.where(d < 1e-9, 1e-9, d)
    w   = 1.0 / d ** power
    z   = (w * vals[None, :]).sum(axis=1) / w.sum(axis=1)
    return z.reshape(gx.shape)


def ordinary_kriging(xy: np.ndarray, vals: np.ndarray,
                     gx: np.ndarray, gy: np.ndarray,
                     nugget_frac: float = 0.05) -> np.ndarray:
    """Ordinary Kriging with an EMPIRICAL exponential variogram.

    NOTE ON METHOD (v3.5): the variogram is not fitted to an experimental
    semivariogram.  It uses sill = sample variance, effective range = maximum
    pairwise distance, and an optional nugget (`nugget_frac` × sill).  This is
    a pragmatic interpolator suitable for visual surfaces; it is NOT a
    geostatistically-fitted kriging model.  If kriged surfaces are reported in
    a manuscript, either (a) fit the variogram to the experimental
    semivariogram and report leave-one-out cross-validation (see
    `loocv_rmse`), or (b) use IDW (the configured default) and state so.
    Negative predictions are clipped to 0 because rainfall is non-negative.
    LU-factorises the kriging system once and solves all prediction points in
    batch.  Falls back to IDW if the system is singular.
    """
    try:
        from scipy.spatial.distance import cdist
        from scipy.linalg import lu_factor, lu_solve

        n   = len(xy)
        D   = cdist(xy, xy)
        rng = D.max() or 1.0
        sill = np.var(vals, ddof=0)
        nug  = max(nugget_frac, 0.0) * sill

        def vg(h: np.ndarray) -> np.ndarray:
            if sill <= 0:
                return np.zeros_like(h)
            g = nug + (sill - nug) * (1 - np.exp(-3 * h / rng))
            return np.where(h <= 0, 0.0, g)   # γ(0) = 0 exactly

        # Build augmented kriging matrix G (n+1 × n+1)
        G = np.vstack([
            np.hstack([vg(D),            np.ones((n, 1))]),
            np.hstack([np.ones((1, n)),  np.zeros((1, 1))]),
        ])
        lu, piv = lu_factor(G)   # factorise once

        # Prediction points
        pts = np.column_stack([gx.ravel(), gy.ravel()])
        Dp  = cdist(pts, xy)

        # Batch solve: build all RHS vectors at once (n_pts × n+1)
        rhs = np.hstack([vg(Dp), np.ones((len(pts), 1))])   # (n_pts, n+1)
        lam = lu_solve((lu, piv), rhs.T)   # (n+1, n_pts)
        z   = (lam[:-1] * vals[:, None]).sum(axis=0)
        z   = np.clip(z, 0.0, None)        # rainfall ≥ 0 (FIX-D)
        return z.reshape(gx.shape)

    except Exception as exc:
        log.warning("kriging fallback to IDW: %s", exc)
        return idw(xy, vals, gx, gy)


def loocv_rmse(xy: np.ndarray, vals: np.ndarray, method: str = "idw",
               power: float = 2.0) -> float:
    """Leave-one-out cross-validation RMSE for the chosen interpolator.

    Lets the manuscript report a defensible skill metric for the
    interpolation surface (mm).  Returns NaN if fewer than 3 stations.
    """
    n = len(xy)
    if n < 3:
        return float("nan")
    errs = []
    for i in range(n):
        keep = np.arange(n) != i
        gx = np.array([[xy[i, 0]]]); gy = np.array([[xy[i, 1]]])
        if method == "kriging":
            pred = ordinary_kriging(xy[keep], vals[keep], gx, gy)[0, 0]
        else:
            pred = idw(xy[keep], vals[keep], gx, gy, power)[0, 0]
        errs.append(pred - vals[i])
    return float(np.sqrt(np.mean(np.square(errs))))


def surface(xy: np.ndarray, vals: np.ndarray,
            geom, bounds: tuple, cfg: dict):
    """Interpolate station values to a regular grid, clipped to boundary.

    Parameters
    ----------
    xy     : (n_stations, 2) lon/lat array
    vals   : (n_stations,) value array
    geom   : shapely boundary geometry
    bounds : (x0, y0, x1, y1) from load_boundary
    cfg    : full config dict

    Returns
    -------
    gx, gy : meshgrid coordinates
    z      : masked array (NaN outside boundary)
    mask   : boolean array (True = inside boundary)
    """
    g  = cfg["gis"]
    n  = g["grid_n"]
    x0, y0, x1, y1 = bounds
    gx, gy = np.meshgrid(np.linspace(x0, x1, n),
                         np.linspace(y0, y1, n))

    if g["interpolation"] == "kriging":
        z = ordinary_kriging(xy, vals, gx, gy)
    else:
        z = idw(xy, vals, gx, gy, g.get("idw_power", 2.0))
    z = np.clip(z, 0.0, None)   # rainfall is non-negative (FIX-D)

    pg   = prep(geom)
    mask = np.fromiter(
        (pg.contains(Point(x, y)) for x, y in zip(gx.ravel(), gy.ravel())),
        bool, gx.size,
    ).reshape(gx.shape)

    return gx, gy, np.ma.array(z, mask=~mask), mask
