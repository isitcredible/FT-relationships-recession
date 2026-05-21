"""
Audit Chart 1 replication vs FT benchmark.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _audit import compare_long, load_benchmark, summarize, write_audit  # noqa: E402


def main() -> None:
    ours = __import__("pandas").read_csv(ROOT / "output" / "chart01_stone_decomposition.csv")
    bench = load_benchmark("ft_chart01_us_tfr_decomposition.csv")
    audit = compare_long(ours, bench, ["facet", "year", "series"], label="chart01")
    summary = summarize(audit)
    write_audit(audit, ROOT / "output" / "audit_chart01.csv", summary)


if __name__ == "__main__":
    main()
