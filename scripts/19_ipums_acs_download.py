"""
Submit / download IPUMS USA ACS extract for Stone decomposition.

Default extract #432 may already be queued from an interactive submit.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
from _ipums import (  # noqa: E402
    acs_samples,
    download_file,
    get_extract,
    stone_variables_female,
    submit_usa_extract,
    wait_for_extract,
)

META = DATA / "ipums_stone_extract.json"
DEFAULT_EXTRACT = 432


def main() -> None:
    if META.exists():
        meta = json.loads(META.read_text())
        number = meta["number"]
        print(f"Using saved extract #{number}")
    else:
        resp = submit_usa_extract(
            "FT relationship recession Stone ACS 2000-2022",
            acs_samples(),
            stone_variables_female(),
        )
        number = resp["number"]
        META.write_text(json.dumps({"number": number, "status": resp["status"]}, indent=2))
        print(f"Submitted extract #{number}")

    info = wait_for_extract(number)
    META.write_text(json.dumps(info, indent=2))
    url = info["downloadLinks"]["data"]["url"]
    gz = DATA / "ipums_stone_acs.csv.gz"
    download_file(url, gz)
    print(f"Downloaded {gz} ({gz.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
