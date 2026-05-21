"""
Lyman Stone / FT counterfactual TFR decomposition.

Counterfactual holds partnership-status shares at baseline while allowing
age-specific fertility within status to evolve (Actual allows both to move).

TFR(t) = sum_{a,s} w_a * share_{s|a,t} * rate_{a,s,t}

where rate is age-specific general fertility contribution within status s,
share is fraction of women age a in status s, w_a are age weights (5-year bands).

Cumulative pct change from baseline year b:
  100 * (TFR(t) / TFR(b) - 1)
"""
from __future__ import annotations

import pandas as pd


def compute_tfr(panel: pd.DataFrame, year: int, share_col: str = "share") -> float:
    sub = panel[panel["year"] == year]
    return (sub["weight"] * sub[share_col] * sub["rate"]).sum()


def decomposition_series(
    panel: pd.DataFrame,
    baseline_year: int,
    years: list[int],
    actual_share_col: str = "share",
    baseline_share_col: str = "share_baseline",
) -> pd.DataFrame:
    tfr_base = compute_tfr(panel, baseline_year, actual_share_col)
    rows = []
    for year in years:
        tfr_act = compute_tfr(panel, year, actual_share_col)
        tfr_cf = compute_tfr(panel, year, baseline_share_col)
        rows.append({
            "year": year,
            "Actual": 100.0 * (tfr_act / tfr_base - 1),
            "Counterfactual": 100.0 * (tfr_cf / tfr_base - 1),
        })
    return pd.DataFrame(rows)


def to_ft_long(df: pd.DataFrame, facet: str) -> pd.DataFrame:
    out = df.melt(id_vars=["year"], var_name="series", value_name="value")
    out.insert(0, "facet", facet)
    return out
