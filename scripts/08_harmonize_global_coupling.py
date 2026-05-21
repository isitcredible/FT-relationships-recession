"""
Harmonize Western coupling panel and compute regional averages.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"


def main() -> None:
    src = DATA / "eurostat_coupling_western.csv"
    if not src.exists():
        raise FileNotFoundError("Run 06_ilo_coupling_extract.py first")
    df = pd.read_csv(src)
    avg = (
        df.groupby(["region", "year"], as_index=False)["coupling_rate"]
        .mean()
        .assign(country="Region average")
    )
    panel = pd.concat([df, avg], ignore_index=True)
    panel.to_csv(OUT / "chart03_coupling_western.csv", index=False)
    print(f"Wrote {len(panel)} rows to output/chart03_coupling_western.csv")


if __name__ == "__main__":
    main()
