#!/usr/bin/env python3
"""Enforce wasm-component runtime on community plugins.

The hello-world-community placeholder may still declare runtime='wasm'.
"""
from __future__ import annotations

import json
import sys

PLUGIN_INDEX = "plugins/index.json"
PLACEHOLDER_PLUGIN_ID = "hello-world-community"
ALLOWED = {"wasm-component"}
PLACEHOLDER_ALLOWED = {"wasm-component", "wasm"}


def main() -> int:
    with open(PLUGIN_INDEX, encoding="utf-8") as f:
        registry = json.load(f)

    bad: list[str] = []
    for plugin in registry.get("plugins", []):
        plugin_id = plugin.get("id", "<unknown>")
        runtime = plugin.get("runtime")
        allowed = PLACEHOLDER_ALLOWED if plugin_id == PLACEHOLDER_PLUGIN_ID else ALLOWED
        if runtime not in allowed:
            bad.append(f"{plugin_id} (runtime={runtime!r})")

    if bad:
        print(
            "ERROR: Community plugins must use runtime='wasm-component' "
            f"(placeholder {PLACEHOLDER_PLUGIN_ID} may use 'wasm'). "
            f"Invalid entries: {bad}",
            file=sys.stderr,
        )
        return 1

    total = len(registry.get("plugins", []))
    print(
        f"All {total} plugin(s) declare a WASM-component runtime "
        f"(or the {PLACEHOLDER_PLUGIN_ID} wasm placeholder)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
