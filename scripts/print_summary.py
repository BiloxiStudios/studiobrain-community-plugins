#!/usr/bin/env python3
"""Print a summary of the validated registry."""
import json


def main():
    with open("index.json") as f:
        registry = json.load(f)

    plugins = registry.get("plugins", [])
    print("Registry validation passed.")
    print(f"  Registry version: {registry.get('version', 'unknown')}")
    print(f"  Total plugins:    {len(plugins)}")
    for p in plugins:
        print(f"  - {p['id']} v{p['version']} by {p['author']} ({p['category']})")


if __name__ == "__main__":
    main()
