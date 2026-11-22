#!/usr/bin/env python3
"""Validate both community indexes: plugins/index.json and catalog/index.json.

Plugins are stricter: schema + sha256 + WASM URL shape.
Catalog is cheaper: schema + HTTPS URL + checksum field format.

Catalog entries come from two places (SBAI-15330). catalog/index.json holds
entries added by hand whose artifact the author hosts. catalog/entries/<id>.json
holds one entry per file, with its artifact in this repo under
catalog/files/<id>/. The StudioBrain Marketplace writes those when its review
approves a hosted submission. For an in-repo artifact the SHA-256 is checked
against the real bytes, and the file is scanned for secrets.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path


PLUGIN_INDEX = "plugins/index.json"
CATALOG_INDEX = "catalog/index.json"
PLUGIN_SCHEMA = "schema/plugin-entry.json"
CATALOG_SCHEMA = "schema/catalog-entry.json"
CATALOG_ENTRIES_DIR = "catalog/entries"
CATALOG_FILES_DIR = "catalog/files"
MAX_CATALOG_FILE_BYTES = 256 * 1024
ENTRY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
FILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")

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
    "documents": "document",
}
KIND_TO_ARRAY = {kind: array for array, kind in CATALOG_ARRAYS.items()}

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
PLACEHOLDER_PLUGIN_ID = "hello-world-community"
SECRET_RE = re.compile(
    r"(?i)(ghp_|gho_|github_pat_|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|"
    r"api[_-]?key\s*[:=]\s*['\"][^'\"]{8,})"
)


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
    manifest_url = plugin.get("manifest_url", "")
    runtime = plugin.get("runtime")
    network = plugin.get("network") or ""
    environments = plugin.get("environments") or []

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
        if not manifest_url or not _https_url(manifest_url):
            errors.append(
                f"Plugin '{plugin_id}': published plugins require https manifest_url"
            )
    elif sha:
        errors.append(
            f"Plugin '{plugin_id}': sha256 must be empty when wasm_bundle_url is empty"
        )
    elif manifest_url:
        errors.append(
            f"Plugin '{plugin_id}': manifest_url must be empty when wasm_bundle_url is empty"
        )

    desktop_only = environments == ["desktop"]
    blob = json.dumps(plugin)
    if network == "local" or "network:local" in blob:
        if not desktop_only:
            errors.append(
                f"Plugin '{plugin_id}': network:local is allowed only when "
                "environments is exactly [\"desktop\"]"
            )

    if SECRET_RE.search(blob):
        errors.append(
            f"Plugin '{plugin_id}': index entry must not contain secrets "
            "(API keys, tokens, private keys)"
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


def validate_entry_file(path: Path) -> tuple[dict | None, list[str]]:
    """Check one catalog/entries/<id>.json and the artifact it names."""
    label = f"Catalog entry file '{path.as_posix()}'"
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"{label}: not valid JSON ({exc})"]
    if not isinstance(entry, dict):
        return None, [f"{label}: must be a JSON object"]

    errors: list[str] = []
    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or not ENTRY_ID_RE.fullmatch(entry_id):
        return None, [f"{label}: id must be lowercase letters, digits and dashes"]
    if path.stem != entry_id:
        errors.append(f"{label}: file name must be '{entry_id}.json' to match its id")
    if entry.get("kind") not in KIND_TO_ARRAY:
        errors.append(f"{label}: unknown kind {entry.get('kind')!r}")

    file_rel = entry.get("file")
    prefix = f"{CATALOG_FILES_DIR}/{entry_id}/"
    if not isinstance(file_rel, str) or not file_rel.startswith(prefix):
        errors.append(f"{label}: file must be a path under {prefix}")
        return entry, errors
    name = file_rel[len(prefix):]
    if not FILE_NAME_RE.fullmatch(name) or ".." in name:
        errors.append(f"{label}: file must name one plain file under {prefix}")
        return entry, errors

    artifact = Path(file_rel)
    if artifact.is_symlink() or not artifact.is_file():
        errors.append(f"{label}: {file_rel} is not a regular file in this repo")
        return entry, errors
    data = artifact.read_bytes()
    if len(data) > MAX_CATALOG_FILE_BYTES:
        errors.append(f"{label}: {file_rel} is over {MAX_CATALOG_FILE_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label}: {file_rel} must be UTF-8 text")
        text = ""
    digest = hashlib.sha256(data).hexdigest()
    if entry.get("sha256") != digest:
        errors.append(
            f"{label}: sha256 does not match {file_rel} "
            f"(entry {entry.get('sha256')!r}, file {digest})"
        )
    url = entry.get("download_url", "")
    if not isinstance(url, str) or not url.endswith("/" + file_rel):
        errors.append(f"{label}: download_url must end with /{file_rel}")
    if SECRET_RE.search(text) or SECRET_RE.search(json.dumps(entry)):
        errors.append(f"{label}: entry and file must not contain secrets")
    return entry, errors


def check_orphan_files() -> list[str]:
    """Every folder under catalog/files/ belongs to an entry file."""
    root = Path(CATALOG_FILES_DIR)
    if not root.is_dir():
        return []
    errors: list[str] = []
    for child in sorted(root.iterdir()):
        if child.name.startswith("."):
            continue
        if not child.is_dir():
            errors.append(f"{child.as_posix()}: only folders named after an entry id belong here")
        elif not (Path(CATALOG_ENTRIES_DIR) / f"{child.name}.json").is_file():
            errors.append(f"{child.as_posix()}: no {CATALOG_ENTRIES_DIR}/{child.name}.json names this folder")
    return errors


def load_catalog() -> tuple[dict, list[str]]:
    """catalog/index.json with every valid catalog/entries/*.json merged in.

    This is the document that is validated, checked for duplicates and
    published. Entry files that fail their checks are left out and reported.
    """
    doc = load_json(CATALOG_INDEX)
    errors: list[str] = []
    entries_dir = Path(CATALOG_ENTRIES_DIR)
    if entries_dir.is_dir():
        for path in sorted(entries_dir.glob("*.json")):
            entry, entry_errors = validate_entry_file(path)
            errors.extend(entry_errors)
            if entry is None or entry_errors:
                continue
            array_name = KIND_TO_ARRAY[entry["kind"]]
            if not isinstance(doc.get(array_name), list):
                doc[array_name] = []
            doc[array_name].append(entry)
    errors.extend(check_orphan_files())
    return doc, errors


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

    catalog_doc, catalog_errors = load_catalog()
    errors.extend(catalog_errors)
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
