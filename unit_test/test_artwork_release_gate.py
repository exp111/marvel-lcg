from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artwork_release_gate", ROOT / "packaging/verify_artwork_release.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class TestArtworkReleaseGate(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.cards = self.root / "cards.json"
        self.cards.write_text(json.dumps({"test": [{"card_id": "01001", "name": "Test"},
                                                   {"card_id": "01002", "full_link": "01001"}]}))
        self.mapping = {"source_pin": {"snapshot": {"sha256": "f" * 64}}, "mappings": {
            "01001": {"reviewed": True, "review_note": "Reviewed test fixture", "source": {"sheet_sha256": "a" * 64}}}}
        self.catalog = {"schema_version": 1, "catalog_id": "test", "release_ready": True,
            "cards": {"01001": {"sha256": "b" * 64, "bytes": 20, "width": 10, "height": 20,
                                  "format": "jpg", "pack_id": "test-pack"}},
            "aliases": {"01002": "01001"}, "packs": {"test-pack": {"url": "https://example.test/test.zip",
                "sha256": "c" * 64, "bytes": 100, "files": ["01001"]}}}

    def validate(self):
        self.catalog["provenance"] = {"mapping_sha256": sha256(json.dumps(self.mapping, sort_keys=True).encode()).hexdigest(),
            "cards_sha256": sha256(self.cards.read_bytes()).hexdigest(), "source_pin": self.mapping["source_pin"]}
        return self.write_and_validate()

    def write_and_validate(self):
        mapping_path, catalog_path = self.root / "mapping.json", self.root / "catalog.json"
        mapping_path.write_text(json.dumps(self.mapping))
        catalog_path.write_text(json.dumps(self.catalog))
        return GATE.validate_release(catalog_path, mapping_path, self.cards)

    def test_complete_reviewed_catalog_passes_local_gate(self):
        self.assertEqual(self.validate().catalog_id, "test")

    def test_setting_release_ready_cannot_bypass_an_unreviewed_mapping(self):
        self.mapping["mappings"]["01001"]["reviewed"] = False
        with self.assertRaisesRegex(ValueError, "still need review"):
            self.validate()

    def test_omitted_reprint_alias_is_rejected(self):
        self.catalog["aliases"] = {}
        with self.assertRaisesRegex(ValueError, "does not cover"):
            self.validate()

    def test_manifest_must_match_the_reviewed_mapping_hash(self):
        self.validate()
        self.catalog["provenance"]["mapping_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.write_and_validate()

    def test_new_card_database_cannot_reuse_stale_coverage(self):
        self.validate()
        self.catalog["provenance"]["cards_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "current card database"):
            self.write_and_validate()

    def test_missing_builtin_texture_is_a_release_failure(self):
        self.catalog["bundled"] = {"missing-artwork-texture": "test fixture"}
        with self.assertRaisesRegex(ValueError, "Missing bundled"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
