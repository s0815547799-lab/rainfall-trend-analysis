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
