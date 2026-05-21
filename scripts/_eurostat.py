"""Parse Eurostat JSON-STAT API responses."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd

EUROSTAT_BASE = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
)

# Eurostat geo codes for Western facet countries in FT chart 3
WESTERN_GEO = {
    "Canada": "CA",
    "Denmark": "DK",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Netherlands": "NL",
    "Poland": "PL",
    "Spain": "ES",
    "UK": "UK",
    "US": "US",
}

FT_TO_EUROSTAT = {v: k for k, v in WESTERN_GEO.items()}


def parse_eurostat(d: dict) -> pd.DataFrame:
    id_order = d["id"]
    sizes = d["size"]
    dimensions = d["dimension"]
    rev = {
        dim: {v: k for k, v in dimensions[dim]["category"]["index"].items()}
        for dim in id_order
    }
    rows = []
    for flat_idx, value in d["value"].items():
        remaining = int(flat_idx)
        coord = {}
        for i, dim in enumerate(id_order):
            size = sizes[i]
            index = remaining % size
            remaining //= size
            coord[dim] = rev[dim][index]
        coord["value"] = value
        rows.append(coord)
    return pd.DataFrame(rows)


def fetch_table(table: str, **filters) -> pd.DataFrame:
    parts = [f"{k}={v}" for k, v in filters.items()]
    parts += ["format=JSON", "lang=en"]
    url = f"{EUROSTAT_BASE}/{table}?{'&'.join(parts)}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        data = json.loads(resp.read())
    return parse_eurostat(data)


def coupling_from_marital_status(df: pd.DataFrame, ages: range = range(25, 35)) -> float:
    """Legal marital status proxy: (married + registered partnership) / total."""
    age_codes = {f"Y{a}" for a in ages}
    sub = df[df["age"].isin(age_codes)].copy()
    if sub.empty:
        return float("nan")
    total = sub["value"].sum()
    coupled = sub[sub["marsta"].isin(["MAR", "REP"])]["value"].sum()
    return 100.0 * coupled / total if total else float("nan")
