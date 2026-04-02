#!/usr/bin/env python3
"""Check for duplicate plugin IDs in index.json."""
import json
import sys


def main():
    with open("index.json") as f:
        registry = json.load(f)

    ids = [p.get("id") for p in registry.get("plugins", [])]
    seen = set()
    duplicates = []

    for pid in ids:
        if pid in seen:
            duplicates.append(pid)
        seen.add(pid)

    if duplicates:
        print(f"ERROR: Duplicate plugin IDs found: {duplicates}", file=sys.stderr)
        sys.exit(1)

    print(f"No duplicate IDs found across {len(ids)} plugin(s).")


if __name__ == "__main__":
    main()
