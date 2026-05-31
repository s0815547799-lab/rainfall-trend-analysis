"""gis.interp — IDW/Kriging interpolation + boundary clip (config-driven)."""
from __future__ import annotations
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep

log = logging.getLogger(__name__)


def load_boundary(path, target_crs="EPSG:4326"):
    b = gpd.read_file(path).to_crs(target_crs)
    geom = b.union_all() if hasattr(b, "union_all") else b.unary_union
    return geom, tuple(b.total_bounds)


def idw(xy, vals, gx, gy, power=2.0):
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    d = np.sqrt(((pts[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2))
    d = np.where(d < 1e-9, 1e-9, d)
    w = 1.0 / d ** power
    z = (w * vals[None, :]).sum(axis=1) / w.sum(axis=1)
    return z.reshape(gx.shape)


def ordinary_kriging(xy, vals, gx, gy):
    """Lightweight OK with exponential variogram; falls back to IDW if singular."""
    try:
        from scipy.spatial.distance import cdist
        from scipy.linalg import solve
        n = len(xy)
        D = cdist(xy, xy)
        rng = D.max() or 1.0
        def vg(h): return vals.var() * (1 - np.exp(-3 * h / rng)) if vals.var() > 0 else h * 0
        G = vg(D); G = np.vstack([np.hstack([G, np.ones((n, 1))]),
                                  np.hstack([np.ones((1, n)), [[0]]])])
        pts = np.column_stack([gx.ravel(), gy.ravel()])
        Dp = cdist(pts, xy)
        z = np.empty(len(pts))
        for i in range(len(pts)):
            b = np.append(vg(Dp[i]), 1.0)
            lam = solve(G, b)
            z[i] = (lam[:-1] * vals).sum()
        return z.reshape(gx.shape)
    except Exception as e:
        log.warning("kriging fallback to IDW: %s", e)
        return idw(xy, vals, gx, gy)


def surface(xy, vals, geom, bounds, cfg):
    g = cfg["gis"]; n = g["grid_n"]
    x0, y0, x1, y1 = bounds
    gx, gy = np.meshgrid(np.linspace(x0, x1, n), np.linspace(y0, y1, n))
    if g["interpolation"] == "kriging":
        z = ordinary_kriging(xy, vals, gx, gy)
    else:
        z = idw(xy, vals, gx, gy, g.get("idw_power", 2.0))
    pg = prep(geom)
    mask = np.fromiter((pg.contains(Point(x, y)) for x, y in zip(gx.ravel(), gy.ravel())),
                       bool, gx.size).reshape(gx.shape)
    return gx, gy, np.ma.array(z, mask=~mask), mask
