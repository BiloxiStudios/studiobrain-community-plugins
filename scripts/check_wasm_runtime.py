#!/usr/bin/env python3
"""Enforce that all community plugins declare runtime='wasm'."""
import json
import sys


def main():
    with open("index.json") as f:
        registry = json.load(f)

    non_wasm = [
        p.get("id", "<unknown>")
        for p in registry.get("plugins", [])
        if p.get("runtime") != "wasm"
    ]

    if non_wasm:
        print(
            f"ERROR: Community plugins must use runtime='wasm'. "
            f"Non-WASM plugins found: {non_wasm}",
            file=sys.stderr,
        )
        sys.exit(1)

    total = len(registry.get("plugins", []))
    print(f"All {total} plugin(s) use WASM runtime. Community registry requirement satisfied.")


if __name__ == "__main__":
    main()
