#!/usr/bin/env python3
"""Validate both community indexes: plugins/index.json and catalog/index.json.

Plugins are stricter: schema + sha256 + WASM URL shape.
Catalog is cheaper: schema + HTTPS URL + checksum field format.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


PLUGIN_INDEX = "plugins/index.json"
CATALOG_INDEX = "catalog/index.json"
PLUGIN_SCHEMA = "schema/plugin-entry.json"
CATALOG_SCHEMA = "schema/catalog-entry.json"

CATALOG_ARRAYS = {
    "templates": "template",
    "rules": "rule",
    "skills": "skill",
    "layouts": "layout",
    "packs": "pack",
    "providers": "provider",
    "abilities": "ability",
    "flows": "flow",
    "canvas": "canvas",
}

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
PLACEHOLDER_PLUGIN_ID = "hello-world-community"


def _load_schema(schema_path: str) -> dict:
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def _ajv(schema_path: str, data: dict, label: str) -> str | None:
    try:
        import jsonschema
    except ImportError:
        jsonschema = None

    if jsonschema is not None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft7Validator(schema)
        issues = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
        if not issues:
            return None
        details = "\n".join(
            f"  {'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in issues
        )
        return f"{label} failed schema validation:\n{details}"

    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        return (
            f"{label}: cannot validate schema — install jsonschema "
            "(`pip install jsonschema`) or ajv-cli"
        )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [
                npx,
                "--yes",
                "ajv",
                "validate",
                "-s",
                schema_path,
                "-d",
                tmp_path,
                "--spec=draft7",
                "--strict=false",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return (
                f"{label} failed schema validation:\n"
                f"{result.stdout}\n{result.stderr}"
            )
        return None
    finally:
        os.unlink(tmp_path)


def _https_url(value: str) -> bool:
    return value.startswith("https://")


def validate_plugin(plugin: dict) -> list[str]:
    plugin_id = plugin.get("id", "<unknown>")
    errors: list[str] = []
    schema_err = _ajv(PLUGIN_SCHEMA, plugin, f"Plugin '{plugin_id}'")
    if schema_err:
        errors.append(schema_err)
        return errors

    url = plugin.get("wasm_bundle_url", "")
    sha = plugin.get("sha256", "")
    runtime = plugin.get("runtime")

    if runtime not in ("wasm-component", "wasm"):
        errors.append(
            f"Plugin '{plugin_id}': runtime must be 'wasm-component' "
            f"(or 'wasm' for the hello-world-community placeholder), got {runtime!r}"
        )
    elif runtime == "wasm" and plugin_id != PLACEHOLDER_PLUGIN_ID:
        errors.append(
            f"Plugin '{plugin_id}': runtime must be 'wasm-component'. "
            f"'wasm' is only allowed on {PLACEHOLDER_PLUGIN_ID}."
        )

    if url:
        if not _https_url(url):
            errors.append(f"Plugin '{plugin_id}': wasm_bundle_url must be https://")
        if ".wasm" not in url.lower():
            errors.append(
                f"Plugin '{plugin_id}': wasm_bundle_url must point at a .wasm file"
            )
        if not SHA256_RE.fullmatch(sha or ""):
            errors.append(
                f"Plugin '{plugin_id}': published plugins require sha256 (64 hex chars)"
            )
    elif sha:
        errors.append(
            f"Plugin '{plugin_id}': sha256 must be empty when wasm_bundle_url is empty"
        )

    return errors


def validate_catalog_entry(entry: dict, array_name: str, expected_kind: str) -> list[str]:
    entry_id = entry.get("id", "<unknown>")
    label = f"Catalog {array_name} '{entry_id}'"
    errors: list[str] = []
    schema_err = _ajv(CATALOG_SCHEMA, entry, label)
    if schema_err:
        errors.append(schema_err)
        return errors

    kind = entry.get("kind")
    if kind != expected_kind:
        errors.append(
            f"{label}: kind must be {expected_kind!r} to match the {array_name} array, "
            f"got {kind!r}"
        )

    url = entry.get("download_url", "")
    sha = entry.get("sha256", "")
    if url and not _https_url(url):
        errors.append(f"{label}: download_url must be https://")
    if url and sha and not SHA256_RE.fullmatch(sha):
        errors.append(f"{label}: sha256 must be 64 lowercase hex chars when set")
    if not url and sha:
        errors.append(f"{label}: sha256 must be empty when download_url is empty")

    return errors


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    errors: list[str] = []
    plugin_count = 0
    catalog_count = 0

    plugins_doc = load_json(PLUGIN_INDEX)
    if "plugins" not in plugins_doc or not isinstance(plugins_doc["plugins"], list):
        errors.append(f"{PLUGIN_INDEX} must contain a plugins array")
    else:
        for plugin in plugins_doc["plugins"]:
            plugin_count += 1
            plugin_errors = validate_plugin(plugin)
            if plugin_errors:
                errors.extend(plugin_errors)
            else:
                print(f"  PASS plugin: {plugin.get('id', '<unknown>')}")

    catalog_doc = load_json(CATALOG_INDEX)
    for array_name, expected_kind in CATALOG_ARRAYS.items():
        if array_name not in catalog_doc:
            errors.append(f"{CATALOG_INDEX} missing required array '{array_name}'")
            continue
        entries = catalog_doc[array_name]
        if not isinstance(entries, list):
            errors.append(f"{CATALOG_INDEX}.{array_name} must be an array")
            continue
        for entry in entries:
            catalog_count += 1
            entry_errors = validate_catalog_entry(entry, array_name, expected_kind)
            if entry_errors:
                errors.extend(entry_errors)
            else:
                print(f"  PASS catalog/{array_name}: {entry.get('id', '<unknown>')}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(
        f"\nAll {plugin_count} plugin(s) and {catalog_count} catalog entr(y/ies) "
        "passed validation."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
