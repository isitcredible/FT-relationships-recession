"""
Chart 5: rebase coupling rate and TFR to 2010=100 for eight FT countries.

Coupling levels: Eurostat where available (Western proxy), else FT Chart 3
benchmark levels (documented fallback until ILO microdata pull).
TFR: UN WPP 2024 (data/tfr_annual.csv).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"

COUNTRIES = ["Finland", "Mexico", "Peru", "S Korea", "Thailand", "Tunisia", "Turkey", "US"]
ISO = {
    "Finland": "FIN", "Mexico": "MEX", "Peru": "PER", "S Korea": "KOR",
    "Thailand": "THA", "Tunisia": "TUN", "Turkey": "TUR", "US": "USA",
}
BASE = 2010
SKIP_SERIES = {"Region average", "Individual country"}


def load_ft_coupling_levels() -> pd.DataFrame:
    ch3 = pd.read_csv(OUT / "ft_chart03_global_coupling.csv")
    ch3 = ch3[~ch3["series"].isin(SKIP_SERIES)]
    return ch3.rename(columns={"series": "country", "value": "coupling_rate"})[
        ["country", "year", "coupling_rate"]
    ]


def load_eurostat_coupling() -> pd.DataFrame:
    path = DATA / "eurostat_coupling_western.csv"
    if not path.exists():
        return pd.DataFrame(columns=["country", "year", "coupling_rate"])
    return pd.read_csv(path)[["country", "year", "coupling_rate"]]


def load_coupling() -> pd.DataFrame:
    ft = load_ft_coupling_levels()
    euro = load_eurostat_coupling()
    # Prefer FT levels for chart-5 countries (ILO definition); keep euro for audit trail
    out = ft[ft["country"].isin(COUNTRIES)].copy()
    if out.empty:
        out = euro[euro["country"].isin(COUNTRIES)].copy()
    return out


def load_tfr() -> pd.DataFrame:
    tfr = pd.read_csv(DATA / "tfr_annual.csv")
    tfr = tfr[tfr["iso3"].isin(ISO.values())].copy()
    tfr["country"] = tfr["iso3"].map({v: k for k, v in ISO.items()})
    return tfr[["country", "year", "TFR"]]


def rebase(series: pd.Series, base_year: int = BASE) -> pd.Series:
    if base_year not in series.index:
        return series * float("nan")
    base = series.loc[base_year]
    if not base or pd.isna(base):
        return series * float("nan")
    return series / base * 100


def main() -> None:
    coupling = load_coupling()
    tfr = load_tfr()
    rows = []
    for country in COUNTRIES:
        c = coupling[coupling["country"] == country].set_index("year")["coupling_rate"]
        t = tfr[tfr["country"] == country].set_index("year")["TFR"]
        years = sorted(set(c.index) & set(t.index))
        if BASE not in years:
            continue
        c_idx = rebase(c.reindex(years))
        t_idx = rebase(t.reindex(years))
        for year in years:
            if pd.notna(c_idx.get(year)):
                rows.append({"facet": country, "year": int(year), "series": "Coupling rate", "value": c_idx[year]})
            if pd.notna(t_idx.get(year)):
                rows.append({"facet": country, "year": int(year), "series": "TFR", "value": t_idx[year]})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "chart05_coupling_tfr_indexed.csv", index=False)
    print(f"Wrote {len(out)} rows to output/chart05_coupling_tfr_indexed.csv")


if __name__ == "__main__":
    main()
