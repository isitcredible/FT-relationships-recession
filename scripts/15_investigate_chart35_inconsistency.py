"""
Investigate Chart 3 vs Chart 5 coupling inconsistency within the same article.

Chart 5 should be Chart 3 coupling levels rebased to 2010=100. This script
reverse-engineers implied levels from Chart 5 and compares to Chart 3 directly.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
COUNTRIES = ["Finland", "Mexico", "Peru", "S Korea", "Thailand", "Tunisia", "Turkey", "US"]
BASE = 2010


def load_chart3() -> pd.DataFrame:
    ch3 = pd.read_csv(OUT / "ft_chart03_global_coupling.csv")
    ch3 = ch3[ch3["series"].isin(COUNTRIES)].rename(
        columns={"series": "country", "value": "level_ch3"}
    )
    return ch3[["country", "year", "level_ch3"]]


def load_chart5() -> pd.DataFrame:
    ch5 = pd.read_csv(OUT / "ft_chart05_coupling_tfr_indexed.csv")
    ch5 = ch5[ch5["series"] == "Coupling rate"].rename(
        columns={"facet": "country", "value": "index_ch5"}
    )
    return ch5[["country", "year", "index_ch5"]]


def implied_levels(ch3: pd.DataFrame, ch5: pd.DataFrame) -> pd.DataFrame:
    base = ch3[ch3["year"] == BASE][["country", "level_ch3"]].rename(
        columns={"level_ch3": "base_ch3"}
    )
    merged = ch5.merge(base, on="country", how="left")
    merged["level_implied_from_ch5"] = merged["index_ch5"] / 100.0 * merged["base_ch3"]
    return merged.merge(ch3, on=["country", "year"], how="left")


def main() -> None:
    ch3 = load_chart3()
    ch5 = load_chart5()
    panel = implied_levels(ch3, ch5)
    panel["diff_pp"] = panel["level_implied_from_ch5"] - panel["level_ch3"]
    panel["ratio"] = panel["level_implied_from_ch5"] / panel["level_ch3"]

    audit = panel.dropna(subset=["level_ch3", "level_implied_from_ch5"])
    summary = {
        "n": len(audit),
        "mae_pp": audit["diff_pp"].abs().mean(),
        "max_abs_pp": audit["diff_pp"].abs().max(),
        "median_ratio": audit["ratio"].median(),
    }

    out = OUT / "audit_chart35_coupling_inconsistency.csv"
    audit.to_csv(out, index=False)

    worst = audit.reindex(audit["diff_pp"].abs().sort_values(ascending=False).index).head(15)
    worst_path = OUT / "audit_chart35_worst_rows.csv"
    worst.to_csv(worst_path, index=False)

    summary_path = OUT / "audit_chart35_summary.txt"
    summary_path.write_text(
        "\n".join(f"{k}: {v}" for k, v in summary.items()) + "\n"
        + "\nWorst rows (country, year, ch3, ch5-implied, diff_pp):\n"
        + "\n".join(
            f"  {r.country} {int(r.year)}: {r.level_ch3:.2f} vs {r.level_implied_from_ch5:.2f} ({r.diff_pp:+.2f})"
            for _, r in worst.head(8).iterrows()
        )
        + "\n"
    )

    print(f"Wrote {out} ({len(audit)} rows)")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"Wrote {worst_path}")


if __name__ == "__main__":
    main()
