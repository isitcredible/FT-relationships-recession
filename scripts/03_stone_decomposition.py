"""
Stone counterfactual TFR decomposition (Chart 1 replication).

Outputs:
  output/chart01_stone_decomposition.csv
  output/figures/chart01_stone_decomposition.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"
FIG = OUT / "figures"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "repo" / "scripts"))

from _stone import decomposition_series, to_ft_long  # noqa: E402

try:
    from _style import apply_ft_style, add_source, add_brand  # noqa: E402
except ImportError:
    def apply_ft_style(): pass
    def add_source(fig, text): pass
    def add_brand(fig): pass


def main() -> None:
    panel_path = DATA / "fertility_panel.csv"
    if not panel_path.exists():
        raise FileNotFoundError("Run 02_download_acs.py first")

    panel = pd.read_csv(panel_path)
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

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
        p = p.drop(columns=["share_baseline"], errors="ignore").merge(
            base_shares, on=["age_lo", "age_hi", "status"], how="left"
        )
        dec = decomposition_series(p, base, avail)
        parts.append(to_ft_long(dec, facet))

    ours = pd.concat(parts, ignore_index=True)
    ours.to_csv(OUT / "chart01_stone_decomposition.csv", index=False)

    apply_ft_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, facet in zip(axes, windows):
        sub = ours[ours["facet"] == facet]
        for series, color in [("Actual", "#94d2e6"), ("Counterfactual", "#2f85c3")]:
            s = sub[sub["series"] == series]
            ax.plot(s["year"], s["value"], label=series, color=color, linewidth=2)
        ax.set_title(facet)
        ax.set_xlabel("Year")
        ax.set_ylabel("% change in TFR")
        ax.axhline(0, color="#999", linewidth=0.8)
        ax.legend()
    fig.suptitle("US TFR decomposition (Stone counterfactual)", x=0.01, ha="left")
    add_source(fig, "Source: CDC NCHS + Census CPS marital shares (audit replication)")
    add_brand(fig)
    fig.tight_layout()
    fig.savefig(FIG / "chart01_stone_decomposition.png", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT / 'chart01_stone_decomposition.csv'}")


if __name__ == "__main__":
    main()
