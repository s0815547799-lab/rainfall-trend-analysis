"""
Unit tests for all 10 bug fixes and Q1 publication standards.
Run with: python -m pytest tests/test_all_fixes.py -v
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import numpy as np
import pandas as pd
import pytest


# ===========================================================================
# Bug #1 + #2 + #9 — seasonal.py
# ===========================================================================

class TestSeasonal:
    """Tests for _wide_to_yearly: dry-season hydrological year, NaN guard, completeness."""

    @pytest.fixture
    def minimal_df(self):
        """Three calendar years (2000-2002) of daily data for station 500001."""
        from calendar import monthrange
        rows = []
        for y in [2000, 2001, 2002]:
            for m in range(1, 13):
                for d in range(1, monthrange(y, m)[1] + 1):
                    if m == 2 and d == 29:
                        continue   # skip leap day
                    rows.append({"YEAR": y, "MONTH": m, "DAY": d, "500001": 2.0})
        return pd.DataFrame(rows)

    @pytest.fixture
    def wet(self):
        return [5, 6, 7, 8, 9, 10]

    @pytest.fixture
    def dry(self):
        return [11, 12, 1, 2, 3, 4]

    def test_dry_season_hydrological_year(self, minimal_df, wet, dry):
        """Bug #1: Dry(2001) must include Nov+Dec 2000 + Jan–Apr 2001, NOT Nov–Apr 2000."""
        from src.rainfall.seasonal import _wide_to_yearly
        out = _wide_to_yearly(minimal_df.copy(), wet, dry, 2000, 2002)
        dry_rows = out[out.season == "Dry"]

        # Hydro year 2001 = Nov(2000) + Dec(2000) + Jan–Apr(2001)
        # Each day has rainfall = 2.0
        nov_dec_days  = 30 + 31     # Nov + Dec
        jan_apr_days  = 31 + 28 + 31 + 30   # Jan–Apr (2001, not a leap year check needed)
        expected_days = nov_dec_days + jan_apr_days
        expected_mm   = expected_days * 2.0

        row_2001 = dry_rows[dry_rows.year == 2001]
        assert len(row_2001) == 1, "should have one Dry row for hydro-year 2001"
        assert abs(float(row_2001.rainfall.values[0]) - expected_mm) < 1e-6, (
            f"Dry(2001) expected {expected_mm} mm (Nov2000+Dec2000+Jan-Apr2001), "
            f"got {row_2001.rainfall.values[0]}"
        )

    def test_dry_season_label_is_hydro_year(self, minimal_df, wet, dry):
        """Bug #1: The year label for a dry season must be the year the season ENDS."""
        from src.rainfall.seasonal import _wide_to_yearly
        out = _wide_to_yearly(minimal_df.copy(), wet, dry, 2000, 2002)
        dry_years = sorted(out[out.season == "Dry"].year.unique())
        # First possible hydro-year is 2001 (needs Nov+Dec 2000 and Jan–Apr 2001)
        # Last possible hydro-year is 2002 (needs Nov+Dec 2001 and Jan–Apr 2002)
        assert 2000 not in dry_years, "Dry year 2000 requires Nov/Dec 1999 — not in loaded data"
        assert 2001 in dry_years
        assert 2002 in dry_years

    def test_all_nan_year_returns_nan_not_zero(self, minimal_df, wet, dry):
        """Bug #2: A station with all-NaN data for a year must produce NaN, not 0.0."""
        from src.rainfall.seasonal import _wide_to_yearly
        # Set year 2001 to all NaN
        df = minimal_df.copy()
        df.loc[df.YEAR == 2001, "500001"] = np.nan
        out = _wide_to_yearly(df, wet, dry, 2000, 2002)
        ann_2001 = out[(out.season == "Annual") & (out.year == 2001) & (out.station == "500001")]
        assert len(ann_2001) == 1
        assert np.isnan(ann_2001.rainfall.values[0]), (
            "all-NaN year must yield NaN rainfall, not 0.0"
        )

    def test_completeness_threshold(self, minimal_df, wet, dry):
        """Bug #9: A year with <80% valid data must yield NaN."""
        from src.rainfall.seasonal import _wide_to_yearly
        df = minimal_df.copy()
        # Zero out 30% of year-2001 rows (set to NaN) — below 80% threshold
        mask_2001 = df.YEAR == 2001
        idx_2001  = df[mask_2001].index
        n_nan     = int(len(idx_2001) * 0.35)
        df.loc[idx_2001[:n_nan], "500001"] = np.nan
        out = _wide_to_yearly(df, wet, dry, 2000, 2002)
        ann_2001 = out[(out.season == "Annual") & (out.year == 2001) & (out.station == "500001")]
        assert np.isnan(float(ann_2001.rainfall.values[0])), (
            "35% missing data should trigger completeness gate → NaN"
        )

    def test_good_year_is_not_nan(self, minimal_df, wet, dry):
        """Sanity: a year with 100% data must NOT be NaN."""
        from src.rainfall.seasonal import _wide_to_yearly
        out = _wide_to_yearly(minimal_df.copy(), wet, dry, 2000, 2002)
        ann_2000 = out[(out.season == "Annual") & (out.year == 2000) & (out.station == "500001")]
        assert len(ann_2000) == 1
        assert np.isfinite(float(ann_2000.rainfall.values[0])), "complete year must be finite"


# ===========================================================================
# Bug #3 + #4 — metrics.py
# ===========================================================================

class TestMetrics:
    """Tests for kge, validation_metrics, and improvement columns."""

    def test_kge_perfect(self):
        from src.validation.metrics import kge
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert abs(kge(x, x) - 1.0) < 1e-10

    def test_kge_returns_nan_for_flat_obs(self):
        """KGE is undefined when obs has zero variance."""
        from src.validation.metrics import kge
        obs = np.array([2.0, 2.0, 2.0, 2.0])
        sim = np.array([1.0, 2.0, 3.0, 4.0])
        result = kge(obs, sim)
        assert np.isnan(result), "flat obs → NaN KGE"

    def test_kge_returns_nan_for_short_series(self):
        from src.validation.metrics import kge
        assert np.isnan(kge(np.array([1.0]), np.array([1.0])))

    def test_delta_kge_not_percentage_of_negative_baseline(self):
        """Bug #4: ΔKGE must be an absolute difference, not a ratio of |KGE_Raw|.

        Uses a non-degenerate (non-constant) Raw MME that has negative KGE:
        heavily biased (mean = 2× obs mean) and anti-correlated → KGE < 0.
        """
        from src.validation.metrics import kge

        rng = np.random.default_rng(42)
        obs = np.array([100., 150., 80., 120., 110., 140., 90., 130.])

        # Raw MME: mean-biased by 2× AND anti-correlated → KGE strongly negative
        raw = (obs.mean() * 2.0) - obs + rng.normal(0, 5, len(obs))
        # BC MME: close to obs
        bc  = obs + rng.normal(0, 5, len(obs))

        kge_raw = kge(obs, raw)
        kge_bc  = kge(obs, bc)

        assert np.isfinite(kge_raw), f"kge_raw should be finite, got {kge_raw}"
        assert np.isfinite(kge_bc),  f"kge_bc should be finite, got {kge_bc}"
        assert kge_raw < 0,          f"Raw KGE should be negative, got {kge_raw:.3f}"

        # ΔKGE (absolute) should be positive when BC is better
        delta_kge = kge_bc - kge_raw
        assert delta_kge > 0, f"BC should outperform Raw: ΔKGE={delta_kge:.3f}"

        # Demonstrate that the old formula (÷|KGE_Raw|) gives misleading values:
        old_formula_pct = (kge_bc - kge_raw) / abs(kge_raw) * 100
        # Old formula is unbounded and not comparable across stations with
        # different baseline KGE signs.  Absolute ΔKGE is bounded by [−2, 2].
        assert abs(delta_kge) <= 2.0,      "ΔKGE bounded by KGE range (−∞,1) difference"
        assert abs(old_formula_pct) > 50,  "Old %-of-|Raw| formula inflates the figure"

    def test_validation_metrics_common_years(self):
        """Bug #3: KGE_Raw and KGE_BC must be computed on the same year set."""
        from src.validation.metrics import validation_metrics

        rng = np.random.default_rng(42)
        years_full  = np.arange(1981, 2015)
        years_bc    = np.arange(1986, 2015)  # BC starts later

        def _make_obs():
            rows = []
            for y in years_full:
                rows.append({"station": "500001", "year": int(y),
                             "season": "Annual",
                             "rainfall": float(rng.normal(1000, 100))})
            return pd.DataFrame(rows)

        def _make_mme(years, scenario="historical", dataset="Raw"):
            rows = []
            for y in years:
                rows.append({"station": "500001", "season": "Annual",
                             "scenario": scenario,
                             "year": int(y),
                             "mean": float(rng.normal(1000, 100))})
            return pd.DataFrame(rows)

        obs     = _make_obs()
        raw_mme = _make_mme(years_full)
        bc_mme  = _make_mme(years_bc)

        result = validation_metrics(obs, raw_mme, bc_mme, "Annual")
        assert len(result) == 1
        # n_years must equal the three-way common intersection size
        assert int(result.n_years.values[0]) == len(years_bc), (
            f"Expected {len(years_bc)} common years (obs∩raw∩bc), "
            f"got {result.n_years.values[0]}"
        )

    def test_validation_metrics_has_delta_kge_column(self):
        """Bug #4: result must have ΔKGE column, not KGE_Improvement_%."""
        from src.validation.metrics import validation_metrics
        rng  = np.random.default_rng(7)
        yrs  = np.arange(1990, 2010)
        obs  = pd.DataFrame([{"station": "S1", "year": int(y), "season": "Annual",
                               "rainfall": float(rng.normal(800, 80))} for y in yrs])
        def _mme(yrs):
            return pd.DataFrame([{"station": "S1", "year": int(y), "season": "Annual",
                                  "scenario": "historical",
                                  "mean": float(rng.normal(800, 80))} for y in yrs])
        result = validation_metrics(obs, _mme(yrs), _mme(yrs), "Annual")
        assert "ΔKGE" in result.columns, "Must have ΔKGE column (absolute improvement)"
        assert "KGE_Improvement_%" not in result.columns, (
            "Old KGE_Improvement_% column (divides by |KGE_Raw|) must be removed"
        )


# ===========================================================================
# Bug #5 + #6 — utils/io.py
# ===========================================================================

class TestIO:
    def test_parse_csv_accepts_uppercase_scenario(self):
        """Bug #5: SSP245 (uppercase) must be accepted and normalised to ssp245."""
        from src.utils.io import parse_csv
        r = parse_csv("pr_day_MIROC6_SSP245_r1i1p1f1_2015_2050.csv")
        assert r is not None, "uppercase SSP245 must be accepted"
        assert r["scenario"] == "ssp245", f"scenario must be normalised to lowercase, got {r['scenario']}"

    def test_parse_csv_accepts_lowercase_scenario(self):
        from src.utils.io import parse_csv
        r = parse_csv("pr_day_ACCESS-CM2_ssp585_r1i1p1f1_2015_2050.csv")
        assert r is not None
        assert r["scenario"] == "ssp585"

    def test_parse_csv_rejects_non_matching(self):
        from src.utils.io import parse_csv
        assert parse_csv("rainfall_data.csv") is None
        assert parse_csv("some_random_file.txt") is None

    def test_parse_csv_bc_flag(self):
        from src.utils.io import parse_csv
        r = parse_csv("bc_pr_day_MIROC6_ssp245_r1i1p1f1.csv")
        assert r["dataset"] == "BC"
        r2 = parse_csv("pr_day_MIROC6_ssp245_r1i1p1f1.csv")
        assert r2["dataset"] == "Raw"

    def test_load_metadata_case_insensitive(self, tmp_path):
        """Bug #6: Uppercase 'Station', 'Latitude', etc. must be accepted."""
        xlsx = tmp_path / "meta.xlsx"
        df = pd.DataFrame({
            "Station":   ["500001", "500002"],
            "Latitude":  [11.5, 12.0],
            "Longitude": [99.7, 99.8],
            "Altitude":  [50.0, 80.0],
        })
        df.to_excel(xlsx, index=False)
        from src.utils.io import load_metadata
        result = load_metadata(xlsx)
        assert set(result.columns) == {"station", "lat", "lon", "elevation"}, (
            f"Columns should be normalised; got {list(result.columns)}"
        )
        assert result["station"].tolist() == ["500001", "500002"]

    def test_load_metadata_missing_column_raises(self, tmp_path):
        """Bug #6: Missing required column must raise KeyError (not silent crash later)."""
        xlsx = tmp_path / "bad_meta.xlsx"
        df = pd.DataFrame({"station": ["S1"], "Latitude": [11.0]})  # missing longitude
        df.to_excel(xlsx, index=False)
        from src.utils.io import load_metadata
        with pytest.raises(KeyError, match="missing columns"):
            load_metadata(xlsx)


# ===========================================================================
# Bug #7 — figures/make.py: np.concatenate guard
# ===========================================================================

class TestFigureHelpers:
    def test_collect_vals_empty_meta_returns_empty_arrays(self):
        """Bug #7: _collect_vals must not crash when no stations match meta."""
        from src.figures.make import _collect_vals
        obs = pd.DataFrame({
            "station": ["X1"], "year": [2000], "season": ["Annual"],
            "rainfall": [500.0],
        })
        bc = pd.DataFrame({
            "station": ["X1"], "year": [2000], "season": ["Annual"],
            "scenario": ["historical"], "mean": [500.0], "p25": [400.0], "p75": [600.0],
        })
        # meta has NO matching stations
        meta = pd.DataFrame({"station": ["999"], "lat": [12.0], "lon": [99.9]})
        meta = meta.set_index("station")

        result = _collect_vals(obs, bc, meta, "Annual")
        for key, (xy, vv) in result.items():
            assert vv.size == 0, f"Expected empty vv for key {key}, got {vv}"
            assert xy.shape == (0, 2), f"Expected (0,2) xy for key {key}, got {xy.shape}"

    def test_auto_color_range_empty(self):
        """auto_color_range must not crash with empty array."""
        from src.figures.base import auto_color_range
        lo, hi = auto_color_range(np.array([]))
        assert lo == 0.0 and hi == 1.0

        lo, hi = auto_color_range(np.array([]), diverging=True)
        assert lo == -1.0 and hi == 1.0


# ===========================================================================
# Bug #8 — final_run.py: QC covers TIFF
# ===========================================================================

class TestFigureQC:
    def test_qc_checks_tiff(self, tmp_path):
        """Bug #8: figure_qc must inspect TIFF files, not only PNG."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from final_run import figure_qc

        # Save a 600-DPI PNG and TIFF
        fig, ax = plt.subplots(figsize=(3.5, 3.5))
        ax.plot([1, 2, 3], [1, 2, 3])
        fig.savefig(tmp_path / "test_figure_single.png",  dpi=600)
        fig.savefig(tmp_path / "test_figure_single.tiff", dpi=600)
        # Also create a dummy PDF so pdf_ok passes
        (tmp_path / "test_figure_single.pdf").write_bytes(b"%PDF-1.4")
        plt.close(fig)

        qc, passed = figure_qc(tmp_path, target_dpi=600, min_width_px=100)

        tiff_rows = qc[qc.format == "TIFF"]
        assert len(tiff_rows) >= 1, "TIFF file must be included in QC"
        png_rows  = qc[qc.format == "PNG"]
        assert len(png_rows)  >= 1, "PNG file must be included in QC"

    def test_qc_fails_if_no_png_or_tiff(self, tmp_path):
        """figure_qc returns passed=False when figure directory has no raster files."""
        from final_run import figure_qc
        qc, passed = figure_qc(tmp_path)
        assert not passed


# ===========================================================================
# Bug #10 — Taylor diagram: if False removed, rmax is dynamic
# ===========================================================================

class TestTaylorDiagram:
    def test_taylor_no_if_false_dead_branch(self):
        """Bug #10: figures/make.py must not contain 'if False' literal."""
        make_src = Path(__file__).parent.parent / "src" / "figures" / "make.py"
        text = make_src.read_text()
        assert "if False" not in text, (
            "Dead 'if False' branch still present in figures/make.py"
        )

    def test_taylor_rmax_is_dynamic(self):
        """Bug #10: set_rmax must depend on data, not a hardcoded literal 2.0."""
        make_src = Path(__file__).parent.parent / "src" / "figures" / "make.py"
        text = make_src.read_text()
        # Check that 'set_rmax(2.0)' literal is gone from the Taylor function
        assert "set_rmax(2.0)" not in text, (
            "Hardcoded set_rmax(2.0) still present — rmax should be computed from data"
        )


# ===========================================================================
# free_corner geographic convention (base.py)
# ===========================================================================

class TestFreeCorner:
    def test_north_quadrant_is_image_top(self):
        """
        free_corner: row 0 = geographic NORTH. 'ul' (upper-left in image space)
        = NW in geographic space.  Density should be read from image[:hy, :hx]
        for the NW quadrant.
        """
        from src.figures.base import free_corner
        # mask with land only in the SW corner (image lower-left = geo SW)
        # → NW and NE corners are empty → north label goes to NW
        ny, nx = 100, 100
        mask = np.zeros((ny, nx), dtype=bool)
        mask[50:, :50] = True   # lower-left in image = SW in geo = dense
        bounds = (0.0, 0.0, 1.0, 1.0)
        north_pos, scale_pos, scale_c = free_corner(mask, bounds)

        # North label should go to a position with high y (north) — above midpoint 0.5
        assert north_pos[1] > 0.5, (
            f"North label y={north_pos[1]:.2f} should be in northern (upper) part of map"
        )
        # Scale bar should go to southern part
        assert scale_pos[1] < 0.5, (
            f"Scale bar y={scale_pos[1]:.2f} should be in southern (lower) part of map"
        )


# ===========================================================================
# Integration smoke-test (import chain)
# ===========================================================================

class TestImports:
    def test_all_modules_importable(self):
        """All fixed modules must import without error."""
        import src.rainfall.seasonal   as _s; assert _s
        import src.validation.metrics  as _m; assert _m
        import src.utils.io            as _u; assert _u
        import src.figures.base        as _b; assert _b
        import src.figures.make        as _f; assert _f
        import src.ensemble.mme        as _e; assert _e
        import src.tables.results      as _r; assert _r
        import src.gis.interp          as _g; assert _g

    def test_no_stub_map_panel(self):
        """_map_panel stub (body=pass, dead code) must be removed from make.py."""
        make_src = Path(__file__).parent.parent / "src" / "figures" / "make.py"
        text = make_src.read_text()
        assert "def _map_panel" not in text, (
            "_map_panel stub still present in make.py — it was dead code (body=pass)"
        )
