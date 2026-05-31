"""ensemble.mme — Raw MME & BC-MME statistics (mean/median/P25/P75/n_models).

MME = Multi-Model Ensemble summary across all models for a given
dataset × scenario × station × year × season combination.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def build_mme(per_model: pd.DataFrame) -> pd.DataFrame:
    """Compute ensemble statistics across models.

    Parameters
    ----------
    per_model : DataFrame with columns:
        dataset, model, scenario, station, year, season, rainfall

    Returns
    -------
    DataFrame with columns:
        dataset, scenario, station, year, season,
        mean, median, p25, p75, n_models
    """
    keys = ["dataset", "scenario", "station", "year", "season"]
    g = per_model.groupby(keys)["rainfall"]

    out = g.agg(
        mean     = "mean",
        median   = "median",
        p25      = lambda s: float(np.percentile(s.dropna(), 25)) if s.notna().any() else np.nan,
        p75      = lambda s: float(np.percentile(s.dropna(), 75)) if s.notna().any() else np.nan,
        n_models = "count",
    ).reset_index()

    log.info("build_mme: %d rows | datasets=%s | scenarios=%s | n_models max=%d",
             len(out),
             sorted(out.dataset.unique()),
             sorted(out.scenario.unique()),
             int(out.n_models.max()) if len(out) else 0)
    return out
