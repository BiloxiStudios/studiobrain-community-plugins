#!/usr/bin/env python3
"""Entry files under catalog/entries/ and their artifacts (SBAI-15330)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_entries  # noqa: E402

CONTENT = "---\nname: Noir detective\n---\n# Voice\nHard-boiled, first person.\n"
ENTRY_ID = "ml-0123456789abcdef0123456789abcdef"


class CatalogEntryFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        for name in ("schema", "plugins"):
            shutil.copytree(ROOT / name, Path(self.tmp) / name)
        os.makedirs(Path(self.tmp) / "catalog")
        shutil.copy(ROOT / "catalog" / "index.json", Path(self.tmp) / "catalog" / "index.json")
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self.cwd)
        shutil.rmtree(self.tmp)

    def write(self, content: str = CONTENT, **changes) -> None:
        file_rel = f"catalog/files/{ENTRY_ID}/item.md"
        os.makedirs(os.path.dirname(file_rel), exist_ok=True)
        Path(file_rel).write_text(content, encoding="utf-8")
        entry = {
            "id": ENTRY_ID,
            "kind": "rule",
            "version": "1.0.0",
            "download_url": f"https://raw.githubusercontent.com/o/r/main/{file_rel}",
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "author": "Ada",
            "file": file_rel,
        }
        entry.update(changes)
        os.makedirs("catalog/entries", exist_ok=True)
        name = changes.pop("_name", ENTRY_ID)
        Path(f"catalog/entries/{name}.json").write_text(json.dumps(entry), encoding="utf-8")

    def test_good_entry_is_merged_into_its_array(self) -> None:
        self.write()
        doc, errors = validate_entries.load_catalog()
        self.assertEqual(errors, [])
        self.assertEqual([e["id"] for e in doc["rules"]], [ENTRY_ID])
        self.assertEqual(validate_entries.main(), 0)

    def test_document_kind_has_an_array(self) -> None:
        self.write(kind="document")
        doc, errors = validate_entries.load_catalog()
        self.assertEqual(errors, [])
        self.assertEqual(len(doc["documents"]), 1)

    def test_preset_kind_has_an_array(self) -> None:
        self.write(kind="preset")
        doc, errors = validate_entries.load_catalog()
        self.assertEqual(errors, [])
        self.assertEqual(len(doc["presets"]), 1)

    def test_wrong_hash_is_refused_and_left_out(self) -> None:
        self.write(sha256="0" * 64)
        doc, errors = validate_entries.load_catalog()
        self.assertTrue(any("sha256 does not match" in e for e in errors))
        self.assertEqual(doc["rules"], [])
        self.assertEqual(validate_entries.main(), 1)

    def test_file_outside_its_folder_is_refused(self) -> None:
        self.write(file="catalog/index.json")
        _, errors = validate_entries.load_catalog()
        self.assertTrue(any("file must be a path under" in e for e in errors))

    def test_path_escape_is_refused(self) -> None:
        self.write(file=f"catalog/files/{ENTRY_ID}/../../index.json")
        _, errors = validate_entries.load_catalog()
        self.assertTrue(any("one plain file" in e for e in errors))

    def test_download_url_must_point_at_the_file(self) -> None:
        self.write(download_url="https://example.com/other.md")
        _, errors = validate_entries.load_catalog()
        self.assertTrue(any("download_url must end with" in e for e in errors))

    def test_secret_in_the_file_is_refused(self) -> None:
        self.write(content="key: ghp_abcdefghijklmnopqrstuvwxyz0123456789\n")
        _, errors = validate_entries.load_catalog()
        self.assertTrue(any("must not contain secrets" in e for e in errors))

    def test_file_name_must_match_id(self) -> None:
        self.write()
        os.rename(f"catalog/entries/{ENTRY_ID}.json", "catalog/entries/other-name.json")
        _, errors = validate_entries.load_catalog()
        self.assertTrue(any("file name must be" in e for e in errors))

    def test_orphan_folder_is_reported(self) -> None:
        os.makedirs("catalog/files/ml-orphan")
        Path("catalog/files/ml-orphan/x.md").write_text("x", encoding="utf-8")
        _, errors = validate_entries.load_catalog()
        self.assertTrue(any("names this folder" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
