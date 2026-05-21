"""IPUMS API client (api.ipums.org, Authorization header)."""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://api.ipums.org"


def get_api_key() -> str:
    key = os.environ.get("IPUMS_API_KEY") or os.environ.get("IPUMS_API")
    if key:
        return key
    # Non-interactive shells may not load profile; try login shell once.
    try:
        out = subprocess.check_output(
            ["zsh", "-lc", "printf %s \"$IPUMS_API_KEY\""],
            text=True,
            timeout=10,
        )
        if out.strip():
            return out.strip()
    except Exception:
        pass
    raise RuntimeError(
        "IPUMS_API_KEY not in environment. Ensure it is exported in ~/.zshrc "
        "or run: source ~/.zshrc"
    )


def _request(method: str, path: str, payload: dict | None = None, timeout: int = 120) -> dict:
    url = f"{API_BASE}{path}"
    headers = {"Authorization": get_api_key(), "Content-Type": "application/json"}
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"IPUMS API {exc.code}: {body}") from exc


def submit_usa_extract(description: str, samples: dict, variables: dict) -> dict:
    payload = {
        "description": description,
        "dataStructure": {"rectangular": {"on": "P"}},
        "dataFormat": "csv",
        "samples": samples,
        "variables": variables,
    }
    return _request("POST", "/extracts?collection=usa&version=2", payload)


def get_extract(number: int) -> dict:
    return _request("GET", f"/extracts/{number}?collection=usa&version=2")


def wait_for_extract(number: int, poll_sec: int = 30, max_wait: int = 7200) -> dict:
    deadline = time.time() + max_wait
    while time.time() < deadline:
        info = get_extract(number)
        status = info.get("status")
        print(f"  extract {number}: {status}")
        if status == "completed":
            return info
        if status in {"failed", "canceled"}:
            raise RuntimeError(f"Extract {number} {status}")
        time.sleep(poll_sec)
    raise TimeoutError(f"Extract {number} not completed within {max_wait}s")


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"Authorization": get_api_key()})
    with urllib.request.urlopen(req, timeout=600) as resp, open(dest, "wb") as out:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def acs_samples(start: int = 2000, end: int = 2022) -> dict:
    return {f"us{y}a": {} for y in range(start, end + 1)}


def stone_variables_female() -> dict:
    return {
        "AGE": {},
        "SEX": {"caseSelections": {"general": ["2"]}},
        "MARST": {},
        "FERTYR": {},
        "PERWT": {},
    }
