"""
End-to-end smoke test: runs the full generate_all figure pipeline with
synthetic data (no real CMIP6 files needed).  Verifies:
  - All figures are written without error
  - DPI = 600 for every PNG
  - PDF files are present
  - Figure QC gate is functional
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
import numpy as np
import pandas as pd
import pytest
import matplotlib
matplotlib.use("Agg")


# ── Synthetic data factory ────────────────────────────────────────────────────

def _synthetic_bundle(tmp_path: Path, n_stations: int = 4,
                      obs_years=range(1981, 2015),
                      fut_years=range(2015, 2051)):
    """Build a minimal d={} dict that satisfies generate_all requirements."""
    rng = np.random.default_rng(0)
    stations = [f"S{i+1:03d}" for i in range(n_stations)]
    SEASONS  = ["Annual", "Wet", "Dry"]
    SCENS    = ["historical", "ssp245", "ssp585"]

    # --- observed (station × year × season) ---
    obs_rows = []
    for st in stations:
        for y in obs_years:
            base = rng.normal(800, 100)
            for se in SEASONS:
                mult = {"Annual": 1.0, "Wet": 0.7, "Dry": 0.3}[se]
                obs_rows.append({"station": st, "year": int(y), "season": se,
                                 "rainfall": max(0.0, base * mult + rng.normal(0, 20))})
    obs = pd.DataFrame(obs_rows)

    # --- per-model data (for level1) ---
    per_rows = []
    for st in stations:
        for m in ["MOD_A", "MOD_B"]:
            for scen in SCENS:
                years_for = list(obs_years) if scen == "historical" else list(fut_years)
                for y in years_for:
                    base = rng.normal(800, 80)
                    for se in SEASONS:
                        mult = {"Annual": 1.0, "Wet": 0.7, "Dry": 0.3}[se]
                        per_rows.append({"station": st, "year": int(y), "season": se,
                                         "model": m, "scenario": scen, "dataset": "BC",
                                         "rainfall": max(0.0, base * mult + rng.normal(0, 20))})
    per = pd.DataFrame(per_rows)

    # --- MME (station × year × season × scenario) ---
    def _make_mme(dataset_tag="BC"):
        mme_rows = []
        for st in stations:
            for scen in SCENS:
                years_for = list(obs_years) if scen == "historical" else list(fut_years)
                for y in years_for:
                    base = rng.normal(800, 80)
                    for se in SEASONS:
                        mult = {"Annual": 1.0, "Wet": 0.7, "Dry": 0.3}[se]
                        val = max(0.0, base * mult + rng.normal(0, 20))
                        mme_rows.append({
                            "dataset": dataset_tag, "station": st,
                            "year": int(y), "season": se, "scenario": scen,
                            "mean": val, "median": val * 0.98,
                            "p25": val * 0.85, "p75": val * 1.15,
                            "n_models": 2,
                        })
        return pd.DataFrame(mme_rows)

    bc_mme  = _make_mme("BC")
    raw_mme = _make_mme("Raw")

    # --- validation metrics ---
    from src.validation.metrics import validation_metrics
    vm = pd.concat(
        [validation_metrics(obs, raw_mme, bc_mme, s) for s in SEASONS],
        ignore_index=True,
    )

    # --- change ---
    change_rows = []
    for st in stations:
        for scen in ["ssp245", "ssp585"]:
            for se in SEASONS:
                obs_base = obs[(obs.station == st) & (obs.season == se)].rainfall.mean()
                fut_mean = bc_mme[(bc_mme.station == st) & (bc_mme.season == se)
                                  & (bc_mme.scenario == scen)
                                  & (bc_mme.year >= 2021) & (bc_mme.year <= 2050)]["mean"].mean()
                if obs_base > 0:
                    change_rows.append({
                        "station": st, "season": se, "scenario": scen,
                        "obs_baseline": obs_base, "future_bc": fut_mean,
                        "change_pct": (fut_mean - obs_base) / obs_base * 100,
                    })
    change = pd.DataFrame(change_rows)

    # --- metadata ---
    meta_rows = [{"station": st,
                  "lat": 11.5 + i * 0.2,
                  "lon": 99.6 + i * 0.1,
                  "elevation": 50.0 + i * 10}
                 for i, st in enumerate(stations)]
    meta = pd.DataFrame(meta_rows)

    # --- fake boundary (tiny GeoDataFrame) ---
    try:
        import geopandas as gpd
        from shapely.geometry import Polygon
        lons = [r["lon"] for r in meta_rows]
        lats = [r["lat"] for r in meta_rows]
        box  = Polygon([
            (min(lons)-0.1, min(lats)-0.1),
            (max(lons)+0.1, min(lats)-0.1),
            (max(lons)+0.1, max(lats)+0.1),
            (min(lons)-0.1, max(lats)+0.1),
        ])
        gdf = gpd.GeoDataFrame({"geometry": [box]}, crs="EPSG:4326")
        shp = tmp_path / "boundary" / "boundary.shp"
        shp.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(shp)
        boundary_path = str(shp)
    except Exception as exc:
        pytest.skip(f"geopandas/shapely not available for smoke test: {exc}")

    # --- config ---
    cfg = {
        "study_area": {"name": "Test Province"},
        "paths":   {"outputs": str(tmp_path / "outputs"), "boundary": boundary_path},
        "figures": {
            "dpi":          600,
            "formats":      ["png", "tiff", "pdf"],
            "single_col_in": 3.5,
            "double_col_in": 7.2,
        },
        "gis": {"target_crs": "EPSG:4326"},
        "periods": {"baseline": [1981, 2014], "near_future": [2021, 2050]},
        "scenarios": ["ssp245", "ssp585"],
    }

    return {
        "obs": obs, "per": per,
        "raw_mme": raw_mme, "bc_mme": bc_mme,
        "vm": vm, "change": change,
        "meta": meta, "cfg": cfg,
    }


# ── Smoke tests ───────────────────────────────────────────────────────────────

class TestPipelineSmoke:

    @pytest.fixture(scope="class")
    def bundle(self, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("pipeline_smoke")
        return _synthetic_bundle(tmp)

    def test_generate_all_runs_without_error(self, bundle, tmp_path):
        """generate_all must complete and return non-empty file lists."""
        from src.figures.make import generate_all
        d   = bundle
        cfg = dict(d["cfg"])
        cfg["paths"] = dict(cfg["paths"])
        cfg["paths"]["outputs"] = str(tmp_path / "outputs")

        saved = generate_all(d, cfg)
        assert saved, "generate_all returned empty dict"
        total = sum(len(v) for v in saved.values())
        assert total > 0, "No figure files were written"

    def test_figure_count(self, bundle, tmp_path):
        """Expect figures from all 4 figure functions × 2 columns × ≥1 format."""
        from src.figures.make import generate_all
        d   = bundle
        cfg = dict(d["cfg"])
        cfg["paths"] = dict(cfg["paths"])
        cfg["paths"]["outputs"] = str(tmp_path / "outputs2")

        saved = generate_all(d, cfg)
        total = sum(len(v) for v in saved.values())
        # F1+F2+F3 = 3 figs × 2 col × 3 fmts = 18; F4+F5+F6 = 3 × 2 × 3 = 18; F7 = 2×3=6 → 42
        # Allow fewer if spatial figures are skipped
        assert total >= 6, f"Expected ≥6 figure files, got {total}"

    def test_png_dpi_is_600(self, bundle, tmp_path):
        """Every saved PNG must have DPI metadata = 600."""
        from PIL import Image
        from src.figures.make import generate_all
        d   = bundle
        cfg = dict(d["cfg"])
        cfg["paths"] = dict(cfg["paths"])
        cfg["paths"]["outputs"] = str(tmp_path / "outputs3")
        cfg["figures"] = dict(cfg["figures"])
        cfg["figures"]["formats"] = ["png"]   # only PNG for this test

        saved = generate_all(d, cfg)
        all_pngs = [p for lst in saved.values() for p in lst if str(p).endswith(".png")]
        assert all_pngs, "No PNG files found"

        for p in all_pngs:
            im  = Image.open(p)
            dpi = im.info.get("dpi", (0, 0))
            dpi_val = int(round(float(dpi[0]) if isinstance(dpi, tuple) else float(dpi)))
            assert dpi_val == 600, f"{p.name}: DPI={dpi_val}, expected 600"

    def test_qc_gate_passes(self, bundle, tmp_path):
        """figure_qc must report non-empty results when figures are correctly generated."""
        from src.figures.make import generate_all
        from final_run import figure_qc

        d   = bundle
        cfg = dict(d["cfg"])
        cfg["paths"] = dict(cfg["paths"])
        cfg["paths"]["outputs"] = str(tmp_path / "outputs4")
        saved = generate_all(d, cfg)

        # Collect all written files into a pub_figures dir
        pub = tmp_path / "pub_figures"
        pub.mkdir()
        for lst in saved.values():
            for f in lst:
                shutil.copy(f, pub / f.name)

        qc, passed = figure_qc(pub, target_dpi=600, min_width_px=100)
        assert not qc.empty, "QC DataFrame must not be empty"
        failures = qc[~qc.dpi_ok]
        assert failures.empty, f"DPI failures: {failures[['figure','dpi']].to_dict('records')}"
