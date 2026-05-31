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
                     gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
    """Lightweight Ordinary Kriging with exponential variogram.

    LU-factorises the kriging system once and solves for all prediction
    points in batch (avoids N_grid × full factorisation overhead).
    Falls back to IDW if the system is singular.
    """
    try:
        from scipy.spatial.distance import cdist
        from scipy.linalg import lu_factor, lu_solve

        n   = len(xy)
        D   = cdist(xy, xy)
        rng = D.max() or 1.0

        def vg(h: np.ndarray) -> np.ndarray:
            v = np.var(vals, ddof=0)
            return v * (1 - np.exp(-3 * h / rng)) if v > 0 else np.zeros_like(h)

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
        # Solve column-by-column (each grid point is one column of rhs.T)
        lam = lu_solve((lu, piv), rhs.T)   # (n+1, n_pts)
        z   = (lam[:-1] * vals[:, None]).sum(axis=0)
        return z.reshape(gx.shape)

    except Exception as exc:
        log.warning("kriging fallback to IDW: %s", exc)
        return idw(xy, vals, gx, gy)


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

    pg   = prep(geom)
    mask = np.fromiter(
        (pg.contains(Point(x, y)) for x, y in zip(gx.ravel(), gy.ravel())),
        bool, gx.size,
    ).reshape(gx.shape)

    return gx, gy, np.ma.array(z, mask=~mask), mask
