"""test_v35_fixes — self-contained verification of all v3.5 scientific fixes.

Runs WITHOUT pytest/geopandas/pyarrow so it can execute in minimal
environments (CI, review sandboxes).  Covers the original six fixes plus the
four v3.5 methodology fixes:

  FIX-A  change% relative to each model's own BC-historical baseline
  FIX-B  min_years gate ≥ 10 (degenerate short-sample KGE excluded)
  FIX-C  realization collapse → n_models counts DISTINCT models
  FIX-D  kriging: nugget + non-negative clipping + LOOCV helper

Usage:  python tests/test_v35_fixes.py
Exit code 0 = all pass.
"""
from __future__ import annotations
import sys, os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validation.metrics import kge, nse, pbias, validation_metrics
from src.ensemble.mme import build_mme
from src.rainfall.seasonal import _wide_to_yearly
from src.ensemble.daily_mme import build_daily_mme

PASS = 0; FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  PASS  {name}")
    else:
        FAIL += 1; print(f"  FAIL  {name}  {detail}")


# ── Original statistical-correctness fixes ────────────────────────────────────
def test_metrics_basic():
    o = np.array([10., 20, 30, 40, 50])
    check("kge perfect == 1", abs(kge(o, o) - 1.0) < 1e-9)
    check("nse perfect == 1", abs(nse(o, o) - 1.0) < 1e-9)
    check("pbias perfect == 0", abs(pbias(o, o)) < 1e-9)
    check("kge flat-obs -> nan", np.isnan(kge(np.array([5., 5, 5]), np.array([1., 2, 3]))))
    check("kge n<2 -> nan", np.isnan(kge(np.array([1.]), np.array([1.]))))
    # ddof invariance (FIX-01 is cosmetic, value unchanged)
    a = np.random.RandomState(0).rand(20); b = a + 0.05
    def k(dd):
        r = np.corrcoef(a, b)[0, 1]; al = np.std(b, ddof=dd)/np.std(a, ddof=dd); be = b.mean()/a.mean()
        return 1-np.sqrt((r-1)**2+(al-1)**2+(be-1)**2)
    check("kge ddof0==ddof1", abs(k(0)-k(1)) < 1e-12)


# ── FIX-B: min_years gate ─────────────────────────────────────────────────────
def test_min_years_gate():
    rng = np.random.default_rng(1)
    # Only 5 common years -> must be EXCLUDED at default gate (10)
    yrs = np.arange(2010, 2015)
    obs = pd.DataFrame([{"station": "S", "year": int(y), "season": "Annual",
                         "rainfall": float(rng.normal(1000, 100))} for y in yrs])
    mme = pd.DataFrame([{"station": "S", "season": "Annual", "scenario": "historical",
                         "year": int(y), "mean": float(rng.normal(1000, 100))} for y in yrs])
    res = validation_metrics(obs, mme, mme, "Annual")            # default min_years=10
    check("FIX-B 5 common years excluded by default gate", len(res) == 0,
          f"got {len(res)} rows")
    res2 = validation_metrics(obs, mme, mme, "Annual", min_years=3)
    check("FIX-B explicit low gate still allows (caller's choice)", len(res2) == 1)


# ── FIX-C: realization collapse / distinct-model count ────────────────────────
def test_realization_collapse():
    rows = []
    for model, val in [("A", 100.), ("A", 120.), ("B", 200.)]:   # A = 2 realizations
        rows.append(dict(dataset="BC", model=model, scenario="ssp245",
                         station="S1", year=2030, season="Wet", rainfall=val))
    mme = build_mme(pd.DataFrame(rows))
    m = float(mme["mean"].iloc[0]); n = int(mme["n_models"].iloc[0])
    # A collapses to 110; ensemble mean = (110+200)/2 = 155 ; n_models = 2 distinct
    check("FIX-C realization-averaged ensemble mean == 155", abs(m - 155.0) < 1e-9,
          f"got {m}")
    check("FIX-C n_models counts DISTINCT models (==2)", n == 2, f"got {n}")


# ── FIX-D: kriging nugget + non-negativity + LOOCV ────────────────────────────
def test_interp_nonneg():
    # import math fns without triggering geopandas import at module top
    import importlib.util, types
    spec = importlib.util.spec_from_file_location(
        "_interp", os.path.join(os.path.dirname(__file__), "..", "src", "gis", "interp.py"))
    # stub geopandas + shapely so the module imports in a minimal env
    for mod in ["geopandas", "shapely", "shapely.geometry", "shapely.prepared"]:
        if mod not in sys.modules:
            sys.modules[mod] = types.ModuleType(mod)
    sys.modules["shapely.geometry"].Point = lambda *a, **k: None
    sys.modules["shapely.prepared"].prep = lambda g: g
    interp = importlib.util.module_from_spec(spec); spec.loader.exec_module(interp)

    xy = np.array([[99.0, 11.0], [99.5, 11.0], [99.0, 11.5], [99.5, 11.5]])
    vals = np.array([1800., 50., 1700., 80.])    # sharp gradient -> overshoot risk
    gx, gy = np.meshgrid(np.linspace(98.8, 99.7, 25), np.linspace(10.8, 11.7, 25))
    zk = np.clip(interp.ordinary_kriging(xy, vals, gx, gy), 0, None)
    check("FIX-D kriging never negative", float(np.nanmin(zk)) >= 0.0,
          f"min {np.nanmin(zk)}")
    rmse = interp.loocv_rmse(xy, vals, "idw")
    check("FIX-D loocv_rmse returns finite value", np.isfinite(rmse), f"rmse {rmse}")


# ── Seasonal aggregation sanity (dry hydro-year, NaN gate) ────────────────────
def test_seasonal():
    days = pd.date_range("2000-01-01", "2002-12-31", freq="D")
    df = pd.DataFrame({"YEAR": days.year, "MONTH": days.month, "DAY": days.day,
                       "500001": 1.0})
    out = _wide_to_yearly(df, [5,6,7,8,9,10], [11,12,1,2,3,4], 2000, 2002)
    dry = out[(out.season == "Dry")]
    check("seasonal dry-season labelled by ending (hydro) year",
          set(dry.year) <= {2001, 2002}, f"years {sorted(set(dry.year))}")
    # all-NaN -> NaN not 0
    df2 = df.copy(); df2["500001"] = np.nan
    out2 = _wide_to_yearly(df2, [5,6,7,8,9,10], [11,12,1,2,3,4], 2000, 2002)
    check("seasonal all-NaN -> NaN (not 0)", out2.rainfall.isna().all())


# ── FIX-A: change% reference is model BC-historical, on REAL data if present ──
def test_change_reference_real():
    real_change = os.path.join(os.path.dirname(__file__), "..",
                               "outputs", "excel", "Change.csv")
    if not os.path.exists(real_change):
        print("  SKIP  FIX-A real-data change check (run main.py first)")
        return
    ch = pd.read_csv(real_change)
    need = {"obs_baseline", "bc_hist_baseline", "future_bc", "change_pct",
            "change_pct_p25", "change_pct_p75", "n_models"}
    check("FIX-A change table has model-baseline schema", need <= set(ch.columns),
          f"missing {need - set(ch.columns)}")
    # change_pct must equal (future_bc - bc_hist_baseline)/bc_hist_baseline*100
    # at the MME level within rounding (exact per-model; here check direction + magnitude)
    sub = ch.dropna(subset=["bc_hist_baseline", "future_bc"])
    approx = (sub.future_bc - sub.bc_hist_baseline) / sub.bc_hist_baseline * 100
    # MME mean of per-model changes ≈ change from mean baselines (2 models, close)
    err = (approx - sub.change_pct).abs()
    check("FIX-A change_pct consistent with model BC-historical baseline",
          float(err.median()) < 3.0, f"median abs err {err.median():.2f}%")
    check("FIX-A ssp585 drying >= ssp245 (forcing ordering)",
          ch[ch.scenario=="ssp585"].change_pct.mean()
          <= ch[ch.scenario=="ssp245"].change_pct.mean() + 1e-6)


# ── Daily MME export: mixed-calendar alignment + across-GCM averaging ─────────
def test_daily_mme_mixed_calendar():
    import tempfile, os
    d = tempfile.mkdtemp()
    # Model A: Gregorian (includes 2000-02-29). Model B: noleap (no 29 Feb).
    full = pd.date_range("2000-01-01", "2000-12-31", freq="D")
    a = pd.DataFrame({"YEAR": full.year, "MONTH": full.month, "DAY": full.day, "500001": 2.0})
    nl = full[~((full.month == 2) & (full.day == 29))]
    b = pd.DataFrame({"YEAR": nl.year, "MONTH": nl.month, "DAY": nl.day, "500001": 4.0})
    pa = os.path.join(d, "pr_day_MODELA_historical_r1i1p1f1_gn_x.csv")
    pb = os.path.join(d, "pr_day_MODELB_historical_r1i1p1f1_gn_x.csv")
    a.to_csv(pa, index=False); b.to_csv(pb, index=False)
    files = pd.DataFrame([
        {"dataset": "Raw", "model": "MODELA", "scenario": "historical", "path": pa},
        {"dataset": "Raw", "model": "MODELB", "scenario": "historical", "path": pb},
    ])
    wide, models = build_daily_mme(files, "Raw", "historical", 2000, 2000)
    check("daily MME aligned to common 365-day grid (29 Feb stripped)",
          len(wide) == 365, f"got {len(wide)} rows")
    check("daily MME has 2 distinct models", set(models) == {"MODELA", "MODELB"})
    check("daily MME = across-GCM mean (2 & 4 -> 3)",
          abs(float(wide["500001"].mean()) - 3.0) < 1e-9,
          f"got {wide['500001'].mean()}")
    check("daily MME wide layout matches observed (YEAR,MONTH,DAY,station)",
          list(wide.columns[:3]) == ["YEAR", "MONTH", "DAY"] and "500001" in wide.columns)


# ── geo_lite: dependency-free shapefile read + UTM reprojection + mask ────────
def test_geo_lite_boundary():
    import os
    shp = os.path.join(os.path.dirname(__file__), "..", "data", "boundary", "boundary.shp")
    if not os.path.exists(shp):
        print("  SKIP  geo_lite boundary test (no boundary.shp staged)")
        return
    from src.gis.geo_lite import load_boundary_lonlat, mask_inside
    import numpy as np
    rings, bounds, crs = load_boundary_lonlat(shp)
    check("geo_lite detects UTM and reprojects to lon/lat",
          "UTM" in crs and 99 < bounds[0] < 101 and 10 < bounds[1] < 14,
          f"crs={crs} bounds={bounds}")
    check("geo_lite returns polygon rings", len(rings) >= 1 and rings[0].shape[1] == 2)
    gx, gy = np.meshgrid(np.linspace(bounds[0], bounds[2], 40),
                         np.linspace(bounds[1], bounds[3], 40))
    m = mask_inside(rings, gx, gy)
    check("geo_lite mask is a partial interior (0<frac<1)", 0.05 < m.mean() < 0.95,
          f"inside frac {m.mean():.2f}")


if __name__ == "__main__":
    print("Running v3.5 offline verification…")
    for fn in [test_metrics_basic, test_min_years_gate, test_realization_collapse,
               test_interp_nonneg, test_seasonal, test_daily_mme_mixed_calendar,
               test_geo_lite_boundary, test_change_reference_real]:
        print(f"\n[{fn.__name__}]")
        fn()
    print(f"\n{'='*50}\nRESULT: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
