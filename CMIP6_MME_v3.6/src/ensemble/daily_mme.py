"""ensemble.daily_mme — across-GCM DAILY ensemble mean, exported wide like obs.

Produces a daily multi-model ensemble (MME) rainfall series in the SAME wide
layout as the observed input file (YEAR, MONTH, DAY, <station columns>), one
workbook per dataset (Raw, BC) with one sheet per scenario.

Calendar handling (critical):
  GCMs may use different calendars — e.g. ACCESS-ESM1-5 is Gregorian (has
  29 Feb) while CanESM5 is 365_day/noleap (no 29 Feb).  Models are therefore
  aligned on the (YEAR, MONTH, DAY) KEY, not on row position, and 29 Feb is
  stripped from every model first so all share a common 365-day grid.

Scientific caveat:
  A day-by-day mean across GCMs is a smoothed, "representative" series: daily
  rain events do not co-occur across models, so the ensemble-mean daily field
  damps extremes (wet-day frequency rises, intensity falls).  Use it for
  mean/seasonal-total work and as an observed-like product; do NOT use the
  daily MME mean to study extreme-precipitation indices — use individual
  models (or quantile-based pooling) for those.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)
_ID = ["YEAR", "MONTH", "DAY"]


def _load_daily(path: str, y0: int, y1: int) -> pd.DataFrame:
    """Load one model CSV, drop Unnamed/blank cols and 29 Feb, clip to [y0,y1]."""
    df = pd.read_csv(path)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed")]]
    df = df[~((df.MONTH == 2) & (df.DAY == 29))]            # calendar alignment
    df = df[(df.YEAR >= y0) & (df.YEAR <= y1)]
    return df


def build_daily_mme(files: pd.DataFrame, dataset: str, scenario: str,
                    y0: int, y1: int,
                    stations: list[str] | None = None,
                    ) -> tuple[pd.DataFrame, list[str]]:
    """Across-GCM daily ensemble mean for one (dataset, scenario).

    Parameters
    ----------
    files    : discover_csv() output (columns: dataset, model, scenario, path)
    dataset  : "Raw" or "BC"
    scenario : "historical", "ssp245", …
    y0, y1   : inclusive year window
    stations : optional list of station columns to keep (else common across models)

    Returns
    -------
    (wide_df, models)
        wide_df : YEAR, MONTH, DAY, <station columns> = mean across GCMs
                  (NaN-skipping); empty if no files matched.
        models  : list of distinct model names contributing.
    """
    sel = files[(files.dataset == dataset) & (files.scenario == scenario)]
    if sel.empty:
        return pd.DataFrame(), []

    frames, models = [], []
    for _, r in sel.iterrows():
        d = _load_daily(r.path, y0, y1)
        # Calendar sanity: after Feb-29 strip, a standard/noleap model yields 365
        # days/yr.  A 360_day-calendar model yields ~360 and will NOT align on the
        # (Y,M,D) key (it lacks day-31s). Warn so the user can convert upstream.
        nyr = max(int(d.YEAR.max()) - int(d.YEAR.min()) + 1, 1)
        if abs(len(d) - 360 * nyr) < 5:
            log.warning("build_daily_mme: model '%s' appears to use a 360_day "
                        "calendar; it will not align cleanly on the date grid. "
                        "Convert to a standard calendar upstream.", r.model)
        st = [c for c in d.columns if c not in _ID]
        frames.append(d.set_index(_ID)[st])
        models.append(r.model)

    # Collapse realizations of the same model first (one model, one vote)
    by_model: dict[str, pd.DataFrame] = {}
    for m, f in zip(models, frames):
        by_model[m] = f if m not in by_model else (
            pd.concat([by_model[m], f]).groupby(level=_ID).mean())
    distinct_models = sorted(by_model)

    # Common stations across models (or caller-supplied subset)
    common = set.intersection(*[set(f.columns) for f in by_model.values()])
    cols = [s for s in (stations or sorted(common, key=str)) if s in common]

    # Stack distinct-model series and average across models per (date, station)
    big = pd.concat([by_model[m][cols] for m in distinct_models], axis=0)
    mme = big.groupby(level=_ID).mean()        # mean across models, skips NaN

    mme = (mme.reset_index()
           .sort_values(_ID)
           .reset_index(drop=True))
    log.info("build_daily_mme [%s/%s]: %d days × %d stations | %d models %s",
             dataset, scenario, len(mme), len(cols),
             len(distinct_models), distinct_models)
    return mme, distinct_models


def export_daily_mme_excel(files: pd.DataFrame, out_dir: Path,
                           datasets: list[str], scenarios: list[str],
                           windows: dict[str, tuple[int, int]],
                           area_code: str,
                           stations: list[str] | None = None,
                           ) -> list[Path]:
    """Write ONE self-describing workbook per (dataset, scenario).

    Filename encodes dataset, scenario and the number of GCMs, e.g.
        MME_daily_BC_historical_7GCM_prachuap.xlsx
        MME_daily_Raw_ssp245_7GCM_prachuap.xlsx
    Each workbook has:
        • sheet "INFO"  — dataset, scenario, period, n_models, the exact model
                          names, calendar note, n_days, n_stations, timestamp
        • sheet "data"  — wide daily layout (YEAR, MONTH, DAY, <stations>)
    A manifest CSV (MME_daily_manifest_<area>.csv) lists every file → models.

    The model count in the filename is per (dataset, scenario), because a model
    only contributes where it has data — counts can legitimately differ between
    historical and the SSP scenarios.

    Parameters
    ----------
    windows : {"historical": (b0, b1), "ssp": (ssp_ts0, last_year)} year windows.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    written: list[Path] = []
    manifest_rows: list[dict] = []

    for ds in datasets:
        for scn in scenarios:
            y0, y1 = windows["historical"] if scn == "historical" else windows["ssp"]
            wide, models = build_daily_mme(files, ds, scn, y0, y1, stations)
            if wide.empty:
                log.warning("export_daily_mme_excel: no %s/%s data — skipped", ds, scn)
                continue

            n_models  = len(models)
            n_days    = len(wide)
            n_st      = wide.shape[1] - 3
            yr0, yr1  = int(wide.YEAR.min()), int(wide.YEAR.max())
            period    = "past (historical)" if scn == "historical" else f"future ({scn})"

            info = pd.DataFrame({
                "field": ["dataset", "scenario", "period", "year_start", "year_end",
                          "n_models", "models", "n_days", "n_stations",
                          "value", "units", "calendar", "aggregation", "generated"],
                "value": [ds, scn, period, yr0, yr1,
                          n_models, ", ".join(models), n_days, n_st,
                          "daily precipitation", "mm/day",
                          "365-day (29 Feb removed for cross-GCM alignment)",
                          "across-GCM mean (one model one vote; realizations pre-averaged)",
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            })

            fp = out_dir / f"MME_daily_{ds}_{scn}_{n_models}GCM_{area_code}.xlsx"
            with pd.ExcelWriter(fp) as xw:
                info.to_excel(xw, sheet_name="INFO", index=False)
                wide.to_excel(xw, sheet_name="data", index=False)
            log.info("wrote %s | %d GCM %s | %d days × %d stations",
                     fp.name, n_models, models, n_days, n_st)
            written.append(fp)
            manifest_rows.append({
                "file": fp.name, "dataset": ds, "scenario": scn,
                "period": period, "year_start": yr0, "year_end": yr1,
                "n_models": n_models, "models": ", ".join(models),
                "n_days": n_days, "n_stations": n_st,
            })

    if manifest_rows:
        man = out_dir / f"MME_daily_manifest_{area_code}.csv"
        pd.DataFrame(manifest_rows).to_csv(man, index=False)
        log.info("wrote manifest %s (%d files)", man.name, len(manifest_rows))
        written.append(man)

    return written
