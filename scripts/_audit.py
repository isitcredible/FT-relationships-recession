"""Compare replication output to FT benchmark CSVs."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
BENCH = OUT


def load_benchmark(name: str) -> pd.DataFrame:
    return pd.read_csv(BENCH / name)


def compare_long(
    ours: pd.DataFrame,
    bench: pd.DataFrame,
    keys: list[str],
    value_col: str = "value",
    label: str = "",
) -> pd.DataFrame:
    left = ours[keys + [value_col]].rename(columns={value_col: "ours"})
    right = bench[keys + [value_col]].rename(columns={value_col: "ft"})
    merged = left.merge(right, on=keys, how="outer")
    merged["diff"] = merged["ours"] - merged["ft"]
    merged["abs_diff"] = merged["diff"].abs()
    merged["audit"] = label
    return merged.sort_values(keys)


def summarize(audit: pd.DataFrame) -> dict:
    valid = audit.dropna(subset=["ours", "ft"])
    if valid.empty:
        return {"n": 0, "mae": np.nan, "max_abs": np.nan, "rmse": np.nan}
    return {
        "n": len(valid),
        "mae": valid["abs_diff"].mean(),
        "max_abs": valid["abs_diff"].max(),
        "rmse": np.sqrt((valid["diff"] ** 2).mean()),
    }


def write_audit(audit: pd.DataFrame, path: Path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(path, index=False)
    summary_path = path.with_name(path.stem + "_summary.txt")
    summary_path.write_text(
        "\n".join(f"{k}: {v}" for k, v in summary.items()) + "\n"
    )
    print(f"Wrote {path}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
