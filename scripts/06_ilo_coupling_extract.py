"""
Extract Western-facet coupling rates from Eurostat demo_pjanmarsta.

Legal marital status proxy: (married + registered partnership) / women 25-34.
Eurostat JSON-STAT API returns empty payloads for multi-geo requests; fetch
one geo at a time.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
from _eurostat import FT_TO_EUROSTAT, WESTERN_GEO, coupling_from_marital_status, fetch_table  # noqa: E402

YEARS = list(range(1980, 2025))


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows = []
    for year in YEARS:
        for geo, country in FT_TO_EUROSTAT.items():
            try:
                df = fetch_table("demo_pjanmarsta", geo=geo, time=year, sex="F")
            except Exception as exc:
                print(f"  {country} {year}: {exc}")
                continue
            if df.empty or "geo" not in df.columns:
                continue
            val = coupling_from_marital_status(df)
            if pd.notna(val):
                rows.append({"region": "Western", "country": country, "year": year, "coupling_rate": val})
        print(f"  {year}: done")

    out = pd.DataFrame(rows)
    out.to_csv(DATA / "eurostat_coupling_western.csv", index=False)
    print(f"Wrote {len(out)} rows to data/eurostat_coupling_western.csv")


if __name__ == "__main__":
    main()
