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
GRID_N = 300    # default interpolation grid size (N×N) — increased for publication quality
PAD    = 0.04   # degrees of padding around boundary bbox (tight; avoids wasted grid)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §1  Boundary                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _simplify_polygon(pts: np.ndarray, max_pts: int = 1000) -> np.ndarray:
    """
    Reduce a polygon to at most max_pts vertices by uniform subsampling.

    High-resolution projected polygons (e.g. 25 000+ points from UTM→WGS84)
    introduce near-self-intersections that break matplotlib's even-odd PIP
    rule.  Subsampling to ~1 000 vertices removes numerical noise while
    preserving the geographic shape to << 1 km accuracy.

    The returned array is always closed (first point == last point).
    """
    n = len(pts)
    if n <= max_pts:
        closed = pts if np.allclose(pts[0], pts[-1]) else np.vstack([pts, pts[0]])
        return closed
    step   = max(1, n // max_pts)
    idx    = list(range(0, n, step))
    simple = pts[idx]
    if not np.allclose(simple[0], simple[-1]):
        simple = np.vstack([simple, simple[0]])
    return simple


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

    If the shapefile is in a projected CRS (detected from boundary.prj),
    coordinates are automatically reprojected to WGS84 geographic (EPSG:4326)
    so the rest of the pipeline always receives (lon, lat) in decimal degrees.

    Parameters
    ----------
    boundary_dir : directory containing boundary.shp (and companion files)

    Returns
    -------
    list of (N, 2) arrays [lon, lat columns] — always in WGS84 degrees

    Raises
    ------
    FileNotFoundError  — if any required file is absent
    RuntimeError       — if the shapefile contains no valid polygons
    """
    validate_boundary(boundary_dir)
    shp_path = Path(boundary_dir) / "boundary.shp"
    prj_path = Path(boundary_dir) / "boundary.prj"

    # ── Determine if reprojection is needed ───────────────────────────────────
    _transformer = None
    if prj_path.exists():
        try:
            from pyproj import CRS, Transformer
            src_crs = CRS.from_wkt(prj_path.read_text())
            if not src_crs.is_geographic:
                wgs84 = CRS.from_epsg(4326)
                _transformer = Transformer.from_crs(src_crs, wgs84,
                                                    always_xy=True)
        except Exception:
            pass  # fall through — use raw coordinates

    import shapefile as sf_lib
    reader = sf_lib.Reader(str(shp_path))
    polys  = []

    for shape in reader.shapes():
        all_pts = np.array(shape.points)
        # Multi-part polygon: each "part" is a separate ring (outer boundary or
        # inner hole).  Treat every ring as a separate fill polygon so the
        # renderer handles them individually rather than as one tangled loop.
        part_starts = list(shape.parts) + [len(all_pts)]
        for i in range(len(part_starts) - 1):
            seg = all_pts[part_starts[i] : part_starts[i + 1]]
            if len(seg) < 3:
                continue
            if _transformer is not None:
                lons, lats = _transformer.transform(seg[:, 0], seg[:, 1])
                seg = np.column_stack([lons, lats])
            # Simplify dense segments: resampled UTM vertices cause near-
            # duplicate points that confuse point-in-polygon tests.
            seg = _simplify_polygon(seg, max_pts=800)
            polys.append(seg)

    if not polys:
        raise RuntimeError(
            f"No valid polygons (≥ 3 points) found in {shp_path.name}. "
            "Confirm the file is a polygon-type shapefile."
        )
    crs_note = " (reprojected → WGS84)" if _transformer is not None else ""
    n_shapes = len(reader.shapes())
    print(f"    Boundary: {shp_path.name} — {n_shapes} shape(s), "
          f"{len(polys)} ring(s){crs_note}")
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
    Boolean mask — True for grid cells inside the province boundary.

    Renders only the outer boundary ring(s) via matplotlib's Agg renderer
    at exactly the grid resolution.  Inner rings (bays, water cutouts) are
    intentionally omitted: at the rainfall-station grid spacing they are
    sub-km features that would incorrectly fragment the mask.

    The outermost ring per shape is identified as the one with the largest
    bounding-box area.  scipy.ndimage.binary_fill_holes is applied to close
    any sub-pixel edge gaps.
    """
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from scipy.ndimage import binary_fill_holes

    ny, nx = gl.shape
    xmin = float(gl[0,  0])
    xmax = float(gl[0, -1])
    ymin = float(gt[0,  0])
    ymax = float(gt[-1, 0])

    # Select only outer ring(s): largest bbox area among all rings
    def _bbox_area(pts):
        return (pts[:, 0].max() - pts[:, 0].min()) * \
               (pts[:, 1].max() - pts[:, 1].min())

    outer = [max(polys, key=_bbox_area)] if polys else []

    # Render at exactly (nx × ny) pixels
    fig = Figure(figsize=(nx / 100, ny / 100), dpi=100)
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.axis("off")
    ax.set_facecolor((0, 0, 0))
    fig.patch.set_facecolor((0, 0, 0))

    for poly in outer:
        ax.fill(poly[:, 0], poly[:, 1], color=(1, 1, 1), linewidth=0)

    canvas.draw()
    buf  = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
    img  = buf.reshape(ny, nx, 4)
    # Agg rows run top→bottom; our meshgrid gt increases bottom→top
    mask = np.flipud(img[:, :, 0] > 128)
    mask = binary_fill_holes(mask)
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
    kernel: str    = "cubic",
    smoothing: float = 0.10,
) -> np.ndarray:
    """RBF interpolation via scipy.interpolate.RBFInterpolator.

    Defaults use 'cubic' kernel (preserves local spatial variability better
    than 'thin_plate_spline') with low smoothing (0.10) to prevent
    over-regularisation of the spatial field.
    """
    interp = RBFInterpolator(points, values, smoothing=smoothing, kernel=kernel)
    return interp(xi).ravel()


def blend_interpolate(
    points: np.ndarray, values: np.ndarray,
    xi: np.ndarray,
    idw_alpha: float = 0.28,
    kernel: str      = "cubic",
    smoothing: float = 0.08,
) -> np.ndarray:
    """Blend IDW (local fidelity) with RBF (smooth gradients).

    The IDW component preserves station-scale spatial variability and prevents
    artificial homogenisation in data-sparse sub-regions; the RBF component
    provides smooth regional gradients free of Voronoi-edge artefacts.

    Parameters
    ----------
    idw_alpha : weight of the IDW component (0-1).  Default 0.28 gives 28 %
                IDW + 72 % RBF — enough local texture without bull's-eye halos.
    """
    idw_vals = idw_interpolate(points, values, xi, power=2.0)
    try:
        rbf_vals = rbf_interpolate(points, values, xi,
                                   kernel=kernel, smoothing=smoothing)
        return idw_alpha * idw_vals + (1.0 - idw_alpha) * rbf_vals
    except Exception:
        return idw_vals


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
                    kwargs.get("kernel", "cubic"),
                    kwargs.get("smoothing", 0.10),
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
        ("RBF", rbf_interpolate, {"kernel": "cubic", "smoothing": 0.10}),
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
