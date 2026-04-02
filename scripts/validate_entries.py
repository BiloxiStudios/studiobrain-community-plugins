#!/usr/bin/env python3
"""Validate each plugin entry in index.json against the JSON schema."""
import json
import subprocess
import sys
import tempfile
import os


def main():
    with open("index.json") as f:
        registry = json.load(f)

    errors = []
    for plugin in registry.get("plugins", []):
        plugin_id = plugin.get("id", "<unknown>")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(plugin, tmp)
            tmp_path = tmp.name
        try:
            result = subprocess.run(
                [
                    "npx", "--yes", "ajv", "validate",
                    "-s", "schema/plugin-entry.json",
                    "-d", tmp_path,
                    "--spec=draft7",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"Plugin '{plugin_id}' failed schema validation:\n"
                    f"{result.stdout}\n{result.stderr}"
                )
            else:
                print(f"  PASS: {plugin_id}")
        finally:
            os.unlink(tmp_path)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    print(f"\nAll {len(registry['plugins'])} plugin(s) passed schema validation.")


if __name__ == "__main__":
    main()
