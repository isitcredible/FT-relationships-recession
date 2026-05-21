"""
US coupling rates from CPS June fertility supplement.

Replicates FT Chart 2 (education split) and partial Chart 3 (aggregate 25-34)
for years where Census publishes junYYpub.csv.

Couple definition: married spouse present (PEMARITL==1) OR cohabiting partner
line present (PECOHAB==1), matching closest match to FT embed in 2022.
Education: bachelor's or above (PEEDUCA >= 43) vs below.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
sys.path.insert(0, str(ROOT / "scripts"))
from _audit import compare_long, load_benchmark, summarize, write_audit  # noqa: E402

CPS_URL = "https://www2.census.gov/programs-surveys/cps/datasets/{year}/supp/jun{yy}pub.csv"
YEARS = [2020, 2022]


def download_cps(year: int) -> Path:
    yy = str(year)[-2:]
    out = DATA / f"cps_jun{yy}pub.csv"
    if out.exists() and out.stat().st_size > 1_000_000:
        return out
    url = CPS_URL.format(year=year, yy=yy)
    DATA.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} ...")
    urllib.request.urlretrieve(url, out)
    return out


def coupling_from_cps(path: Path, year: int) -> pd.DataFrame:
    use = ["PRTAGE", "PESEX", "PEMARITL", "PEEDUCA", "PWCMPWGT", "PECOHAB"]
    df = pd.read_csv(path, usecols=use)
    df = df[(df["PESEX"] == 2) & (df["PRTAGE"].between(25, 34))].copy()
    df["coupled"] = (df["PEMARITL"] == 1) | (df["PECOHAB"] == 1)
    df["degree"] = df["PEEDUCA"] >= 43

    def wmean(mask: pd.Series) -> float:
        sub = df[mask]
        return 100.0 * sub["coupled"].mul(sub["PWCMPWGT"]).sum() / sub["PWCMPWGT"].sum()

    rows = [
        {"facet": "US", "year": year, "series": "Degree or higher", "value": wmean(df["degree"])},
        {"facet": "US", "year": year, "series": "Below degree", "value": wmean(~df["degree"])},
        {"facet": "US", "year": year, "series": "D o H", "value": wmean(df["degree"])},
        {"facet": "US", "year": year, "series": "No c", "value": wmean(~df["degree"])},
        {"facet": "Western", "year": year, "series": "US", "value": wmean(pd.Series(True, index=df.index))},
    ]
    return pd.DataFrame(rows)


def main() -> None:
    parts_edu, parts_ch3 = [], []
    for year in YEARS:
        path = download_cps(year)
        df = coupling_from_cps(path, year)
        parts_edu.append(df[df["facet"] == "US"])
        parts_ch3.append(df[df["facet"] == "Western"])

    edu = pd.concat(parts_edu, ignore_index=True)
    ch3 = pd.concat(parts_ch3, ignore_index=True)
    edu.to_csv(OUT / "cps_us_coupling_by_education.csv", index=False)
    ch3.to_csv(OUT / "cps_us_coupling_western.csv", index=False)

    bench2 = load_benchmark("ft_chart02_coupling_by_education.csv")
    bench2 = bench2[(bench2["facet"] == "US") & (bench2["year"].isin(YEARS))]
    audit2 = compare_long(
        edu[edu["series"].isin(["D o H", "No c"])],
        bench2,
        ["facet", "year", "series"],
        label="chart02_cps_us",
    )
    write_audit(audit2, OUT / "audit_chart02_cps_us.csv", summarize(audit2))

    bench3 = load_benchmark("ft_chart03_global_coupling.csv")
    bench3 = bench3[(bench3["facet"] == "Western") & (bench3["series"] == "US") & (bench3["year"].isin(YEARS))]
    audit3 = compare_long(ch3, bench3, ["facet", "year", "series"], label="chart03_cps_us")
    write_audit(audit3, OUT / "audit_chart03_cps_us.csv", summarize(audit3))


if __name__ == "__main__":
    main()
