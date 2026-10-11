from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import errno
import json
from pathlib import Path
import tempfile
import threading
import stat
from time import monotonic, sleep
import unittest
from unittest.mock import patch
import zipfile
import zlib

from PIL import Image
import requests

from engine import Engine  # noqa: F401 - establishes the project's import order
from engine.file import artwork


def picture(color="blue"):
    output = BytesIO()
    Image.new("RGB", (20, 30), color).save(output, "PNG")
    return output.getvalue()


def fixture(colors=("blue",), catalog_id="fixture-v1"):
    cards, files, images = {}, [], {}
    for index, color in enumerate(colors, 1):
        card_id = f"{index:05}"
        data = picture(color)
        images[card_id] = data
        cards[card_id] = {"sha256": sha256(data).hexdigest(), "bytes": len(data),
                          "width": 20, "height": 30, "format": "png", "pack_id": "core"}
        files.append(card_id)
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        seen = set()
        for card_id, card in cards.items():
            name = artwork.ArtworkManifest.member_name(card)
            if name not in seen:
                archive.writestr(name, images[card_id])
                seen.add(name)
    pack = output.getvalue()
    manifest = {"schema_version": 1, "catalog_id": catalog_id, "release_ready": True,
                "cards": cards, "aliases": {"reprint": "00001"},
                "packs": {"core": {"url": "https://artwork.example/core.zip",
                                      "sha256": sha256(pack).hexdigest(), "bytes": len(pack), "files": files}}}
    return manifest, pack, images


class FakeResponse:
    def __init__(self, body, offset=0, *, status=200, fault=None, delay=None):
        self.body = body
        self.offset = offset
        self.status_code = status
        self.headers = {"Content-Length": str(len(body) - offset)}
        if status == 206:
            self.headers["Content-Range"] = f"bytes {offset}-{len(body) - 1}/{len(body)}"
        self.fault = fault
        self.delay = delay

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def iter_content(self, _size):
        if self.delay:
            self.delay()
        body = self.body[self.offset:]
        midpoint = max(1, len(body) // 2)
        yield body[:midpoint]
        if self.fault:
            self.fault()
        yield body[midpoint:]


class FakeServer:
    def __init__(self, body):
        self.body = body
        self.calls = []
        self.lock = threading.Lock()
        self.response = None

    def session(self):
        server = self

        class Session:
            def __init__(self):
                self.headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def get(self, url, *, headers, stream, timeout):
                with server.lock:
                    server.calls.append((url, dict(headers)))
                    number = len(server.calls)
                if server.response:
                    return server.response(number, headers)
                offset = int(headers["Range"].split("=")[1].split("-")[0]) if "Range" in headers else 0
                return FakeResponse(server.body, offset, status=206 if offset else 200)

        return Session()


class TestArtworkLibrary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest, self.pack, self.images = fixture(("blue", "red"))
        self.server = FakeServer(self.pack)
        self.libraries = []
        self.addCleanup(self.close_libraries)

    def close_libraries(self):
        for library in self.libraries:
            library.shutdown()

    def library(self, manifest=None, **kwargs):
        library = artwork.ArtworkLibrary(artwork.ArtworkManifest(manifest or self.manifest),
                                         self.root / "library", session_factory=self.server.session, **kwargs)
        self.libraries.append(library)
        return library

    def wait(self, library, state):
        deadline = monotonic() + 5
        while monotonic() < deadline:
            result = library.status()
            if result["state"] == state:
                return result
            sleep(0.01)
        self.fail(f"Expected {state}, received {library.status()}")

    def installed(self):
        library = self.library()
        library.start()
        self.wait(library, "ready")
        return library

    def test_installs_verified_pack_and_reprint_with_readiness_marker(self):
        library = self.installed()
        self.assertEqual(library.get_image("00001"), self.images["00001"])
        self.assertEqual(library.get_image("reprint"), self.images["00001"])
        self.assertTrue(library.ready_for(["00001", "reprint"]))
        self.assertEqual(library.image_state("00001"), "ready")
        self.assertEqual(library.image_state("unknown"), "unavailable")
        self.assertTrue((library.root / "ready.json").is_file())
        self.assertEqual(list((library.root / "downloads").glob("*.part")), [])
        self.assertEqual(len(self.server.calls), 1)
        status = library.status()
        self.assertEqual(status["installed_bytes"], sum(map(len, self.images.values())))
        self.assertEqual(status["required_bytes"], 0)
        self.assertEqual(status["downloaded_bytes"], len(self.pack))

    def test_two_installations_reuse_persistent_library_without_network(self):
        first = self.installed()
        first.shutdown()
        second = self.library()
        second.start()
        self.assertTrue(second.status()["ready"])
        self.assertEqual(second.get_image("00002"), self.images["00002"])
        self.assertEqual(len(self.server.calls), 1)

    def test_shared_os_lock_prevents_duplicate_pack_downloads(self):
        def response(_number, _headers):
            return FakeResponse(self.pack, delay=lambda: sleep(0.1))
        self.server.response = response
        first, second = self.library(), self.library()
        first.start()
        second.start()
        self.wait(first, "ready")
        self.wait(second, "ready")
        self.assertEqual(len(self.server.calls), 1)

    def test_pack_downloads_use_at_most_two_workers(self):
        manifest = {"schema_version": 1, "catalog_id": "several", "release_ready": True,
                    "cards": {}, "packs": {}, "aliases": {}}
        bodies = {}
        for index, color in enumerate(("blue", "red", "green", "yellow")):
            item, body, _ = fixture((color,))
            card_id, pack_id = f"{index + 1:05}", f"pack{index}"
            card = item["cards"]["00001"]
            card["pack_id"] = pack_id
            manifest["cards"][card_id] = card
            pack = item["packs"]["core"]
            pack.update(url=f"https://artwork.example/{pack_id}.zip", files=[card_id])
            manifest["packs"][pack_id] = pack
            bodies[pack["url"]] = body
        counter = {"active": 0, "maximum": 0}
        lock = threading.Lock()
        def delay():
            with lock:
                counter["active"] += 1
                counter["maximum"] = max(counter["maximum"], counter["active"])
            sleep(0.05)
            with lock:
                counter["active"] -= 1
        self.server.response = lambda number, _headers: FakeResponse(
            bodies[self.server.calls[number - 1][0]], delay=delay)
        library = self.library(manifest)
        library.start()
        self.wait(library, "ready")
        self.assertEqual(counter["maximum"], 2)
        self.assertEqual(len(self.server.calls), 4)

    def test_paused_transfer_resumes_from_written_bytes(self):
        library = self.library()
        self.server.response = lambda number, headers: (
            FakeResponse(self.pack, fault=library.pause) if number == 1 else
            FakeResponse(self.pack, int(headers["Range"].split("=")[1].split("-")[0]), status=206))
        library.start()
        self.wait(library, "paused")
        deadline = monotonic() + 2
        while library._active and monotonic() < deadline:
            sleep(0.01)
        partial = next((library.root / "downloads").glob("*.part"))
        self.assertEqual(partial.stat().st_size, len(self.pack) // 2)
        library.resume()
        self.wait(library, "ready")
        self.assertEqual(self.server.calls[1][1]["Range"], f"bytes={len(self.pack) // 2}-")

    def test_interrupted_transfer_retries_with_range_after_restart(self):
        def disconnect():
            raise requests.ConnectionError("connection interrupted")
        self.server.response = lambda _number, _headers: FakeResponse(self.pack, fault=disconnect)
        first = self.library()
        first.start()
        self.wait(first, "error")
        first.shutdown()
        self.server.response = None
        second = self.library()
        second.start()
        self.wait(second, "ready")
        self.assertIn("Range", self.server.calls[-1][1])

    def test_server_ignoring_range_restarts_without_concatenation(self):
        library = self.library()
        pack_hash = self.manifest["packs"]["core"]["sha256"]
        partial = library.root / "downloads" / f"{pack_hash}.part"
        partial.parent.mkdir(parents=True)
        partial.write_bytes(self.pack[:10])
        self.server.response = lambda *_: FakeResponse(self.pack)
        library.start()
        self.wait(library, "ready")
        self.assertEqual(library.get_image("00001"), self.images["00001"])

    def test_wrong_resume_range_is_rejected(self):
        library = self.library()
        def response(*_):
            result = FakeResponse(self.pack, status=206)
            result.headers["Content-Range"] = "bytes 1-2/3"
            return result
        self.server.response = response
        library.start()
        self.assertIn("resume range", self.wait(library, "error")["error"])
        self.assertFalse((library.root / "ready.json").exists())

    def test_hash_mismatch_is_not_installed_and_partial_is_removed(self):
        self.server.body = b"x" * len(self.pack)
        library = self.library()
        library.start()
        self.assertIn("hash mismatch", self.wait(library, "error")["error"])
        self.assertIsNone(library.get_image("00001"))
        self.assertEqual(list((library.root / "downloads").glob("*.part")), [])

    def test_retry_recovers_after_provider_failure(self):
        self.server.response = lambda *_: FakeResponse(b"", status=503)
        library = self.library()
        library.start()
        self.wait(library, "error")
        self.assertEqual(library.image_state("00001"), "error")
        self.server.response = None
        library.retry()
        self.wait(library, "ready")

    def test_corrupt_cached_image_cannot_preserve_ready_on_restart(self):
        first = self.installed()
        card = self.manifest["cards"]["00001"]
        first._object_path(card).write_bytes(b"x" * card["bytes"])
        second = self.library()
        self.assertFalse(second.status()["can_play"])
        self.assertFalse(second.ready_for(["00001"]))
        second.start()
        self.wait(second, "ready")
        self.assertEqual(second.get_image("00001"), self.images["00001"])

    def test_previous_ready_catalog_remains_usable_during_update(self):
        self.installed()
        updated, pack, images = fixture(("green", "red"), "fixture-v2")
        self.server.body = pack
        library = self.library(updated)
        self.assertFalse(library.status()["ready"])
        self.assertTrue(library.status()["has_previous"])
        self.assertTrue(library.status()["can_play"])
        self.assertEqual(library.get_image("00001"), self.images["00001"])
        self.assertNotEqual(library.image_state("00001"), "ready")
        self.server.response = lambda *_: FakeResponse(pack, status=503)
        library.start()
        self.wait(library, "error")
        self.assertEqual(library.image_state("00001"), "error")
        self.assertEqual(library.get_image("00001"), self.images["00001"])
        self.server.response = None
        library.retry()
        self.wait(library, "ready")
        self.assertEqual(library.get_image("00001"), images["00001"])
        self.assertEqual(library.image_state("00001"), "ready")

    def test_draft_catalog_never_downloads_or_unlocks_new_install(self):
        self.manifest["release_ready"] = False
        library = self.library()
        library.start()
        self.assertEqual(library.status()["state"], "incomplete")
        self.assertFalse(library.status()["ready"])
        self.assertFalse(library.status()["can_play"])
        self.assertIn("incomplete", library.status()["error"])
        self.assertEqual(self.server.calls, [])

    def test_draft_does_not_trust_preexisting_matching_objects(self):
        first = self.installed()
        draft = deepcopy(self.manifest)
        draft.update(catalog_id="unapproved", release_ready=False)
        # Prior approved art remains permitted; current draft bytes cannot
        # independently qualify an installation with no completion marker.
        (first.root / "ready.json").unlink()
        library = self.library(draft)
        self.assertFalse(library.status()["can_play"])
        self.assertIsNone(library.get_image("00001"))
        self.assertFalse(library.ready_for(["00001"]))

    def test_empty_draft_manifest_reports_incomplete(self):
        library = self.library({"schema_version": 1, "catalog_id": "draft", "release_ready": False,
                                "cards": {}, "packs": {}, "aliases": {}})
        library.start()
        self.assertEqual(library.status()["state"], "incomplete")
        self.assertFalse(library.status()["can_play"])

    def test_verified_legacy_files_migrate_without_modification_or_network(self):
        legacy = self.root / "legacy"
        legacy.mkdir()
        for card_id, data in self.images.items():
            (legacy / f"{card_id}.png").write_bytes(data)
        library = self.library(legacy_roots=[legacy])
        library.start()
        self.wait(library, "ready")
        self.assertEqual(self.server.calls, [])
        self.assertEqual((legacy / "00001.png").read_bytes(), self.images["00001"])

    def test_unverified_legacy_art_is_preserved_but_not_trusted(self):
        legacy = self.root / "legacy"
        legacy.mkdir()
        old_art = picture("yellow")
        (legacy / "00001.png").write_bytes(old_art)
        library = self.library(legacy_roots=[legacy])
        library.start()
        self.wait(library, "ready")
        self.assertEqual(library.get_image("00001"), self.images["00001"])
        self.assertEqual((legacy / "00001.png").read_bytes(), old_art)

    def test_duplicate_content_uses_one_archive_member(self):
        manifest, pack, images = fixture(("blue", "blue"))
        self.server.body = pack
        library = self.library(manifest)
        library.start()
        self.wait(library, "ready")
        self.assertEqual(len(list((library.root / "objects").iterdir())), 1)
        self.assertEqual(library.status()["installed_bytes"], len(images["00001"]))

    def test_updated_card_reuses_old_pack_inventory_for_unchanged_cards(self):
        self.installed().shutdown()
        manifest = deepcopy(self.manifest)
        manifest["catalog_id"] = "updated-crop"
        old_pack = manifest["packs"]["core"]
        old_pack["members"] = {artwork.ArtworkManifest.member_name(card): deepcopy(card)
                               for card in manifest["cards"].values()}
        old_pack["files"] = ["00002"]
        replacement, new_pack, images = fixture(("green",))
        new_card = replacement["cards"]["00001"]
        new_card["pack_id"] = "correction"
        manifest["cards"]["00001"] = new_card
        manifest["packs"]["correction"] = replacement["packs"]["core"]
        manifest["packs"]["correction"]["url"] = "https://artwork.example/correction.zip"
        self.server.body = new_pack
        updated = self.library(manifest)
        updated.start()
        self.wait(updated, "ready")
        self.assertEqual(len(self.server.calls), 2)
        self.assertIn("correction.zip", self.server.calls[-1][0])
        self.assertEqual(updated.get_image("00001"), images["00001"])
        self.assertEqual(updated.get_image("00002"), self.images["00002"])
        # A fresh installation can validate and use the unchanged portion of
        # the original immutable archive without installing its obsolete image.
        fresh_root = self.root / "fresh"
        self.server.response = lambda number, _headers: FakeResponse(
            new_pack if "correction" in self.server.calls[number - 1][0] else self.pack)
        fresh = artwork.ArtworkLibrary(artwork.ArtworkManifest(manifest), fresh_root,
                                        session_factory=self.server.session)
        self.libraries.append(fresh)
        fresh.start()
        self.wait(fresh, "ready")
        self.assertEqual(fresh.get_image("00001"), images["00001"])
        self.assertFalse(fresh._object_path(self.manifest["cards"]["00001"]).exists())

    def test_bad_archive_path_and_extra_member_are_rejected(self):
        output = BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("../../outside.png", self.images["00001"])
        self.server.body = output.getvalue()
        pack = self.manifest["packs"]["core"]
        pack.update(sha256=sha256(self.server.body).hexdigest(), bytes=len(self.server.body))
        library = self.library()
        library.start()
        self.assertIn("unexpected", self.wait(library, "error")["error"])
        self.assertFalse((self.root / "outside.png").exists())

    def test_symlink_archive_member_is_rejected_even_with_expected_name(self):
        output = BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            for card_id, card in self.manifest["cards"].items():
                info = zipfile.ZipInfo(artwork.ArtworkManifest.member_name(card))
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, self.images[card_id])
        self.server.body = output.getvalue()
        self.manifest["packs"]["core"].update(sha256=sha256(self.server.body).hexdigest(), bytes=len(self.server.body))
        library = self.library()
        library.start()
        self.assertIn("archive member", self.wait(library, "error")["error"])

    def test_stream_cannot_exceed_manifest_byte_limit(self):
        def response(*_):
            result = FakeResponse(self.pack + self.pack)
            result.headers["Content-Length"] = str(len(self.pack))
            return result
        self.server.response = response
        library = self.library()
        library.start()
        self.assertIn("exceeds", self.wait(library, "error")["error"])
        self.assertFalse((library.root / "ready.json").exists())

    def test_declared_dimensions_must_match_decoded_image(self):
        self.manifest["cards"]["00001"]["width"] = 21
        library = self.library()
        library.start()
        self.assertIn("dimensions mismatch", self.wait(library, "error")["error"])
        self.assertFalse((library.root / "ready.json").exists())

    def test_disk_error_is_reported_without_qualifying_as_ready(self):
        library = self.library()
        with patch.object(artwork, "_atomic_write", side_effect=OSError("disk full")):
            library.start()
            self.assertIn("disk full", self.wait(library, "error")["error"])
        self.assertFalse(library.status()["can_play"])
        library.retry()
        self.wait(library, "ready")

    def test_verified_completed_library_needs_no_writes_or_network_on_restart(self):
        self.installed().shutdown()
        library = self.library()
        with patch.object(artwork, "_atomic_write", side_effect=OSError("disk full/read only")) as write:
            library.start()
            self.assertTrue(library.status()["can_play"])
            self.assertEqual(library.status()["state"], "ready")
            self.assertEqual(library.get_image("00001"), self.images["00001"])
            write.assert_not_called()
        self.assertEqual(len(self.server.calls), 1)

    def test_completed_catalog_rehashes_but_does_not_redecode_unchanged_images(self):
        first = self.installed()
        first.shutdown()
        with patch.object(artwork, "_validate_image", side_effect=AssertionError("unnecessary decode")):
            library = self.library()
            self.assertTrue(library.status()["ready"])
            self.assertEqual(library.get_image("00001"), self.images["00001"])
            card = self.manifest["cards"]["00001"]
            library._object_path(card).write_bytes(b"x" * card["bytes"])
            self.assertIsNone(library.get_image("00001"))
            self.assertFalse(library.status()["ready"])

    def test_missing_completion_proof_forces_full_decode_on_reopen(self):
        first = self.installed()
        first.shutdown()
        (first.root / "ready.json").unlink()
        with patch.object(artwork, "_validate_image", wraps=artwork._validate_image) as validate:
            library = self.library()
            self.assertTrue(library.status()["ready"])
            self.assertEqual(validate.call_count, len(self.images))

    def test_completed_catalog_cannot_skip_checks_for_changed_metadata(self):
        self.installed().shutdown()
        changed = deepcopy(self.manifest)
        changed["cards"]["00001"]["width"] += 1
        library = self.library(changed)
        self.assertFalse(library.status()["ready"])
        self.assertIsNone(library.get_image("00001"))
        changed["catalog_id"] = "new-revision-with-bad-dimensions"
        updated = self.library(changed)
        self.assertFalse(updated.status()["ready"])
        self.assertTrue(updated.status()["has_previous"])
        self.assertEqual(updated.get_image("00001"), self.images["00001"])
        self.assertNotEqual(updated.image_state("00001"), "ready")

    def test_failed_completion_marker_can_retry_without_redownloading(self):
        library = self.library()
        original = artwork._atomic_write
        def write(path, data):
            if path.name == "ready.json":
                raise OSError("disk full writing completion marker")
            return original(path, data)
        with patch.object(artwork, "_atomic_write", side_effect=write):
            library.start()
            self.assertIn("completion marker", self.wait(library, "error")["error"])
            self.assertFalse(library.status()["can_play"])
        self.assertFalse((library.root / "ready.json").exists())
        library.retry()
        self.wait(library, "ready")
        self.assertEqual(len(self.server.calls), 1)

    def test_disk_full_mid_transfer_retains_actual_prefix_for_range_retry(self):
        library = self.library()
        original = Path.open
        written = []
        class DiskFullFile:
            def __init__(self, output):
                self.output = output
            def __enter__(self):
                return self
            def __exit__(self, *_):
                self.output.close()
            def write(self, data):
                prefix = data[:max(1, len(data) // 2)]
                self.output.write(prefix)
                self.output.flush()
                written.append(len(prefix))
                raise OSError(errno.ENOSPC, "disk full during transfer")
        def open_file(path, mode="r", *args, **kwargs):
            output = original(path, mode, *args, **kwargs)
            return DiskFullFile(output) if path.suffix == ".part" and mode == "wb" else output
        with patch.object(Path, "open", open_file):
            library.start()
            self.assertIn("disk full during transfer", self.wait(library, "error")["error"])
        self.assertFalse(library.status()["can_play"])
        partial = next((library.root / "downloads").glob("*.part"))
        self.assertEqual(partial.stat().st_size, sum(written))
        library.retry()
        self.wait(library, "ready")
        self.assertEqual(self.server.calls[1][1]["Range"], f"bytes={sum(written)}-")
        self.assertEqual(library.get_image("00001"), self.images["00001"])

    def test_corrupt_deflate_payload_reports_error_and_worker_survives_retry(self):
        output = BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for card_id, card in self.manifest["cards"].items():
                archive.writestr(artwork.ArtworkManifest.member_name(card), self.images[card_id])
        body = bytearray(output.getvalue())
        with zipfile.ZipFile(BytesIO(body)) as archive:
            member = archive.infolist()[0]
            # Set the first DEFLATE block type to reserved (11), preserving the
            # ZIP header and declared inventory so decompression is exercised.
            offset = member.header_offset + 30 + len(member.filename.encode()) + len(member.extra)
            body[offset] = 0x07
        with zipfile.ZipFile(BytesIO(body)) as archive:
            with self.assertRaises(zlib.error):
                archive.read(archive.infolist()[0])
        self.server.body = bytes(body)
        pack = self.manifest["packs"]["core"]
        pack.update(sha256=sha256(body).hexdigest(), bytes=len(body))
        library = self.library()
        library.start()
        self.assertIn("decompress", self.wait(library, "error")["error"])
        self.assertFalse(library.status()["can_play"])
        self.assertTrue(all(thread.is_alive() for thread in library._threads))
        # An immutable malformed published pack remains an explicit error on
        # retry rather than silently losing its worker and hanging forever.
        library.retry()
        self.wait(library, "error")

    def test_non_contention_os_lock_error_does_not_loop_forever(self):
        if artwork.sys.platform == "win32":
            target = "msvcrt.locking"
        else:
            target = "fcntl.flock"
        library = self.library()
        with patch(target, side_effect=OSError(errno.EINVAL, "unsupported lock")):
            library.start()
            self.assertIn("unsupported lock", self.wait(library, "error")["error"])
        self.assertEqual(self.server.calls, [])
        library.retry()
        self.wait(library, "ready")

    def test_repair_does_not_rewrite_valid_objects_when_disk_is_tight(self):
        library = self.installed()
        damaged = library._object_path(self.manifest["cards"]["00001"])
        preserved = library._object_path(self.manifest["cards"]["00002"])
        damaged.write_bytes(b"x" * len(self.images["00001"]))
        original = artwork._atomic_write
        writes = []
        def write(path, data):
            writes.append(path)
            if path == preserved:
                raise OSError("not enough space to rewrite an intact object")
            return original(path, data)
        with patch.object(artwork, "_atomic_write", side_effect=write):
            self.assertIsNone(library.get_image("00001"))
            self.wait(library, "ready")
        self.assertIn(damaged, writes)
        self.assertNotIn(preserved, writes)

    def test_low_disk_space_stops_before_network(self):
        library = self.library()
        with patch.object(artwork.shutil, "disk_usage", return_value=type("Disk", (), {"free": 0})()):
            library.start()
            self.assertIn("free space", self.wait(library, "error")["error"])
        self.assertEqual(self.server.calls, [])

    def test_initial_and_resumed_storage_estimate_includes_two_temp_packs(self):
        library = self.library()
        status = library.status()
        self.assertEqual(status["total_installed_bytes"], sum(map(len, self.images.values())))
        self.assertEqual(status["required_storage_bytes"], sum(map(len, self.images.values())) + len(self.pack))

    def test_resumed_status_counts_saved_prefix_without_requiring_its_space_again(self):
        library = self.library()
        part = library.root / "downloads" / f"{self.manifest['packs']['core']['sha256']}.part"
        part.parent.mkdir(parents=True)
        saved = len(self.pack) // 2
        part.write_bytes(self.pack[:saved])
        reopened = self.library()
        status = reopened.status()
        self.assertEqual(status["downloaded_bytes"], saved)
        self.assertEqual(status["packs"]["core"]["downloaded_bytes"], saved)
        self.assertEqual(status["required_bytes"], len(self.pack) - saved)
        self.assertEqual(status["required_storage_bytes"], sum(map(len, self.images.values())) + len(self.pack) - saved)

    def test_explicit_generated_and_bundled_ids_only_are_readiness_exemptions(self):
        self.manifest.update(generated={"dummy_minion": "Uses the generated encounter back"},
                             bundled={"player": "Bundled player card back"})
        self.manifest["aliases"]["generated_alias"] = "dummy_minion"
        library = self.library()
        self.assertTrue(library.ready_for(["dummy_minion", "player", "generated_alias"]))
        self.assertFalse(library.has_image_id("generated_alias"))
        self.assertFalse(library.ready_for(["new_unknown_card"]))
        self.assertFalse(library.ready_for(["00001"]))

    def test_missing_or_corrupt_manifest_returns_diagnostics_facade(self):
        path = self.root / "manifest.json"
        for contents in (None, "{malformed}"):
            if contents is not None:
                path.write_text(contents, encoding="utf-8")
            library = artwork.load_artwork_library(path, root=self.root / "library")
            self.assertIsInstance(library, artwork.UnavailableArtworkLibrary)
            self.assertFalse(library.status()["can_play"])
            self.assertEqual(library.image_state("00001"), "unavailable")
            library.start()
            library.pause()
            library.resume()
            library.retry()
            library.shutdown()

    def test_malformed_pack_url_returns_diagnostics_instead_of_crashing(self):
        self.manifest["packs"]["core"]["url"] = {"unexpected": "object"}
        path = self.root / "malformed-manifest.json"
        path.write_text(json.dumps(self.manifest), encoding="utf-8")
        library = artwork.load_artwork_library(path, root=self.root / "library")
        self.assertIsInstance(library, artwork.UnavailableArtworkLibrary)
        self.assertIn("pack URL", library.status()["error"])

    def test_corruption_after_warm_start_automatically_queues_repair(self):
        self.installed().shutdown()
        library = self.library()
        library.start()
        card = self.manifest["cards"]["00001"]
        library._object_path(card).write_bytes(b"x" * card["bytes"])
        self.assertIsNone(library.get_image("00001"))
        self.wait(library, "ready")
        self.assertEqual(library.get_image("00001"), self.images["00001"])

    def test_manifest_rejects_bad_hash_alias_cycles_and_large_packs(self):
        for update in (lambda value: value["cards"]["00001"].update(sha256="bad"),
                       lambda value: value.update(aliases={"a": "b", "b": "a"}),
                       lambda value: value["packs"]["core"].update(bytes=artwork.MAX_PACK_BYTES + 1),
                       lambda value: value["packs"]["core"].update(url="file:///tmp/art.zip"),
                       lambda value: value["packs"]["core"].update(files=["00001"]),
                       lambda value: value.update(catalog_id="../outside")):
            value = deepcopy(self.manifest)
            update(value)
            with self.assertRaises(artwork.ArtworkError):
                artwork.ArtworkManifest(value)

    def test_user_data_defaults_and_explicit_artwork_override(self):
        with patch.object(artwork.sys, "platform", "win32"), patch.dict(artwork.os.environ, {"LOCALAPPDATA": str(self.root)}):
            self.assertEqual(artwork.default_artwork_folder(), self.root / "Marvel Champions Digital" / "artwork")
        with patch.object(artwork.sys, "platform", "linux"), patch.dict(artwork.os.environ, {"XDG_DATA_HOME": str(self.root)}):
            self.assertEqual(artwork.default_artwork_folder(), self.root / "marvel-champions-digital" / "artwork")
        with patch.object(artwork.ARTWORK_FOLDER, "value", str(self.root / "portable")):
            self.assertEqual(artwork.artwork_folder(), self.root / "portable")


if __name__ == "__main__":
    unittest.main()
