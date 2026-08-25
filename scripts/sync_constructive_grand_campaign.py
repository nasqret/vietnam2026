#!/usr/bin/env python3
"""Synchronize the portable grand-campaign explorer with its exact JSON DAG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
EXPLORER = CAMPAIGN.parent / "index.html"
OPENING = '<script type="application/json" id="campaign-data">'
CLOSING = "</script>"


def _snapshot() -> str:
    document = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    if type(document) is not dict or document.get("schema") != "constructive-grand-campaign-v1":
        raise ValueError("grand-campaign JSON has an invalid schema")
    payload = json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if "</script" in payload.lower():
        raise ValueError("grand-campaign JSON cannot contain a closing script element")
    return payload


def _expected(source: str) -> tuple[str, str]:
    start = source.find(OPENING)
    if start < 0 or source.find(OPENING, start + len(OPENING)) >= 0:
        raise ValueError("grand-campaign explorer needs exactly one embedded JSON snapshot")
    start += len(OPENING)
    finish = source.find(CLOSING, start)
    if finish < 0:
        raise ValueError("grand-campaign explorer has an unterminated JSON snapshot")
    return source[start:finish], source[:start] + _snapshot() + source[finish:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without rewriting HTML")
    arguments = parser.parse_args()
    try:
        source = EXPLORER.read_text(encoding="utf-8")
        observed, expected = _expected(source)
        if observed == _snapshot():
            print("Constructive grand-campaign embedded snapshot verified")
            return 0
        if arguments.check:
            print("Constructive grand-campaign embedded snapshot is stale")
            return 1
        EXPLORER.write_text(expected, encoding="utf-8")
        print("Constructive grand-campaign embedded snapshot updated")
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Cannot synchronize constructive grand-campaign snapshot: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
