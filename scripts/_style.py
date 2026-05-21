"""
FT-inspired matplotlib style for Burn-Murdoch audit figures.

Cream background and source-line footers follow standard FT charting practice.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

FT_CREAM = "#FFF1E5"
FT_INK = "#262A33"
FT_CLARET = "#990F3D"
FT_OXFORD = "#0F5499"
FT_CYAN = "#5CC9E0"
FT_GRID = "#D9D2C7"

COUNTRY_COLOR = FT_CYAN


def apply_ft_style() -> None:
    """Set matplotlib rcParams to an FT-inspired look."""
    mpl.rcParams.update({
        "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 13,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.labelsize": 13,
        "axes.labelcolor": FT_INK,
        "axes.edgecolor": FT_INK,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.facecolor": FT_CREAM,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": FT_GRID,
        "grid.linewidth": 0.6,
        "grid.alpha": 0.9,
        "xtick.color": FT_INK,
        "ytick.color": FT_INK,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "figure.facecolor": FT_CREAM,
        "figure.titlesize": 22,
        "figure.titleweight": "bold",
        "legend.frameon": False,
        "legend.fontsize": 12,
        "legend.labelcolor": FT_INK,
        "text.color": FT_INK,
        "savefig.facecolor": FT_CREAM,
        "savefig.edgecolor": FT_CREAM,
        "savefig.dpi": 200,
    })


def add_source(fig, text: str) -> None:
    fig.text(0.01, 0.005, text, ha="left", va="bottom", fontsize=10,
             style="italic", color="#666666")


def add_brand(fig) -> None:
    fig.text(0.99, 0.005, "isitcredible.com", ha="right", va="bottom",
             fontsize=11, fontweight="bold", color=FT_CLARET)
