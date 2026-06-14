"""ensemble.mme — Raw MME & BC-MME statistics (mean/median/P25/P75/n_models).

MME = Multi-Model Ensemble summary across all models for a given
dataset × scenario × station × year × season combination.

Realization handling (v3.5, FIX-C):
  CMIP6 models may contribute multiple realizations (r1i1p1f1, r2i1p1f1, …).
  To enforce the "one model, one vote" convention and prevent models with
  more realizations from dominating the ensemble, realizations of the SAME
  model are first averaged to a single per-model series, AFTER which the
  ensemble statistics are computed across distinct models.  Consequently
  `n_models` counts DISTINCT models, not realization files.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def build_mme(per_model: pd.DataFrame) -> pd.DataFrame:
    """Compute ensemble statistics across distinct models.

    Parameters
    ----------
    per_model : DataFrame with columns:
        dataset, model, scenario, station, year, season, rainfall
        (an optional `realization` column is collapsed first if present)

    Returns
    -------
    DataFrame with columns:
        dataset, scenario, station, year, season,
        mean, median, p25, p75, n_models
        where n_models = number of DISTINCT models contributing a finite value.
    """
    keys      = ["dataset", "scenario", "station", "year", "season"]
    model_key = keys + ["model"]

    # ── Stage 1: collapse realizations → one value per (model, key) ───────────
    # mean() skips NaN; a model with several realizations becomes one series.
    per_model = (per_model
                 .groupby(model_key, as_index=False)["rainfall"]
                 .mean())

    # ── Stage 2: ensemble statistics across DISTINCT models ───────────────────
    g = per_model.groupby(keys)["rainfall"]

    out = g.agg(
        mean     = "mean",
        median   = "median",
        p25      = lambda s: float(np.percentile(s.dropna(), 25)) if s.notna().any() else np.nan,
        p75      = lambda s: float(np.percentile(s.dropna(), 75)) if s.notna().any() else np.nan,
        n_models = lambda s: int(s.notna().sum()),   # distinct models w/ finite value
    ).reset_index()

    log.info("build_mme: %d rows | datasets=%s | scenarios=%s | n_models max=%d "
             "(distinct models, realizations pre-averaged)",
             len(out),
             sorted(out.dataset.unique()),
             sorted(out.scenario.unique()),
             int(out.n_models.max()) if len(out) else 0)
    return out
