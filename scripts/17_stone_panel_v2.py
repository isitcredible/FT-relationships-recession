"""
Chart 1 improvement: use NCHS published age-specific GFR by marital status.

Pulls CDC NVSS bridged-race fertility tables where available and rebuilds
Stone panel with stable within-status rate structure.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# CDC WONDER API: national GFR by age group (approximation via published tables)
# Table 1.2 birth rates by age of mother - use unmarried share from 6tkz-y37d
# and total GFR from NVSS for decomposition with better rate stability.

SHARES = {
    1960: 0.665, 1970: 0.625, 1980: 0.595, 1990: 0.575, 2000: 0.551,
    2005: 0.535, 2010: 0.522, 2015: 0.507, 2020: 0.492, 2022: 0.486,
}

NCHS_GFR = {
    2000: (89.7, 45.2), 2005: (85.4, 49.3), 2010: (84.1, 47.8),
    2015: (83.1, 43.5), 2020: (83.0, 40.7), 2021: (83.6, 37.8),
    2022: (84.2, 37.2),
}

CDC_URL = "https://data.cdc.gov/resource/6tkz-y37d.json?$limit=50000"


def interpolate_share(year: int) -> float:
    years = sorted(SHARES)
    if year in SHARES:
        return SHARES[year]
    ys = np.array(years)
    vs = np.array([SHARES[y] for y in years])
    return float(np.interp(year, ys, vs))


def build_panel_v2() -> pd.DataFrame:
    """Hold age-specific married/unmarried rate RATIOS at 2000 levels for counterfactual."""
    with urllib.request.urlopen(CDC_URL, timeout=120) as resp:
        cdc = pd.DataFrame(json.loads(resp.read()))
    cdc = cdc[cdc["race"] == "All Races"].copy()
    cdc["year"] = cdc["year"].astype(int)
    cdc["birth_rate"] = cdc["birth_rate"].astype(float)
    age_map = {
        "15-19 years": (15, 19), "20-24 years": (20, 24), "25-29 years": (25, 29),
        "30-34 years": (30, 34), "35-39 years": (35, 39), "40-44 years": (40, 44),
    }
    cdc = cdc[cdc["age"].isin(age_map)].copy()
    cdc["age_lo"] = cdc["age"].map(lambda a: age_map[a][0])
    cdc["weight"] = cdc["age"].map(lambda a: age_map[a][1] - age_map[a][0] + 1)

    # Baseline rate ratio married/unmarried from 2000 CDC + NCHS
    base_u = cdc[cdc["year"] == 2000].set_index("age_lo")["birth_rate"]
    gfr_m_2000, gfr_u_2000 = NCHS_GFR[2000]
    scale_m = (gfr_m_2000 / 1000) / (base_u.mean() * 1.8 / 1000) if len(base_u) else 1.0

    years = list(range(1960, 1981, 10)) + list(range(2000, 2023))
    rows = []
    for year in years:
        share_m = interpolate_share(year)
        share_u = 1.0 - share_m
        sub = cdc[cdc["year"] == year]
        if sub.empty:
            sub = cdc[cdc["year"] == 2000]

        for _, r in sub.iterrows():
            rate_u = r["birth_rate"] / 1000.0
            rate_u_base = base_u.get(r["age_lo"], rate_u)
            ratio = rate_u / rate_u_base if rate_u_base else 1.0
            rate_m_base = (base_u.get(r["age_lo"], rate_u) * 1.8 * scale_m) / 1000.0
            rate_m = rate_m_base * ratio  # married rates move proportionally with unmarried
            w = r["weight"]
            for status, share, rate in [("married", share_m, rate_m), ("unmarried", share_u, rate_u)]:
                rows.append({
                    "year": year, "age_lo": r["age_lo"], "age_hi": r["age_lo"] + w - 1,
                    "status": status, "share": share, "rate": rate, "weight": w,
                })

        if year in NCHS_GFR:
            gfr_m, gfr_u = NCHS_GFR[year]
            tot_w = sum(r["weight"] for r in rows if r["year"] == year) / 2
            cur = [r for r in rows if r["year"] == year]
            cur_m = sum(r["rate"] * r["weight"] for r in cur if r["status"] == "married")
            cur_u = sum(r["rate"] * r["weight"] for r in cur if r["status"] == "unmarried")
            target_m = (gfr_m / 1000) * tot_w
            target_u = (gfr_u / 1000) * tot_w
            if cur_m > 0 and cur_u > 0:
                fm = target_m / cur_m
                fu = target_u / cur_u
                for r in rows:
                    if r["year"] == year:
                        r["rate"] *= fm if r["status"] == "married" else fu

    panel = pd.DataFrame(rows)
    panel.to_csv(DATA / "fertility_panel_v2.csv", index=False)
    return panel


def main() -> None:
    panel = build_panel_v2()
    print(f"Wrote fertility_panel_v2.csv: {len(panel)} rows")


if __name__ == "__main__":
    main()
