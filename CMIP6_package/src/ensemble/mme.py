"""ensemble.mme — Raw MME & BC-MME (mean/median/P25/P75). MME = summary, not a member."""
from __future__ import annotations
import logging, numpy as np, pandas as pd
log=logging.getLogger(__name__)

def build_mme(per_model: pd.DataFrame):
    """per_model: [dataset,model,scenario,station,year,season,rainfall] → ensemble stats (across models)."""
    keys=["dataset","scenario","station","year","season"]
    g=per_model.groupby(keys)["rainfall"]
    out=g.agg(mean="mean",median="median",
              p25=lambda s:np.percentile(s,25),p75=lambda s:np.percentile(s,75),
              n_models="count").reset_index()
    return out
