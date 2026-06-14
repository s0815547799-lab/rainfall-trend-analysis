"""gis.geo_lite — dependency-free shapefile + reprojection backend.

Reads ESRI Polygon shapefiles, reprojects to WGS84 lon/lat using parameters
parsed from the companion .prj, and builds boundary masks with
matplotlib.path — all with only numpy + matplotlib (no geopandas / shapely /
pyproj / fiona).  This makes the GIS/figure stage runnable in minimal
environments and portable to ANY province's shapefile (UTM or geographic).

Supported .prj cases:
  • PROJCS Transverse_Mercator (UTM zones, incl. Thai UTM 47N/48N): inverse TM.
  • GEOGCS only (already lon/lat): identity.
  • Anything else: identity + warning (assumes lon/lat).
"""
from __future__ import annotations

import math
import struct
import logging
import re
from pathlib import Path as _P

import numpy as np

log = logging.getLogger(__name__)


# ── .prj parsing ──────────────────────────────────────────────────────────────

def _grab(txt: str, key: str) -> float | None:
    m = re.search(rf'PARAMETER\["{key}",\s*([-\d.]+)\]', txt, re.IGNORECASE)
    return float(m.group(1)) if m else None


def parse_prj(prj_path: str | _P):
    """Return a reprojection function f(x, y)->(lon, lat) inferred from the .prj.

    Falls back to identity (assume lon/lat) if no .prj or unrecognised."""
    p = _P(prj_path)
    if not p.exists():
        log.warning("geo_lite: no .prj (%s); assuming coordinates are lon/lat", p.name)
        return lambda x, y: (x, y), "lonlat(assumed)"
    txt = p.read_text(errors="ignore")

    if "PROJCS" not in txt.upper() and "GEOGCS" in txt.upper():
        return lambda x, y: (x, y), "geographic(lon/lat)"

    if "TRANSVERSE_MERCATOR" in txt.upper():
        a = 6378137.0
        sm = re.search(r'SPHEROID\["[^"]*",\s*([-\d.]+),\s*([-\d.]+)\]', txt)
        if sm:
            a = float(sm.group(1)); invf = float(sm.group(2))
            f = 1.0 / invf if invf else 1 / 298.257223563
        else:
            f = 1 / 298.257223563
        lon0 = math.radians(_grab(txt, "Central_Meridian") or 0.0)
        k0   = _grab(txt, "Scale_Factor")   or 0.9996
        E0   = _grab(txt, "False_Easting")  or 0.0
        N0   = _grab(txt, "False_Northing") or 0.0
        lat0 = math.radians(_grab(txt, "Latitude_Of_Origin") or 0.0)
        fn = _make_tm_inverse(a, f, lon0, k0, E0, N0, lat0)
        zone = (math.degrees(lon0) + 183) / 6
        return fn, f"UTM-like TM (zone≈{zone:.0f}N, CM={math.degrees(lon0):.1f})"

    log.warning("geo_lite: unrecognised .prj projection; assuming lon/lat")
    return lambda x, y: (x, y), "unknown(assumed lon/lat)"


def _make_tm_inverse(a, f, lon0, k0, E0, N0, lat0):
    """Inverse Transverse Mercator (Snyder 1987), vectorised over arrays."""
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    M0 = a * ((1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * lat0
              - (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * math.sin(2*lat0)
              + (15*e2**2/256 + 45*e2**3/1024) * math.sin(4*lat0)
              - (35*e2**3/3072) * math.sin(6*lat0))

    def inv(E, N):
        E = np.asarray(E, float); N = np.asarray(N, float)
        M = M0 + (N - N0) / k0
        mu = M / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))
        phi1 = (mu + (3*e1/2 - 27*e1**3/32) * np.sin(2*mu)
                + (21*e1**2/16 - 55*e1**4/32) * np.sin(4*mu)
                + (151*e1**3/96) * np.sin(6*mu)
                + (1097*e1**4/512) * np.sin(8*mu))
        C1 = ep2 * np.cos(phi1)**2
        T1 = np.tan(phi1)**2
        sin1 = np.sin(phi1)
        N1 = a / np.sqrt(1 - e2 * sin1**2)
        R1 = a * (1 - e2) / (1 - e2 * sin1**2)**1.5
        D = (E - E0) / (N1 * k0)
        lat = phi1 - (N1 * np.tan(phi1) / R1) * (
            D**2/2 - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*ep2) * D**4/24
            + (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*ep2 - 3*C1**2) * D**6/720)
        lon = lon0 + (D - (1 + 2*T1 + C1) * D**3/6
            + (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*ep2 + 24*T1**2) * D**5/120) / np.cos(phi1)
        return np.degrees(lon), np.degrees(lat)
    return inv


# ── Shapefile (.shp) polygon reader ───────────────────────────────────────────

def read_polygons(shp_path: str | _P) -> list[list[np.ndarray]]:
    """Return a list of polygon parts; each part is an (n,2) array of (x,y)
    in the file's native CRS.  Supports Polygon(5), PolygonZ(15), PolygonM(25)."""
    buf = open(shp_path, "rb").read()
    if struct.unpack(">i", buf[0:4])[0] != 9994:
        raise ValueError("not a valid .shp file (bad magic)")
    parts_all: list[np.ndarray] = []
    off = 100  # past header
    n = len(buf)
    while off + 8 <= n:
        _, clen = struct.unpack(">ii", buf[off:off+8])     # record header (16-bit words)
        rec = off + 8
        shp_type = struct.unpack("<i", buf[rec:rec+4])[0]
        if shp_type in (5, 15, 25):
            # box(4d) at rec+4..rec+36 ; numParts, numPoints at rec+36
            nparts, npoints = struct.unpack("<ii", buf[rec+36:rec+44])
            pstart = rec + 44
            part_idx = struct.unpack("<%di" % nparts, buf[pstart:pstart+4*nparts])
            pts_start = pstart + 4*nparts
            xy = struct.unpack("<%dd" % (2*npoints),
                               buf[pts_start:pts_start+16*npoints])
            xy = np.array(xy, float).reshape(npoints, 2)
            bounds = list(part_idx) + [npoints]
            for i in range(nparts):
                parts_all.append(xy[bounds[i]:bounds[i+1]])
        off = rec + clen * 2
    if not parts_all:
        raise ValueError("no polygon records found in shapefile")
    return [parts_all]   # wrap: one feature group of parts (rings)


def load_boundary_lonlat(shp_path: str | _P):
    """Load a boundary shapefile, reproject every ring to WGS84 lon/lat.

    Returns
    -------
    rings  : list of (n,2) arrays in lon/lat
    bounds : (lon_min, lat_min, lon_max, lat_max)
    crs    : human-readable description of the source projection used
    """
    prj = _P(shp_path).with_suffix(".prj")
    reproject, crs = parse_prj(prj)
    groups = read_polygons(shp_path)
    rings: list[np.ndarray] = []
    for parts in groups:
        for ring in parts:
            lon, lat = reproject(ring[:, 0], ring[:, 1])
            rings.append(np.column_stack([np.asarray(lon).ravel(),
                                          np.asarray(lat).ravel()]))
    allpts = np.vstack(rings)
    bounds = (float(allpts[:, 0].min()), float(allpts[:, 1].min()),
              float(allpts[:, 0].max()), float(allpts[:, 1].max()))
    log.info("geo_lite.load_boundary_lonlat: %d ring(s) | src=%s | "
             "lon[%.3f,%.3f] lat[%.3f,%.3f]",
             len(rings), crs, bounds[0], bounds[2], bounds[1], bounds[3])
    return rings, bounds, crs


def make_path(rings: list[np.ndarray]):
    """Build one matplotlib compound Path from boundary rings (even-odd holes)."""
    from matplotlib.path import Path as MPath
    verts, codes = [], []
    for r in rings:
        if len(r) < 3:
            continue
        verts.extend(r.tolist()); verts.append(r[0].tolist())
        codes.extend([MPath.MOVETO] + [MPath.LINETO] * (len(r) - 1) + [MPath.CLOSEPOLY])
    return MPath(np.asarray(verts), codes)


def mask_inside(rings, gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
    """Boolean mask (gx.shape): True where the grid point is inside the boundary."""
    path = make_path(rings)
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    return path.contains_points(pts).reshape(gx.shape)
