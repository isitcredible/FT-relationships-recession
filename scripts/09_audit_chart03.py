"""Audit Chart 3 Western facet vs FT benchmark."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from _audit import compare_long, load_benchmark, summarize, write_audit  # noqa: E402


def main() -> None:
    raw = pd.read_csv(ROOT / "output" / "chart03_coupling_western.csv")
    ours = raw.rename(columns={"region": "facet", "country": "series", "coupling_rate": "value"})
    bench = load_benchmark("ft_chart03_global_coupling.csv")
    bench = bench[bench["facet"] == "Western"]
    audit = compare_long(ours, bench, ["facet", "year", "series"], label="chart03_western")
    summary = summarize(audit)
    write_audit(audit, ROOT / "output" / "audit_chart03_western.csv", summary)


if __name__ == "__main__":
    main()
