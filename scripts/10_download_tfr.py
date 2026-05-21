"""Ensure UN WPP TFR is in data/tfr_annual.csv."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

mod = import_module("02_download_acs")
mod.ensure_wpp()
print("TFR data ready.")
