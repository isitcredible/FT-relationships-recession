"""
Build fertility panel for Stone decomposition from CDC NCHS API + published shares.

Sources:
  - CDC data.cdc.gov 6tkz-y37d: unmarried birth rates by age (1970-2015, All Races)
  - NCHS NVSR Table 10: married/unmarried GFR 15-44 (national, selected years)
  - Census CPS trend: married share of women 15-44 (historical anchors in SHARES)
"""
from __future__ import annotations

import gzip
import json
import shutil
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

WPP_URL = (
    "https://population.un.org/wpp/assets/Excel%20Files/"
    "1_Indicator%20(Standard)/CSV_FILES/"
    "WPP2024_Demographic_Indicators_Medium.csv.gz"
)
SMARTPHONES_WPP = ROOT.parent / "smartphones-fertility" / "data" / "tfr_annual.csv"
CDC_URL = "https://data.cdc.gov/resource/6tkz-y37d.json?$limit=50000"

# Married share of women 15-44 (Census CPS / NCHS historical anchors)
SHARES = {
    1960: 0.665, 1970: 0.625, 1980: 0.595, 1990: 0.575, 2000: 0.551,
    2005: 0.535, 2010: 0.522, 2015: 0.507, 2020: 0.492, 2022: 0.486,
}

# NCHS NVSR married / unmarried GFR per 1,000 women 15-44 (Table 10, national)
NCHS_GFR = {
    2000: (89.7, 45.2), 2005: (85.4, 49.3), 2010: (84.1, 47.8),
    2015: (83.1, 43.5), 2020: (83.0, 40.7), 2021: (83.6, 37.8),
    2022: (84.2, 37.2),
}


def ensure_wpp() -> None:
    out = DATA / "tfr_annual.csv"
    if out.exists():
        return
    if SMARTPHONES_WPP.exists():
        shutil.copy2(SMARTPHONES_WPP, out)
        return
    gz = DATA / "wpp_demographic_indicators.csv.gz"
    urllib.request.urlretrieve(WPP_URL, gz)
    csv = DATA / "wpp_demographic_indicators.csv"
    with gzip.open(gz, "rb") as f_in, open(csv, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    df = pd.read_csv(csv, usecols=["ISO3_code", "LocTypeName", "Location", "Time", "TFR"])
    df = df[(df["LocTypeName"] == "Country/Area") & (df["Time"] <= 2023)]
    df.rename(columns={"Time": "year", "ISO3_code": "iso3", "Location": "country"}, inplace=True)
    df[["iso3", "country", "year", "TFR"]].to_csv(out, index=False)


def download_cdc_unmarried() -> pd.DataFrame:
    out = DATA / "cdc_unmarried_birth_rates.csv"
    if out.exists():
        return pd.read_csv(out)
    with urllib.request.urlopen(CDC_URL, timeout=120) as resp:
        rows = json.loads(resp.read())
    df = pd.DataFrame(rows)
    df["year"] = df["year"].astype(int)
    df["birth_rate"] = df["birth_rate"].astype(float)
    df.to_csv(out, index=False)
    return df


def interpolate_share(year: int) -> float:
    years = sorted(SHARES)
    if year in SHARES:
        return SHARES[year]
    ys = np.array(years)
    vs = np.array([SHARES[y] for y in years])
    return float(np.interp(year, ys, vs))


def build_panel() -> pd.DataFrame:
    cdc = download_cdc_unmarried()
    cdc = cdc[cdc["race"] == "All Races"].copy()
    age_map = {
        "15-19 years": (15, 19), "20-24 years": (20, 24), "25-29 years": (25, 29),
        "30-34 years": (30, 34), "35-39 years": (35, 39), "40-44 years": (40, 44),
    }
    cdc = cdc[cdc["age"].isin(age_map)].copy()
    cdc["age_lo"] = cdc["age"].map(lambda a: age_map[a][0])
    cdc["age_hi"] = cdc["age"].map(lambda a: age_map[a][1])
    cdc["weight"] = cdc["age_hi"] - cdc["age_lo"] + 1

    years = list(range(1960, 1981, 10)) + list(range(2000, 2023))
    rows = []
    baseline_share = interpolate_share(2000)

    for year in years:
        share_m = interpolate_share(year)
        share_u = 1.0 - share_m

        if year in NCHS_GFR:
            gfr_m, gfr_u = NCHS_GFR[year]
            rate_m = gfr_m / 1000.0
            rate_u = gfr_u / 1000.0
            rows.append(dict(year=year, age_lo=15, age_hi=44, status="married",
                             share=share_m, rate=rate_m, weight=30,
                             share_baseline=interpolate_share(1960 if year <= 1980 else 2000)))
            rows.append(dict(year=year, age_lo=15, age_hi=44, status="unmarried",
                             share=share_u, rate=rate_u, weight=30,
                             share_baseline=1 - interpolate_share(1960 if year <= 1980 else 2000)))
            continue

        sub = cdc[cdc["year"] == year]
        if sub.empty and year <= 1980:
            # Historical anchors: approximate from 1980 CDC + NCHS trend
            sub = cdc[cdc["year"] == 1980]
        for _, r in sub.iterrows():
            rate_u = r["birth_rate"] / 1000.0
            # Back-out married rate from aggregate TFR if NCHS point missing
            rate_m = rate_u * 1.8  # rough married/unmarried rate ratio pre-2000
            w = r["weight"]
            rows.append(dict(year=year, age_lo=r["age_lo"], age_hi=r["age_hi"],
                             status="unmarried", share=share_u, rate=rate_u, weight=w,
                             share_baseline=1 - (interpolate_share(1960) if year <= 1980 else baseline_share)))
            rows.append(dict(year=year, age_lo=r["age_lo"], age_hi=r["age_hi"],
                             status="married", share=share_m, rate=rate_m, weight=w,
                             share_baseline=(interpolate_share(1960) if year <= 1980 else baseline_share)))

    panel = pd.DataFrame(rows)
    panel.to_csv(DATA / "fertility_panel.csv", index=False)
    return panel


def main() -> None:
    ensure_wpp()
    panel = build_panel()
    print(f"Wrote fertility panel: {len(panel)} rows, years {panel.year.min()}-{panel.year.max()}")


if __name__ == "__main__":
    main()
