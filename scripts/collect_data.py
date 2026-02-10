#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = ["requests"]
# ///
"""Automated training-data collection for metamaska.

Run with: uv run scripts/collect_data.py

Fully-automated sources:
  - HttpParamsDataset (GitHub CSV)   → valid, sqli, xss
  - PayloadsAllTheThings (GitHub)    → sqli, xss, cmdi, path-traversal

Deferred (stubs only):
  - Kaggle XSS dataset               → needs API key
  - ECML/PKDD 2007 dataset           → dead upstream link
  - HackTricks                        → payloads embedded in prose
"""

from __future__ import annotations

import csv
import io
import json
import logging
import subprocess
import tempfile
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "dataset.json"

MAX_LINES_PER_FILE = 5000

# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

Record = dict[str, str]  # {"pattern": ..., "type": ...}

VALID_TYPES = {"valid", "sqli", "xss", "cmdi", "path-traversal"}


def _make_record(pattern: str, type_: str) -> Record | None:
    pattern = pattern.strip()
    if not pattern or type_ not in VALID_TYPES:
        return None
    return {"pattern": pattern, "type": type_}


# ---------------------------------------------------------------------------
# HttpParamsDataset  (fully automated)
# ---------------------------------------------------------------------------

HTTPPARAMS_CSV_URL = (
    "https://raw.githubusercontent.com/Morzeux/HttpParamsDataset"
    "/master/payload_full.csv"
)


def collect_httpparams() -> list[Record]:
    """Download HttpParamsDataset CSV and return records."""
    log.info("Collecting HttpParamsDataset …")
    try:
        resp = requests.get(HTTPPARAMS_CSV_URL, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("HttpParamsDataset download failed: %s", exc)
        return []

    records: list[Record] = []
    reader = csv.DictReader(io.StringIO(resp.text))
    type_map = {"norm": "valid", "sqli": "sqli", "xss": "xss"}
    for row in reader:
        label = type_map.get(row.get("label", "").strip().lower())
        if label is None:
            label = type_map.get(row.get("attack_type", "").strip().lower())
        if label is None:
            continue
        payload = row.get("payload", "")
        rec = _make_record(payload, label)
        if rec:
            records.append(rec)

    log.info("  → %d records from HttpParamsDataset", len(records))
    return records


# ---------------------------------------------------------------------------
# PayloadsAllTheThings  (fully automated)
# ---------------------------------------------------------------------------

PATT_REPO = "swisskyrepo/PayloadsAllTheThings"

# Intruder dirs we care about  →  mapped type
PATT_DIRS: dict[str, str] = {
    "SQL Injection/Intruder": "sqli",
    "XSS Injection/Intruders": "xss",
    "Command Injection/Intruder": "cmdi",
    "Directory Traversal/Intruder": "path-traversal",
}

GITHUB_API = "https://api.github.com"


def _sparse_clone_patt() -> list[Record]:
    """Try a sparse git clone to grab only the Intruder directories."""
    records: list[Record] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "patt"
        try:
            subprocess.run(
                [
                    "git", "clone", "--filter=blob:none", "--no-checkout",
                    "--depth=1", f"https://github.com/{PATT_REPO}.git",
                    str(tmp_path),
                ],
                check=True, capture_output=True, timeout=60,
            )
            subprocess.run(
                ["git", "sparse-checkout", "init", "--cone"],
                cwd=tmp_path, check=True, capture_output=True, timeout=30,
            )
            subprocess.run(
                ["git", "sparse-checkout", "set", *PATT_DIRS.keys()],
                cwd=tmp_path, check=True, capture_output=True, timeout=30,
            )
            subprocess.run(
                ["git", "checkout"],
                cwd=tmp_path, check=True, capture_output=True, timeout=60,
            )
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            log.debug("Sparse clone failed: %s", exc)
            return []  # caller will fall back to API

        for dir_rel, type_ in PATT_DIRS.items():
            intruder = tmp_path / dir_rel
            if not intruder.is_dir():
                continue
            for txt in intruder.glob("*.txt"):
                lines = txt.read_text(errors="replace").splitlines()
                for line in lines[:MAX_LINES_PER_FILE]:
                    rec = _make_record(line, type_)
                    if rec:
                        records.append(rec)
    return records


def _api_download_patt() -> list[Record]:
    """Fallback: use the GitHub API to list + download raw files."""
    records: list[Record] = []
    session = requests.Session()

    for dir_rel, type_ in PATT_DIRS.items():
        api_url = f"{GITHUB_API}/repos/{PATT_REPO}/contents/{dir_rel}"
        try:
            resp = session.get(api_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            log.warning("  GitHub API failed for %s: %s", dir_rel, exc)
            continue

        for item in resp.json():
            if not item.get("name", "").endswith(".txt"):
                continue
            download_url = item.get("download_url")
            if not download_url:
                continue
            try:
                file_resp = session.get(download_url, timeout=60)
                file_resp.raise_for_status()
            except requests.RequestException:
                continue
            lines = file_resp.text.splitlines()
            for line in lines[:MAX_LINES_PER_FILE]:
                rec = _make_record(line, type_)
                if rec:
                    records.append(rec)
    return records


def collect_payloadsallthethings() -> list[Record]:
    """Collect payloads from PayloadsAllTheThings Intruder directories."""
    log.info("Collecting PayloadsAllTheThings …")
    records = _sparse_clone_patt()
    if not records:
        log.info("  Sparse clone unavailable, falling back to GitHub API …")
        records = _api_download_patt()
    log.info("  → %d records from PayloadsAllTheThings", len(records))
    return records


# ---------------------------------------------------------------------------
# Deferred sources (stubs)
# ---------------------------------------------------------------------------


def collect_kaggle_xss() -> list[Record]:
    """Stub — Kaggle XSS dataset requires an API key.

    To enable:
      1. pip install kaggle
      2. Place kaggle.json in ~/.kaggle/
      3. Implement download from 'Kaggle XSS dataset' here
    """
    log.info(
        "Skipping Kaggle XSS — requires API key. "
        "See https://www.kaggle.com/docs/api for setup instructions."
    )
    return []


def collect_ecml_pkdd() -> list[Record]:
    """Stub — ECML/PKDD 2007 HTTP dataset.

    The original link is currently dead. If a mirror becomes available,
    implement the download + parsing here.
    """
    log.info("Skipping ECML/PKDD 2007 — upstream link is dead.")
    return []


def collect_hacktricks() -> list[Record]:
    """Stub — HackTricks payloads are embedded in Markdown prose.

    Extracting them requires non-trivial parsing of the HackTricks
    GitBook/GitHub repo. Implement if/when structured payload files
    become available.
    """
    log.info("Skipping HackTricks — payloads embedded in prose, not yet parseable.")
    return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def deduplicate(records: list[Record]) -> list[Record]:
    seen: set[tuple[str, str]] = set()
    unique: list[Record] = []
    for r in records:
        key = (r["pattern"], r["type"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def main() -> None:
    all_records: list[Record] = []

    # Fully automated sources
    all_records.extend(collect_httpparams())
    all_records.extend(collect_payloadsallthethings())

    # Deferred sources (stubs — will log skip messages)
    all_records.extend(collect_kaggle_xss())
    all_records.extend(collect_ecml_pkdd())
    all_records.extend(collect_hacktricks())

    all_records = deduplicate(all_records)

    types_found = {r["type"] for r in all_records}
    log.info("Total unique records: %d", len(all_records))
    log.info("Types present: %s", ", ".join(sorted(types_found)))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    log.info("Written to %s", OUTPUT_FILE)


if __name__ == "__main__":
    main()
