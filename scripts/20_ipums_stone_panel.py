"""
Build Stone fertility panel from IPUMS ACS microdata.

Women 15-44, 5-year age bands, marital status groups matching Stone:
  married (MARST 1/2), divorced (4), widowed (5), never married (6).
Age-specific rate = weighted share with FERTYR==2 (birth in past year).
"""
from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

AGE_BINS = [(15, 19), (20, 24), (25, 29), (30, 34), (35, 39), (40, 44)]
STATUS_MAP = {
    1: "married",
    2: "married",
    4: "divorced",
    5: "widowed",
    6: "never_married",
}


def load_micro() -> pd.DataFrame:
    gz = DATA / "ipums_stone_acs.csv.gz"
    if not gz.exists():
        raise FileNotFoundError("Run 19_ipums_acs_download.py first")
    with gzip.open(gz, "rt") as f:
        df = pd.read_csv(f, usecols=["YEAR", "AGE", "MARST", "FERTYR", "PERWT"])
    df = df[df["AGE"].between(15, 44)].copy()
    df = df[df["MARST"].isin(STATUS_MAP)].copy()
    df["status"] = df["MARST"].map(STATUS_MAP)
    df["birth"] = (df["FERTYR"] == 2).astype(float)
    df["fert_ok"] = df["FERTYR"].isin([1, 2])
    return df


def age_band(age: int) -> tuple[int, int]:
    for lo, hi in AGE_BINS:
        if lo <= age <= hi:
            return lo, hi
    return 15, 19


def build_panel(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bands = df["AGE"].apply(age_band)
    df["age_lo"] = bands.apply(lambda x: x[0])
    df["age_hi"] = bands.apply(lambda x: x[1])
    df["weight"] = df["age_hi"] - df["age_lo"] + 1

    rows = []
    for year in sorted(df["YEAR"].unique()):
        sub = df[df["YEAR"] == year]
        for age_lo, age_hi in AGE_BINS:
            age_sub = sub[(sub["age_lo"] == age_lo) & (sub["age_hi"] == age_hi)]
            age_w = age_sub["PERWT"].sum()
            if age_w <= 0:
                continue
            for status in sorted(age_sub["status"].unique()):
                g = age_sub[age_sub["status"] == status]
                w = g["PERWT"].sum()
                if w <= 0:
                    continue
                fert = g[g["fert_ok"]]
                if fert.empty or fert["PERWT"].sum() <= 0:
                    continue
                rate = fert["birth"].mul(fert["PERWT"]).sum() / fert["PERWT"].sum()
                rows.append({
                    "year": int(year),
                    "age_lo": age_lo,
                    "age_hi": age_hi,
                    "status": status,
                    "share": w / age_w,
                    "rate": rate,
                    "weight": age_hi - age_lo + 1,
                })

    panel = pd.DataFrame(rows)
    # 2000 Census 1% lacks FERTYR; impute 2000 rates from 2001 (nearest ACS fertility year).
    if 2000 not in panel["year"].values and 2001 in panel["year"].values:
        shares00 = df[df["YEAR"] == 2000].copy()
        bands = shares00["AGE"].apply(age_band)
        shares00["age_lo"] = bands.apply(lambda x: x[0])
        shares00["age_hi"] = bands.apply(lambda x: x[1])
        shares00 = shares00[shares00["MARST"].isin(STATUS_MAP)]
        shares00["status"] = shares00["MARST"].map(STATUS_MAP)
        y0_rows = []
        for age_lo, age_hi in AGE_BINS:
            age_sub = shares00[(shares00["age_lo"] == age_lo) & (shares00["age_hi"] == age_hi)]
            age_w = age_sub["PERWT"].sum()
            if age_w <= 0:
                continue
            for status in sorted(age_sub["status"].unique()):
                g = age_sub[age_sub["status"] == status]
                w = g["PERWT"].sum()
                if w <= 0:
                    continue
                y0_rows.append({
                    "year": 2000,
                    "age_lo": age_lo,
                    "age_hi": age_hi,
                    "status": status,
                    "share": w / age_w,
                    "weight": age_hi - age_lo + 1,
                })
        y0 = pd.DataFrame(y0_rows).merge(
            panel[panel["year"] == 2001][["age_lo", "age_hi", "status", "rate"]],
            on=["age_lo", "age_hi", "status"],
            how="left",
        )
        panel = pd.concat([y0, panel], ignore_index=True)
    return panel


def main() -> None:
    df = load_micro()
    panel = build_panel(df)
    out = DATA / "fertility_panel_ipums.csv"
    panel.to_csv(out, index=False)
    print(f"Wrote {out} ({len(panel)} rows, years {panel.year.min()}-{panel.year.max()})")


if __name__ == "__main__":
    main()
