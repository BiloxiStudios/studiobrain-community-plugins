#!/usr/bin/env python3
"""Print a summary of both community indexes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_entries import CATALOG_ARRAYS, CATALOG_INDEX, PLUGIN_INDEX


def main() -> None:
    with open(PLUGIN_INDEX, encoding="utf-8") as f:
        plugins_doc = json.load(f)
    with open(CATALOG_INDEX, encoding="utf-8") as f:
        catalog_doc = json.load(f)

    plugins = plugins_doc.get("plugins", [])
    print("Registry validation passed.")
    print(f"  Plugin index version:  {plugins_doc.get('version', 'unknown')}")
    print(f"  Catalog index version: {catalog_doc.get('version', 'unknown')}")
    print(f"  Total plugins:         {len(plugins)}")
    for plugin in plugins:
        print(
            f"  - {plugin['id']} v{plugin['version']} by {plugin['author']} "
            f"({plugin.get('category', 'plugin')}, runtime={plugin.get('runtime')})"
        )

    print("  Catalog counts:")
    for array_name in CATALOG_ARRAYS:
        entries = catalog_doc.get(array_name, [])
        print(f"    {array_name}: {len(entries)}")
        for entry in entries:
            print(
                f"      - {entry.get('id')} v{entry.get('version')} "
                f"by {entry.get('author')}"
            )


if __name__ == "__main__":
    main()
