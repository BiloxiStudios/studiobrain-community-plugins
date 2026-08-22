#!/usr/bin/env python3
"""Check for duplicate IDs across plugins/index.json and catalog/index.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_entries import CATALOG_ARRAYS, CATALOG_INDEX, PLUGIN_INDEX


def main() -> int:
    with open(PLUGIN_INDEX, encoding="utf-8") as f:
        plugins_doc = json.load(f)
    with open(CATALOG_INDEX, encoding="utf-8") as f:
        catalog_doc = json.load(f)

    seen: dict[str, str] = {}
    duplicates: list[str] = []

    for plugin in plugins_doc.get("plugins", []):
        pid = plugin.get("id")
        if not pid:
            continue
        if pid in seen:
            duplicates.append(f"{pid} (plugins + {seen[pid]})")
        else:
            seen[pid] = "plugins"

    for array_name in CATALOG_ARRAYS:
        for entry in catalog_doc.get(array_name, []):
            eid = entry.get("id")
            if not eid:
                continue
            loc = f"catalog.{array_name}"
            if eid in seen:
                duplicates.append(f"{eid} ({loc} + {seen[eid]})")
            else:
                seen[eid] = loc

    if duplicates:
        print(f"ERROR: Duplicate IDs found: {duplicates}", file=sys.stderr)
        return 1

    print(f"No duplicate IDs found across {len(seen)} entr(y/ies).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
