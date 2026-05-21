"""Audit Chart 5 vs FT benchmark."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from _audit import compare_long, load_benchmark, summarize, write_audit  # noqa: E402


def main() -> None:
    import pandas as pd
    ours = pd.read_csv(ROOT / "output" / "chart05_coupling_tfr_indexed.csv")
    bench = load_benchmark("ft_chart05_coupling_tfr_indexed.csv")
    audit = compare_long(ours, bench, ["facet", "year", "series"], label="chart05")
    summary = summarize(audit)
    write_audit(audit, ROOT / "output" / "audit_chart05.csv", summary)


if __name__ == "__main__":
    main()
