"""Run Stone decomposition on fertility_panel_v2 and audit vs FT."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
sys.path.insert(0, str(ROOT / "scripts"))
from _stone import decomposition_series, to_ft_long  # noqa: E402
from _audit import compare_long, load_benchmark, summarize, write_audit  # noqa: E402


def main() -> None:
    panel_path = DATA / "fertility_panel_v2.csv"
    if not panel_path.exists():
        raise FileNotFoundError("Run 17_stone_panel_v2.py first")
    panel = pd.read_csv(panel_path)
    windows = {
        "1960-1980": (1960, list(range(1960, 1981, 10))),
        "2000-2022": (2000, list(range(2000, 2023))),
    }
    parts = []
    for facet, (base, years) in windows.items():
        avail = [y for y in years if y in panel["year"].unique()]
        p = panel[panel["year"].isin(avail)].copy()
        base_shares = (
            panel[panel["year"] == base][["age_lo", "age_hi", "status", "share"]]
            .rename(columns={"share": "share_baseline"})
        )
        p = p.merge(base_shares, on=["age_lo", "age_hi", "status"], how="left")
        dec = decomposition_series(p, base, avail)
        parts.append(to_ft_long(dec, facet))
    ours = pd.concat(parts, ignore_index=True)
    ours.to_csv(OUT / "chart01_stone_decomposition_v2.csv", index=False)
    bench = load_benchmark("ft_chart01_us_tfr_decomposition.csv")
    audit = compare_long(ours, bench, ["facet", "year", "series"], label="chart01_v2")
    write_audit(audit, OUT / "audit_chart01_v2.csv", summarize(audit))


if __name__ == "__main__":
    main()
