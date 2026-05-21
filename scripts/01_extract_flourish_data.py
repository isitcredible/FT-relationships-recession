"""
Extract FT chart data from saved Flourish embed HTML files.

John Burn-Murdoch, "The relationship recession is going global,"
Financial Times, 11 January 2025.

Each embed ships full data in JavaScript (_Flourish_data). This script
parses those blocks and writes tidy benchmark CSVs to output/.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_FILES = ROOT / "archive" / "The relationship recession is going global_files"
OUT = ROOT / "output"

EMBEDS = [
    ("embed.html", "ft_chart01_us_tfr_decomposition.csv"),
    ("embed(2).html", "ft_chart02_coupling_by_education.csv"),
    ("embed(3).html", "ft_chart03_global_coupling.csv"),
    ("embed(4).html", "ft_chart04_gsma_mobile_gender_gap.csv"),
    ("embed(5).html", "ft_chart05_coupling_tfr_indexed.csv"),
]


def _parse_js_object(text: str) -> dict | list:
    """Best-effort parse of a JS object literal embedded in saved HTML."""
    # new Date(ms) -> ms (UTC year extraction handled separately)
    text = re.sub(r"new Date\((-?\d+)\)", r"\1", text)
    text = re.sub(r"new Date\((-?\d+\.?\d*)\)", r"\1", text)
    # trailing commas before } or ]
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def _extract_js_value(html: str, name: str) -> str:
    """Extract a JS object/array assigned to name (possibly in a var a=..., b=... block)."""
    marker = f"{name} = "
    start = html.find(marker)
    if start < 0:
        raise ValueError(f"Could not find {name} in embed HTML")
    i = start + len(marker)
    while i < len(html) and html[i].isspace():
        i += 1
    opener = html[i]
    if opener not in "{[":
        raise ValueError(f"Expected object/array after {name}, got {opener!r}")
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escape = False
    j = i
    while j < len(html):
        ch = html[j]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return html[i : j + 1]
        j += 1
    raise ValueError(f"Unterminated value for {name}")


def _label_to_year(label) -> int | float | str | None:
    if label is None:
        return None
    if isinstance(label, (int, float)):
        if 1800 <= label <= 2100:
            return int(label)
        # Flourish datetime: ms since epoch if |label| >= 1e11 (~1973 as ms)
        if abs(label) >= 100_000_000_000:
            return datetime.fromtimestamp(label / 1000, tz=timezone.utc).year
        if abs(label) >= 1_000_000_000:
            return datetime.fromtimestamp(label, tz=timezone.utc).year
        if label == 0:
            return 1970
        return int(label) if float(label).is_integer() else label
    return label


def _settings_title(html: str) -> str:
    m = re.search(r'"layout\.title"\s*:\s*"((?:\\.|[^"\\])*)"', html)
    return m.group(1).encode().decode("unicode_escape") if m else ""


def _viz_id(html: str) -> int | None:
    m = re.search(r"_Flourish_visualisation_id\s*=\s*(\d+)", html)
    return int(m.group(1)) if m else None


def _rows_to_long(rows: list, col_names: dict) -> pd.DataFrame:
    """Standard facet/label/value Flourish table -> long CSV."""
    # col_names maps JS field names (keys) to human labels (values); rows use keys.
    value_cols = col_names.get("value") or []

    records = []
    for row in rows:
        facet = row.get("facet")
        label = _label_to_year(row.get("label"))
        values = row.get("value") or []
        for series, val in zip(value_cols, values):
            if val is None:
                continue
            records.append({
                "facet": facet,
                "year": label,
                "series": series,
                "value": val,
            })
    return pd.DataFrame(records)


def _rows_dot_chart(rows: list, col_names: dict) -> pd.DataFrame:
    records = []
    for row in rows:
        records.append({
            "region": row.get("y") or row.get("series"),
            "sex": row.get("color"),
            "value": row.get("x"),
        })
    return pd.DataFrame(records)


def extract_embed(path: Path) -> tuple[pd.DataFrame, dict]:
    html = path.read_text(encoding="utf-8", errors="replace")
    meta = {
        "file": path.name,
        "viz_id": _viz_id(html),
        "title": _settings_title(html),
    }

    data_raw = _extract_js_value(html, "_Flourish_data")
    col_raw = _extract_js_value(html, "_Flourish_data_column_names")
    data_obj = _parse_js_object(data_raw)
    col_obj = _parse_js_object(col_raw)

    rows = data_obj["data"]
    col_names = col_obj["data"]

    if "x" in col_names and "y" in col_names:
        df = _rows_dot_chart(rows, col_names)
    else:
        df = _rows_to_long(rows, col_names)

    return df, meta


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []

    for embed_name, out_name in EMBEDS:
        path = ARCHIVE_FILES / embed_name
        df, meta = extract_embed(path)
        out_path = OUT / out_name
        df.to_csv(out_path, index=False)
        manifest.append({**meta, "rows": len(df), "output": out_name})
        print(f"{embed_name} (viz {meta['viz_id']}): {len(df)} rows -> {out_name}")
        print(f"  title: {meta['title'][:80]}...")

    pd.DataFrame(manifest).to_csv(OUT / "ft_chart_manifest.csv", index=False)
    print(f"\nWrote manifest to {OUT / 'ft_chart_manifest.csv'}")


if __name__ == "__main__":
    main()
