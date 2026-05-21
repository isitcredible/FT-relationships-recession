"""
Chart 4: verify GSMA 2018 mobile gender gap against FT embed values.

Source: GSMA Mobile Gender Gap Report 2018, Table 2 (LMIC regions).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

# GSMA 2018 report Table 2: pct using mobile internet, LMIC regions
GSMA_2018 = [
    ("Europe & central Asia", "Women", 67), ("Europe & central Asia", "Men", 70),
    ("East Asia", "Women", 61), ("East Asia", "Men", 64),
    ("Latin America", "Women", 60), ("Latin America", "Men", 63),
    ("MENA", "Women", 43), ("MENA", "Men", 54),
    ("Sub-Saharan Africa", "Women", 24), ("Sub-Saharan Africa", "Men", 39),
    ("South Asia", "Women", 10), ("South Asia", "Men", 34),
]


def main() -> None:
    ours = pd.DataFrame(GSMA_2018, columns=["region", "sex", "value"])
    bench = pd.read_csv(OUT / "ft_chart04_gsma_mobile_gender_gap.csv")
    merged = ours.merge(bench, on=["region", "sex"], how="outer", suffixes=("_gsma", "_ft"))
    merged["diff"] = merged["value_gsma"] - merged["value_ft"]
    merged.to_csv(OUT / "audit_chart04_gsma.csv", index=False)
    valid = merged.dropna()
    print(f"Chart 4 GSMA verify: max |diff| = {valid['diff'].abs().max():.4f} (expect 0)")


if __name__ == "__main__":
    main()
