"""
rta.aggregation — Temporal aggregation and descriptive statistics.

aggregate_all() and descriptive_stats() extracted verbatim from
rainfall_trend_analysis_v3.py §2 (lines 251–311).
validate_dry_season() is a new addition for v4.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import math
import warnings
from pathlib import Path

# ── Scientific stack ──────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from scipy import stats as sps

# ── Package config ────────────────────────────────────────────────────────────
from .config import WET_THR, WET_MONTHS, DRY_MONTHS, MIN_N


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §2a  Temporal aggregation                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def aggregate_all(df: pd.DataFrame) -> dict:
    """
    Aggregate daily rainfall to four temporal scales.

    Scales returned
    ---------------
    "annual"      — Calendar-year totals (Jan–Dec).  YS resample with
                    min_count = 80 % of days in each year.
    "wet"         — Wet-season totals (May–Oct).  Days filtered to
                    WET_MONTHS then YS-resampled with the same 80 % rule.
    "dry"         — Dry-season totals (Nov–Apr), using a hydrological-year
                    approach: Nov/Dec of year Y are shifted to year Y+1 so
                    each 6-month block (Nov Y → Apr Y+1) is labelled Y+1.
                    YS resample with 80 % min_count applied after the shift.
    "monthly_all" — Full monthly-total time series (MS resample, 80 % rule).

    Parameters
    ----------
    df : pd.DataFrame
        Daily rainfall with DatetimeIndex and station columns (from load_daily).

    Returns
    -------
    dict with keys "annual", "wet", "dry", "monthly_all".
    """
    scales = {}

    # ── Annual (Jan–Dec) ──────────────────────────────────────────────────
    scales["annual"] = df.resample("YS").apply(
        lambda g: g.sum(min_count=int(0.8 * len(g)))
    )

    # ── Wet season (May–Oct) ──────────────────────────────────────────────
    wet = df[df.index.month.isin(WET_MONTHS)]
    scales["wet"] = wet.resample("YS").apply(
        lambda g: g.sum(min_count=int(0.8 * len(g)))
    )

    # ── Dry season (Nov–Apr) — hydrological year approach ─────────────────
    # Nov/Dec of year Y are shifted to year Y+1 so the six months form a
    # continuous block labelled with the ending calendar year.
    dry_raw   = df[df.index.month.isin(DRY_MONTHS)].copy()
    late_mask = dry_raw.index.month.isin([11, 12])
    new_idx   = [
        d.replace(year=d.year + 1) if m else d
        for d, m in zip(dry_raw.index.to_list(), late_mask)
    ]
    dry_raw.index = pd.DatetimeIndex(new_idx)
    scales["dry"] = dry_raw.resample("YS").apply(
        lambda g: g.sum(min_count=int(0.8 * len(g)))
    )

    # Null out blocks that do not contain all 6 required months (Nov–Apr).
    # Boundary blocks at the data start/end are incomplete (e.g. Jan–Apr only
    # at the start, or Nov–Dec only at the end) and must not enter MK analysis.
    _dry_required = frozenset([11, 12, 1, 2, 3, 4])
    _month_cov = (dry_raw.groupby(dry_raw.index.year)
                  .apply(lambda g: frozenset(g.index.month.tolist())))
    _incomplete = [yr for yr in scales["dry"].index.year
                   if _month_cov.get(yr, frozenset()) != _dry_required]
    if _incomplete:
        scales["dry"].loc[scales["dry"].index.year.isin(_incomplete)] = np.nan

    # ── Monthly climatology (full monthly total series) ───────────────────
    monthly_all = df.resample("MS").apply(
        lambda g: g.sum(min_count=int(0.8 * len(g)))
    )
    scales["monthly_all"] = monthly_all

    return scales


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §2b  Descriptive statistics                                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def descriptive_stats(scales: dict, df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptive statistics for the annual time series.

    Statistics computed per station
    --------------------------------
    N (yr)       — number of non-missing annual values
    Mean (mm)    — arithmetic mean of annual totals
    Median (mm)  — median of annual totals
    Max (mm)     — maximum annual total
    Min (mm)     — minimum annual total
    Std (mm)     — sample standard deviation (ddof=1)
    CV (%)       — coefficient of variation (Std / Mean × 100)
    Wet-days/yr  — mean number of wet days per year (daily ≥ WET_THR mm)
    Skewness     — Fisher–Pearson skewness of annual totals
    Kurtosis     — excess kurtosis of annual totals (Fisher definition)

    Parameters
    ----------
    scales   : dict      Output of aggregate_all(); must contain "annual".
    df_daily : pd.DataFrame  Original daily data (DatetimeIndex) from load_daily.

    Returns
    -------
    pd.DataFrame indexed by Station with one row per station.
    """
    ann  = scales["annual"]
    stns = ann.columns.tolist()
    rows = []

    for s in stns:
        v = ann[s].dropna().values.astype(float)
        d = df_daily[s].dropna()
        w = d[d >= WET_THR]
        n = len(v)
        rows.append({
            "Station":     s,
            "N (yr)":      n,
            "Mean (mm)":   round(float(np.mean(v)), 1)               if n > 0 else np.nan,
            "Median (mm)": round(float(np.median(v)), 1)             if n > 0 else np.nan,
            "Max (mm)":    round(float(np.max(v)), 1)                if n > 0 else np.nan,
            "Min (mm)":    round(float(np.min(v)), 1)                if n > 0 else np.nan,
            "Std (mm)":    round(float(np.std(v, ddof=1)), 1)        if n > 1 else np.nan,
            "CV (%)":      round(float(np.std(v, ddof=1) / np.mean(v) * 100), 1)
                           if n > 1 and np.mean(v) != 0 else np.nan,
            "Wet-days/yr": round(float(len(w) / n), 1)               if n > 0 else np.nan,
            "Skewness":    round(float(sps.skew(v)), 3)               if n > 3 else np.nan,
            "Kurtosis":    round(float(sps.kurtosis(v, fisher=True)), 3) if n > 3 else np.nan,
        })

    return pd.DataFrame(rows).set_index("Station")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  §2c  Dry-season validation                                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def validate_dry_season(scales: dict, out_path: Path = None) -> dict:
    """
    Validate the dry-season hydrological year shift in ``scales["dry"]``.

    Checks performed
    ----------------
    1. No duplicate years in the dry-season index (would indicate a
       programming error in the Nov/Dec shift).
    2. Year sequence is strictly monotonic (no gaps or reversals).
    3. Each year's block index contains only valid year integers (sanity
       check that shifted dates did not produce nonsensical years).

    Diagnostic output
    -----------------
    Prints a table with columns:
        HydroYear | N_values | Completeness | Status

    If *out_path* is provided the same text is written to that file.

    Parameters
    ----------
    scales   : dict   Output of aggregate_all(); must contain "dry".
    out_path : Path, optional
               If given, diagnostic text is written to this file.

    Returns
    -------
    dict with keys:
        "valid"    : bool   — True if all checks passed
        "years"    : list   — sorted list of hydrological years found
        "n_blocks" : int    — total number of year blocks
        "errors"   : list   — list of error message strings (empty if valid)

    Raises
    ------
    RuntimeError
        If duplicate years are detected (check 1 fails).
    """
    dry_df = scales["dry"]

    # Extract integer years from the DatetimeIndex
    years_raw = dry_df.index.year.tolist()

    # ── Check 1: No duplicates ────────────────────────────────────────────
    seen = set()
    duplicates = []
    for y in years_raw:
        if y in seen:
            duplicates.append(y)
        seen.add(y)

    if duplicates:
        raise RuntimeError(
            f"validate_dry_season: duplicate hydrological years detected: "
            f"{sorted(set(duplicates))}.  The Nov/Dec shift in aggregate_all() "
            f"may have produced overlapping year labels."
        )

    years_sorted = sorted(set(years_raw))
    n_blocks     = len(years_sorted)
    errors       = []

    # ── Check 2: Strictly monotonic sequence ─────────────────────────────
    for i in range(1, len(years_sorted)):
        if years_sorted[i] <= years_sorted[i - 1]:
            errors.append(
                f"Year sequence not strictly monotonic between "
                f"{years_sorted[i-1]} and {years_sorted[i]}."
            )

    # ── Check 3: Valid year integers in each block ────────────────────────
    for y in years_sorted:
        if not isinstance(y, (int, np.integer)) or y < 1900 or y > 2200:
            errors.append(
                f"Suspicious year value in dry-season index: {y!r}.  "
                f"Expected an integer in [1900, 2200]."
            )

    # ── Check 4: All included blocks must have all 6 required months ─────
    _dry_required = frozenset([11, 12, 1, 2, 3, 4])
    # Count non-NaN stations per year; a year with 0 non-NaN stations is excluded.
    stns = dry_df.columns.tolist()
    for y in years_sorted:
        row_mask = dry_df.index.year == y
        sub      = dry_df.loc[row_mask]
        if len(sub) > 0 and stns:
            non_nan = int(sub[stns].notna().any(axis=0).sum())
            if non_nan == len(stns):
                pass  # full block with data — accepted
            elif non_nan > 0:
                # Partial data: some stations NaN, some not — warn
                errors.append(
                    f"Year {y}: mixed NaN coverage ({non_nan}/{len(stns)} stations "
                    f"non-NaN). Possible partial season escaped the completeness filter."
                )
            # non_nan == 0 means block was correctly nulled by aggregate_all()

    valid = len(errors) == 0

    # ── Build diagnostic table ────────────────────────────────────────────
    lines = []
    lines.append("=" * 68)
    lines.append("  Dry-Season Hydrological Year Validation")
    lines.append("=" * 68)

    # Count full (non-NaN) blocks
    full_years = []
    excl_years = []
    for y in years_sorted:
        row_mask = dry_df.index.year == y
        sub      = dry_df.loc[row_mask]
        nn = int(sub[stns].notna().any(axis=0).sum()) if len(sub) > 0 and stns else 0
        if nn > 0:
            full_years.append(y)
        else:
            excl_years.append(y)

    lines.append(f"  Total blocks  : {n_blocks}  "
                 f"(full: {len(full_years)}, excluded: {len(excl_years)})")
    lines.append(f"  Full range    : {full_years[0] if full_years else 'n/a'}"
                 f" – {full_years[-1] if full_years else 'n/a'}")
    lines.append(f"  Excluded      : {excl_years if excl_years else 'none'}")
    lines.append(f"  Status        : {'PASS' if valid else 'FAIL'}")
    lines.append("-" * 68)
    lines.append(f"  {'HydroYear':>10}  {'N_rows':>7}  {'NonNaN_stns':>12}  {'Status':>8}")
    lines.append("-" * 68)

    for y in years_sorted:
        row_mask = dry_df.index.year == y
        sub      = dry_df.loc[row_mask]
        n_vals   = sub.shape[0]
        if n_vals > 0 and stns:
            non_nan = int(sub[stns].notna().any(axis=0).sum())
        else:
            non_nan = 0
        pct    = f"{non_nan}/{len(stns)}" if stns else "n/a"
        status = "OK" if non_nan > 0 else "EXCL"
        lines.append(f"  {y:>10}  {n_vals:>7}  {pct:>12}  {status:>8}")

    lines.append("-" * 68)
    if errors:
        lines.append("  ERRORS:")
        for err in errors:
            lines.append(f"    • {err}")
    else:
        lines.append("  All checks passed.")
    lines.append("=" * 68)

    diag_text = "\n".join(lines)
    print(diag_text)

    # ── Write to file if requested ────────────────────────────────────────
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(diag_text + "\n")

    return {
        "valid":    valid,
        "years":    years_sorted,
        "n_blocks": n_blocks,
        "errors":   errors,
    }
