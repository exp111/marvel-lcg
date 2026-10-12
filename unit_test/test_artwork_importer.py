"""Offline checks for the maintainer artwork pipeline; never contacts providers."""
from copy import deepcopy
from io import BytesIO
import importlib.util
import json
from pathlib import Path
import stat
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
import zipfile

from PIL import Image

SOURCE = Path(__file__).resolve().parents[1] / "packaging" / "artwork" / "importer.py"
SPEC = importlib.util.spec_from_file_location("artwork_importer", SOURCE)
artwork = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artwork)

URL = "https://steamusercontent-a.akamaihd.net/ugc/123/ABCDE/"
BACK_URL = "https://steamusercontent-a.akamaihd.net/ugc/456/FEDCB/"


class TestArtworkImporter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cards = self.root / "cards.json"
        self.cards.write_text(json.dumps({"core": [
            {"card_id": "10001", "name": "Red Card", "type": "Event", "set_name": "Test"},
            {"card_id": "10002", "name": "Blue Card", "type": "Event", "set_name": "Test"},
            {"card_id": "20001", "full_link": "10001"},
        ]}), encoding="utf-8")
        self.sheet = Image.new("RGB", (400, 300), "red")
        self.sheet.paste("blue", (200, 0, 400, 300))
        raw = BytesIO()
        self.sheet.save(raw, format="PNG")
        self.raw = raw.getvalue()
        self.sha = artwork.digest(self.raw)
        self.sheets = self.root / "sheets"
        self.sheets.mkdir()
        (self.sheets / self.sha).write_bytes(self.raw)
        deck = {"7": {"FaceURL": URL, "BackURL": BACK_URL, "NumWidth": 2,
                      "NumHeight": 1, "UniqueBack": False}}
        # Old CardID prefixes deliberately differ from the scoped CustomDeck.
        self.snapshot = {"LuaScript": "raise an exception if anyone executes me",
                         "ObjectStates": [{"GUID": "red", "Name": "Card", "Nickname": "Red Card",
                                           "CardID": 9900, "CustomDeck": deck},
                                          {"GUID": "blue", "Name": "Card", "Nickname": "Blue Card",
                                           "CardID": 9901, "CustomDeck": deck}]}
        self.pin = {"snapshot": {"url": URL, "sha256": "a" * 64, "bytes": 100}}
        self.mapping = artwork.inspect(self.snapshot, self.cards, self.pin, self.root / "inspect")

    def approve(self):
        for entry in self.mapping["mappings"].values():
            entry["reviewed"] = True
            entry["review_note"] = "Fixture crop visually identified by known solid color"
            entry["source"]["sheet_sha256"] = self.sha

    def build(self, directory="output", **kwargs):
        return artwork.build(self.mapping, self.cards, self.snapshot, self.sheets,
                             self.root / directory, "test-v1", "https://example.org/artwork/v1", **kwargs)

    def test_inspection_never_certifies_candidates(self):
        self.assertEqual(len(self.mapping["mappings"]), 2)
        self.assertTrue(all(entry["reviewed"] is False for entry in self.mapping["mappings"].values()))
        self.assertFalse(artwork.coverage(self.mapping, self.cards)["release_ready"])
        self.assertEqual(self.mapping["mappings"]["10002"]["source"]["deck_key"], "7")

    def test_bson_decode_and_reject_invalid_boundaries(self):
        string = b"LuaScript\0" + struct.pack("<i", 8) + b"ignored\0"
        document = b"\x02" + string
        raw = struct.pack("<i", len(document) + 5) + document + b"\0"
        self.assertEqual(artwork.decode_snapshot(raw), {"LuaScript": "ignored"})
        for invalid in (raw[:-1], raw + b"extra", b"\x01\0\0\0\0"):
            with self.assertRaises(ValueError):
                artwork.decode_snapshot(invalid)

    def test_snapshot_requires_exact_raw_hash(self):
        raw = json.dumps(self.snapshot).encode()
        path = self.root / "snapshot"
        path.write_bytes(raw)
        pin = {"snapshot": {"sha256": artwork.digest(raw), "bytes": len(raw)}}
        self.assertEqual(artwork.load_snapshot(path, pin), self.snapshot)
        path.write_bytes(raw + b" ")
        with self.assertRaises(ValueError):
            artwork.load_snapshot(path, pin)

    def test_source_url_and_source_object_are_verified(self):
        self.approve()
        for url in ("http://steamusercontent-a.akamaihd.net/ugc/123/a/", "https://example.org/ugc/123/a/",
                    "https://steamusercontent-a.akamaihd.net@evil.test/ugc/123/a/"):
            with self.assertRaises(ValueError):
                artwork.source_url(url)
        original = self.mapping["mappings"]["10001"]
        for key, changed in (("sheet_url", BACK_URL), ("index", 1), ("guid", "other")):
            entry = deepcopy(original)
            entry["source"][key] = changed
            with self.assertRaises(ValueError):
                artwork.validate_source(entry, self.snapshot)

    def test_native_dimensions_correct_tile_and_rotation(self):
        self.approve()
        entry = deepcopy(self.mapping["mappings"]["10002"])
        entry["rotation"] = 90
        raw, width, height, format = artwork.extract(entry, self.sheets / self.sha)
        self.assertEqual((width, height, format), (300, 200, "jpg"))
        with Image.open(BytesIO(raw)) as image:
            red, green, blue = image.getpixel((50, 50))
            self.assertLess(red + green, 10)
            self.assertGreater(blue, 245)

    def test_alternate_sources_restrict_reviewed_publisher_paths(self):
        accepted = (
            "https://cdn.svc.asmodee.net/production-fantasyflightgames/uploads/2026/08/card.png",
            "https://skilledinvestigator.com/wp-content/uploads/2026/07/Jessica-Jones-Hero-Pack-29-5.png",
        )
        for url in accepted:
            self.assertEqual(artwork.alternate_url(url), url)
        for url in (
            "https://cdn.svc.asmodee.net/unrelated/card.png",
            "https://skilledinvestigator.com/wp-content/uploads/2026/09/card.png",
            "https://skilledinvestigator.com/wp-content/uploads/2026/07/card.png?redirect=1",
            "https://skilledinvestigator.com@evil.test/wp-content/uploads/2026/07/card.png",
        ):
            with self.assertRaises(ValueError):
                artwork.alternate_url(url)

    def test_card_encoding_enforces_runtime_limits_without_resizing(self):
        entry = deepcopy(self.mapping["mappings"]["10001"])
        entry["source"].update(columns=1, rows=1, index=0)
        with Image.new("RGB", (4097, 100), "red") as oversized:
            with self.assertRaisesRegex(ValueError, "4096-pixel"):
                artwork.encode_crop(entry, oversized)
        with patch.object(artwork, "MAX_IMAGE_BYTES", 100):
            with self.assertRaisesRegex(ValueError, "16 MiB"):
                artwork.encode_crop(entry, self.sheet)
        with self.assertRaises(ValueError):
            artwork.safe_id("a" * 101)

    def test_verification_rejects_runtime_incompatible_image_metadata(self):
        self.approve()
        catalog = self.build()
        for key, invalid in (("width", 4097), ("height", 4097), ("bytes", 16 * 1024 * 1024 + 1)):
            bad = deepcopy(catalog)
            bad["cards"]["10001"][key] = invalid
            with self.assertRaisesRegex(ValueError, "runtime"):
                artwork.verify(bad, self.root / "output")

    def test_verification_decodes_jpeg_pixels_not_only_header(self):
        self.approve()
        catalog = self.build()
        pack_id, pack = next(iter(catalog["packs"].items()))
        archive_path = self.root / "output" / f"{pack_id}.zip"
        with zipfile.ZipFile(archive_path) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        card = catalog["cards"]["10001"]
        old_name = f"cards/{card['sha256']}.jpg"
        truncated = files.pop(old_name)[:-2]
        # This is the regression: structural verify alone accepts the JPEG.
        with Image.open(BytesIO(truncated)) as image:
            image.verify()
        card.update(sha256=artwork.digest(truncated), bytes=len(truncated))
        new_name = f"cards/{card['sha256']}.jpg"
        files[new_name] = truncated
        pack["members"].pop(old_name)
        pack["members"][new_name] = {key: card[key] for key in ("sha256", "bytes", "width", "height", "format")}
        payload = artwork.zip_bytes(files)
        archive_path.write_bytes(payload)
        pack.update(sha256=artwork.digest(payload), bytes=len(payload))
        with self.assertRaises((OSError, ValueError)):
            artwork.verify(catalog, archive_path.parent)

    def test_verification_rejects_zip_symlink_metadata(self):
        self.approve()
        catalog = self.build()
        pack_id, pack = next(iter(catalog["packs"].items()))
        archive_path = self.root / "output" / f"{pack_id}.zip"
        with zipfile.ZipFile(archive_path) as archive:
            entries = [(info, archive.read(info)) for info in archive.infolist()]
        with zipfile.ZipFile(archive_path, "w") as archive:
            for info, payload in entries:
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, payload)
        pack.update(bytes=archive_path.stat().st_size, sha256=artwork.digest(archive_path.read_bytes()))
        with self.assertRaisesRegex(ValueError, "Unexpected ZIP"):
            artwork.verify(catalog, archive_path.parent)

    def test_shared_sheet_decoded_once(self):
        self.approve()
        with patch.object(artwork.Image, "open", wraps=Image.open) as opened:
            images = dict(artwork.iter_extracted(self.mapping["mappings"], self.sheets))
        self.assertEqual(set(images), {"10001", "10002"})
        self.assertEqual(opened.call_count, 1)

    def test_release_gates_and_deterministic_packs(self):
        with self.assertRaisesRegex(ValueError, "Release blocked"):
            self.build()
        draft = self.build("draft", draft=True)
        self.assertFalse(draft["release_ready"])
        self.approve()
        complete_draft = self.build("complete-draft", draft=True)
        self.assertFalse(complete_draft["release_ready"])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            artwork.verify(complete_draft, self.root / "complete-draft")
        first, second = self.build("one"), self.build("two")
        self.assertEqual(first, second)
        self.assertTrue(first["release_ready"])
        self.assertEqual(first["aliases"], {"20001": "10001"})
        artwork.verify(first, self.root / "one")
        for pack_id in first["packs"]:
            self.assertEqual((self.root / "one" / (pack_id + ".zip")).read_bytes(),
                             (self.root / "two" / (pack_id + ".zip")).read_bytes())

    def test_changed_catalog_cannot_overwrite_immutable_output(self):
        self.approve()
        self.build()
        self.mapping["mappings"]["10002"]["rotation"] = 180
        with self.assertRaisesRegex(ValueError, "different catalog"):
            self.build()

    def test_pack_member_validation_rejects_additional_file(self):
        self.approve()
        catalog = self.build()
        pack_id, metadata = next(iter(catalog["packs"].items()))
        path = self.root / "output" / f"{pack_id}.zip"
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr("../unapproved.txt", b"unapproved")
        metadata["bytes"] = path.stat().st_size
        metadata["sha256"] = artwork.digest(path.read_bytes())
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            artwork.verify(catalog, path.parent)

    def test_pack_splits_before_configured_limit(self):
        self.approve()
        raw, _, _, _ = artwork.extract(self.mapping["mappings"]["10001"], self.sheets / self.sha)
        limit = len(raw) + 350
        with patch.object(artwork, "MAX_PACK_BYTES", limit):
            catalog = self.build()
            self.assertEqual(len(catalog["packs"]), 2)
            self.assertTrue(all(pack["bytes"] <= limit for pack in catalog["packs"].values()))
            artwork.verify(catalog, self.root / "output")

    def test_alias_cycles_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            artwork.canonical("one", {"one": "two", "two": "one"})

    def test_seeded_sheet_fetch_deduplicates_and_does_not_approve(self):
        seed = self.root / "large-sheet.jpg"
        seed.write_bytes(self.raw)  # Actual PNG; extension is deliberately wrong.
        empty_cache = self.root / "new-cache"
        with patch.object(artwork.requests.Session, "get", side_effect=AssertionError("Must not download seeded data")):
            errors = artwork.fetch_sheets(self.mapping, self.snapshot, empty_cache, seeds={URL: seed})
        self.assertEqual(errors, [])
        self.assertEqual((empty_cache / self.sha).read_bytes(), self.raw)
        self.assertEqual(len(artwork.read_json(empty_cache / "sources.json")), 1)
        self.assertTrue(all(not entry["reviewed"] and entry["source"]["sheet_sha256"] == self.sha
                            for entry in self.mapping["mappings"].values()))

    def test_generated_and_bundled_accounting_preserves_aliases(self):
        cards = artwork.read_json(self.cards)
        cards["special"] = [{"card_id": "minion", "name": "Minion", "pic_id": "player"},
                             {"card_id": "challenge", "name": "Challenge"}]
        artwork.write_json(self.cards, cards)
        self.approve()
        self.assertEqual(artwork.coverage(self.mapping, self.cards)["unaccounted_nonnumbered"],
                         ["challenge", "minion", "player"])
        self.mapping["nonnumbered"] = {
            "minion": {"reviewed": True, "disposition": "alias", "reason": "Uses player back"},
            "player": {"reviewed": True, "disposition": "builtin", "reason": "Bundled player back"},
            "challenge": {"reviewed": True, "disposition": "generated", "reason": "Game-generated challenge text"}}
        catalog = self.build()
        self.assertTrue(catalog["release_ready"])
        self.assertEqual(catalog["aliases"]["minion"], "player")
        self.assertIn("player", catalog["bundled"])
        self.assertIn("challenge", catalog["generated"])
        artwork.verify(catalog, self.root / "output")

    def test_previous_unchanged_pack_is_reused(self):
        self.approve()
        old = self.build("old")
        new = self.build("new", previous=old)
        self.assertEqual(new["packs"], old["packs"])
        self.assertEqual(list((self.root / "new").glob("*.zip")), [])

    def test_one_correction_creates_only_a_delta_pack(self):
        self.approve()
        old = self.build("old")
        self.mapping["mappings"]["10002"]["rotation"] = 90
        new = self.build("new", previous=old)
        old_id = old["cards"]["10001"]["pack_id"]
        self.assertEqual(new["cards"]["10001"]["pack_id"], old_id)
        self.assertNotEqual(new["cards"]["10002"]["pack_id"], old_id)
        self.assertEqual(new["packs"][old_id]["files"], ["10001"])
        self.assertEqual(len(new["packs"][old_id]["members"]), 2)
        (self.root / "new" / f"{old_id}.zip").write_bytes((self.root / "old" / f"{old_id}.zip").read_bytes())
        artwork.verify(new, self.root / "new")

    def test_alternate_image_is_pinned_pending_and_rechecked_at_build(self):
        self.approve()
        path = self.root / "alternate.jpg"
        path.write_bytes(self.raw)
        artwork.stage_alternate(self.mapping, "10002", "blue-clean", "https://marvelcdb.com/bundles/cards/10002.jpg",
                                path, self.sha, self.sheets, crop=[200, 0, 400, 300])
        self.assertFalse(self.mapping["mappings"]["10002"]["reviewed"])
        with self.assertRaisesRegex(ValueError, "Release blocked"):
            self.build()
        self.mapping["mappings"]["10002"].update(reviewed=True, review_note="Blue crop inspected; no watermark")
        catalog = self.build()
        self.assertEqual(catalog["cards"]["10002"]["width"], 200)
        self.assertIn("blue-clean", catalog["provenance"]["alternate_sources"])
        (self.sheets / "originals" / self.sha).write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "source hash"):
            self.build("tampered")

    def test_alternate_source_requires_exact_hash_and_allowed_host(self):
        path = self.root / "alternate.png"
        path.write_bytes(self.raw)
        with self.assertRaisesRegex(ValueError, "explicit hash"):
            artwork.stage_alternate(self.mapping, "10002", "test", "https://marvelcdb.com/a.jpg",
                                    path, "0" * 64, self.sheets)
        with self.assertRaisesRegex(ValueError, "supported HTTPS"):
            artwork.stage_alternate(self.mapping, "10002", "test", "https://unreviewed.test/a.jpg",
                                    path, self.sha, self.sheets)

    def test_explicit_crop_cannot_leave_source_bounds(self):
        self.approve()
        entry = self.mapping["mappings"]["10001"]
        entry["source"]["pixel_crop"] = [-1, 0, 200, 300]
        with self.assertRaisesRegex(ValueError, "outside source"):
            artwork.extract(entry, self.sheets / self.sha)

    def test_only_actual_transparency_requires_png(self):
        self.approve()
        entry = self.mapping["mappings"]["10001"]
        for alpha, expected in ((255, "jpg"), (128, "png")):
            with Image.new("RGBA", (400, 300), (0, 0, 255, alpha)) as sheet:
                self.assertEqual(artwork.encode_crop(entry, sheet)[3], expected)
        with Image.new("P", (400, 300), 1) as sheet:
            sheet.putpalette([0, 0, 0, 0, 0, 255] + [0] * 762)
            sheet.info["transparency"] = 0  # The transparent palette entry is unused.
            self.assertEqual(artwork.encode_crop(entry, sheet)[3], "jpg")
            sheet.putpixel((0, 0), 0)
            self.assertEqual(artwork.encode_crop(entry, sheet)[3], "png")

    def test_pdf_page_preserves_vector_text_with_pinned_resolution(self):
        pixmap = SimpleNamespace(tobytes=Mock(return_value=self.raw))
        page = SimpleNamespace(rect=SimpleNamespace(width=177.134, height=251.575),
                               get_pixmap=Mock(return_value=pixmap))
        document = MagicMock()
        document.__enter__.return_value = document
        document.__len__.return_value = 1
        document.__getitem__.return_value = page
        fake_fitz = SimpleNamespace(open=Mock(return_value=document), Matrix=lambda x, y: (x, y))
        with patch.dict("sys.modules", {"fitz": fake_fitz}):
            self.assertEqual(artwork.alternate_image_bytes(b"pdf", "pdf_page", page=0, render_dpi=300), self.raw)
            page.get_pixmap.assert_called_once_with(matrix=(300 / 72, 300 / 72), alpha=False)
            with self.assertRaisesRegex(ValueError, "Invalid PDF page"):
                artwork.alternate_image_bytes(b"pdf", "pdf_page", page=1, render_dpi=300)
            with self.assertRaisesRegex(ValueError, "resolution"):
                artwork.alternate_image_bytes(b"pdf", "pdf_page", page=0, render_dpi=2000)


if __name__ == "__main__":
    unittest.main()
