"""Verified, persistent card artwork, independent of a game installation.

Only a bundled manifest selects remote files. Workshop parsing and image-sheet
processing are maintainer operations; a player's game downloads bounded packs.

Runtime manifest schema (additional provenance/generated/dependencies metadata
is preserved):
  {"schema_version": 1, "catalog_id": "artwork-...", "release_ready": true,
   "cards": {"01001a": {"sha256": "...", "bytes": 123, "width": 710,
              "height": 1030, "format": "jpg", "pack_id": "core-..."}},
   "aliases": {"reprint_id": "01001a"},
   "packs": {"core-...": {"url": "https://...", "sha256": "...",
              "bytes": 456, "files": ["01001a"]}}}
ZIP member names are exactly cards/<image-sha256>.<format>. No directory or
unexpected entries are accepted. A draft (release_ready=false) is inspectable
but cannot start downloads or qualify as a completed catalog.
An optional packs[pack_id].members dictionary maps those ZIP paths to complete
image metadata (sha256, bytes, width, height, format). It preserves an older
pack's exact inventory when only some of its images remain in the new catalog;
files lists only the current card IDs that still reference that pack.
"""

from __future__ import annotations

from collections import deque
from contextlib import contextmanager
import errno
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import threading
from typing import Callable, Iterable
from urllib.parse import urlsplit
import uuid
import zipfile
import zlib

from PIL import Image
import requests

from engine.config import ConfigVariables


ARTWORK_FOLDER = ConfigVariables.Folder("artwork_folder", "")
MAX_PACK_BYTES = 64 * 1024 * 1024
MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_UNPACKED_BYTES = 128 * 1024 * 1024
DOWNLOAD_TIMEOUT = (5, 20)
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")
_FORMATS = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP"}


def default_artwork_folder() -> Path:
    """Do not put the library beside the executable or in a temporary folder."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "Marvel Champions Digital" / "artwork"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Marvel Champions Digital" / "artwork"
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "marvel-champions-digital" / "artwork"


def artwork_folder() -> Path:
    return Path(ARTWORK_FOLDER.value).expanduser() if ARTWORK_FOLDER.value else default_artwork_folder()


class ArtworkError(ValueError):
    pass


class _Interrupted(Exception):
    pass


def _positive_int(value, maximum: int) -> bool:
    return type(value) is int and 0 < value <= maximum


def _safe_id(value) -> bool:
    return isinstance(value, str) and bool(_ID.fullmatch(value)) and value not in (".", "..")


class ArtworkManifest:
    """The small, immutable runtime index, validated before any downloads."""

    def __init__(self, data: dict):
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ArtworkError("Unsupported artwork manifest version")
        if not _safe_id(data.get("catalog_id")):
            raise ArtworkError("Invalid artwork catalog ID")
        self.data = data
        self.catalog_id = data["catalog_id"]
        self.release_ready = data.get("release_ready") is True
        self.cards = data.get("cards")
        self.packs = data.get("packs")
        self.aliases = data.get("aliases", {})
        self.generated = data.get("generated", {})
        self.bundled = data.get("bundled", {})
        if (not isinstance(self.cards, dict) or (not self.cards and self.release_ready)
                or len(self.cards) > 20000):
            raise ArtworkError("The artwork manifest has no valid cards")
        if not isinstance(self.packs, dict) or len(self.packs) > 20000:
            raise ArtworkError("Invalid artwork packs")
        if not isinstance(self.aliases, dict) or len(self.aliases) > 20000:
            raise ArtworkError("Invalid artwork aliases")
        for group in (self.generated, self.bundled):
            if not isinstance(group, dict) or any(not _safe_id(key) or not isinstance(reason, str)
                                                  for key, reason in group.items()):
                raise ArtworkError("Invalid local artwork accounting")
        if set(self.cards) & (set(self.generated) | set(self.bundled)) or set(self.generated) & set(self.bundled):
            raise ArtworkError("Conflicting managed and local artwork IDs")
        digest_metadata = {}
        for card_id, card in self.cards.items():
            if not _safe_id(card_id) or not isinstance(card, dict):
                raise ArtworkError("Invalid artwork card ID")
            if not isinstance(card.get("sha256"), str) or not _HASH.fullmatch(card["sha256"]):
                raise ArtworkError(f"Invalid artwork hash: {card_id}")
            if card.get("format") not in _FORMATS or not _positive_int(card.get("bytes"), MAX_IMAGE_BYTES):
                raise ArtworkError(f"Invalid artwork encoding: {card_id}")
            if not all(_positive_int(card.get(key), 4096) for key in ("width", "height")):
                raise ArtworkError(f"Invalid artwork dimensions: {card_id}")
            if card.get("pack_id") not in self.packs:
                raise ArtworkError(f"Missing artwork pack: {card_id}")
            metadata = tuple(card[key] for key in ("bytes", "width", "height", "format"))
            previous = digest_metadata.setdefault(card["sha256"], metadata)
            if previous != metadata:
                raise ArtworkError("Conflicting metadata for the same artwork hash")
        for pack_id, pack in self.packs.items():
            if not _safe_id(pack_id) or not isinstance(pack, dict):
                raise ArtworkError("Invalid artwork pack ID")
            if not isinstance(pack.get("sha256"), str) or not _HASH.fullmatch(pack["sha256"]):
                raise ArtworkError(f"Invalid artwork pack hash: {pack_id}")
            if not _positive_int(pack.get("bytes"), MAX_PACK_BYTES):
                raise ArtworkError(f"Artwork pack exceeds the size limit: {pack_id}")
            if not isinstance(pack.get("url"), str):
                raise ArtworkError(f"Invalid artwork pack URL: {pack_id}")
            url = urlsplit(pack["url"])
            if url.scheme != "https" or not url.hostname or url.username or url.password or url.fragment:
                raise ArtworkError(f"Artwork pack requires an HTTPS URL: {pack_id}")
            files = pack.get("files")
            expected = {key for key, card in self.cards.items() if card["pack_id"] == pack_id}
            if not isinstance(files, list) or any(not isinstance(item, str) for item in files):
                raise ArtworkError(f"Invalid artwork pack file list: {pack_id}")
            if len(files) != len(set(files)) or set(files) != expected or not files:
                raise ArtworkError(f"Artwork pack membership mismatch: {pack_id}")
            members = self.members(pack_id)
            if not isinstance(members, dict) or not members or len(members) > 20000:
                raise ArtworkError(f"Invalid artwork pack inventory: {pack_id}")
            for name, image in members.items():
                if (not isinstance(image, dict) or not isinstance(image.get("sha256"), str)
                        or not _HASH.fullmatch(image["sha256"]) or image.get("format") not in _FORMATS
                        or not _positive_int(image.get("bytes"), MAX_IMAGE_BYTES)
                        or not all(_positive_int(image.get(key), 4096) for key in ("width", "height"))
                        or name != self.member_name(image)):
                    raise ArtworkError(f"Invalid artwork member metadata: {pack_id}")
                metadata = tuple(image[key] for key in ("bytes", "width", "height", "format"))
                if digest_metadata.setdefault(image["sha256"], metadata) != metadata:
                    raise ArtworkError("Conflicting metadata for the same artwork hash")
            for card_id in files:
                card = self.cards[card_id]
                member = members.get(self.member_name(card), {})
                if any(member.get(key) != card[key] for key in ("sha256", "bytes", "width", "height", "format")):
                    raise ArtworkError(f"Current artwork is missing from pack inventory: {card_id}")
            objects = {image["sha256"]: image["bytes"] for image in members.values()}
            if sum(objects.values()) > MAX_UNPACKED_BYTES:
                raise ArtworkError(f"Artwork pack expansion exceeds the size limit: {pack_id}")
        for alias, target in self.aliases.items():
            if (not _safe_id(alias) or alias in self.cards or alias in self.generated
                    or alias in self.bundled or not _safe_id(target)):
                raise ArtworkError("Invalid artwork alias")
            if self.canonical_id(alias) is None:
                raise ArtworkError(f"Missing or cyclic artwork alias: {alias}")
        self.encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.sha256 = sha256(self.encoded).hexdigest()

    @classmethod
    def load(cls, path: str | Path) -> ArtworkManifest:
        path = Path(path)
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ArtworkError("Artwork manifest is too large")
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def canonical_id(self, card_id: str) -> str | None:
        visited = set()
        while card_id in self.aliases:
            if card_id in visited:
                return None
            visited.add(card_id)
            card_id = self.aliases[card_id]
        return card_id if card_id in self.cards or card_id in self.generated or card_id in self.bundled else None

    def members(self, pack_id: str) -> dict:
        pack = self.packs[pack_id]
        if "members" in pack:
            return pack["members"]
        return {self.member_name(self.cards[key]): self.cards[key] for key in pack["files"]}

    @staticmethod
    def member_name(card: dict) -> str:
        return f"cards/{card['sha256']}.{card['format']}"


def _validate_image(data: bytes, card: dict) -> None:
    if len(data) != card["bytes"] or sha256(data).hexdigest() != card["sha256"]:
        raise ArtworkError("Artwork image hash or size mismatch")
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != _FORMATS[card["format"]] or image.size != (card["width"], card["height"]):
                raise ArtworkError("Artwork image format or dimensions mismatch")
            if getattr(image, "n_frames", 1) != 1:
                raise ArtworkError("Animated images are not card artwork")
            image.verify()
        # Pillow verify() checks file structure but does not decode JPEG pixels.
        with Image.open(BytesIO(data)) as image:
            image.load()
    except Image.DecompressionBombError as error:
        raise ArtworkError("Artwork image exceeds the decoding limit") from error


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _pack_lock(path: Path, check_running: Callable[[], None]):
    """OS-owned lock; a crashed process releases it without stale lock recovery."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        acquired = False
        try:
            while not acquired:
                check_running()
                try:
                    handle.seek(0)
                    if sys.platform == "win32":
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except OSError as error:
                    if error.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                        raise
                    threading.Event().wait(0.1)
            yield
        finally:
            if acquired:
                handle.seek(0)
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class ArtworkLibrary:
    """Two-worker installer plus read-only lookup for the existing image route."""

    def __init__(self, manifest_path: str | Path | ArtworkManifest, root: str | Path | None = None,
                 *, legacy_roots: Iterable[str | Path] = (),
                 legacy_folders: Iterable[str | Path] = (), session_factory=None):
        self.manifest = manifest_path if isinstance(manifest_path, ArtworkManifest) else ArtworkManifest.load(manifest_path)
        self.root = Path(root) if root is not None else artwork_folder()
        self.legacy_folders = tuple(Path(path) for path in (*legacy_roots, *legacy_folders))
        self._session_factory = session_factory or requests.Session
        self._condition = threading.Condition(threading.RLock())
        self._running = False
        self._stopping = False
        self._threads: list[threading.Thread] = []
        self._queue: deque[str] = deque()
        self._active: set[str] = set()
        self._errors: dict[str, str] = {}
        self._downloaded: dict[str, int] = {}
        self._available: set[str] = set()
        self._verified: dict[tuple, tuple[int, int]] = {}
        self._ready = False
        self._paused = False
        self._completed = self._load_completed_catalog()
        self._completed_images = ({self._image_identity(card) for card in self._completed.cards.values()}
                                  if self._completed is not None else set())
        self._previous = self._load_previous()
        self._scan_current()

    def _object_path(self, card: dict) -> Path:
        return self.root / "objects" / f"{card['sha256']}.{card['format']}"

    @staticmethod
    def _image_identity(card: dict) -> tuple:
        return tuple(card[key] for key in ("sha256", "bytes", "width", "height", "format"))

    def _read_card(self, card: dict) -> bytes | None:
        path = self._object_path(card)
        try:
            info = path.stat()
            if info.st_size != card["bytes"]:
                return None
            data = path.read_bytes()
            signature = (info.st_mtime_ns, info.st_size)
            identity = self._image_identity(card)
            # Hash the bytes on every read, including equal-size replacements.
            if sha256(data).hexdigest() != card["sha256"]:
                return None
            if self._verified.get(identity) != signature:
                # Exact matching bytes and metadata from a completed catalog
                # were fully decoded before its atomic completion marker was
                # written. Rehash them on every reopen, but do not repeatedly
                # decode the entire collection before the menu can appear.
                if identity not in self._completed_images:
                    _validate_image(data, card)
                self._verified[identity] = signature
            return data
        except (OSError, ValueError, SyntaxError):
            return None

    def _load_completed_catalog(self) -> ArtworkManifest | None:
        try:
            marker = json.loads((self.root / "ready.json").read_text(encoding="utf-8"))
            catalog_id = marker["catalog_id"]
            if not _safe_id(catalog_id):
                return None
            manifest = ArtworkManifest.load(self.root / "catalogs" / f"{catalog_id}.json")
            if not manifest.release_ready or marker.get("manifest_sha256") != manifest.sha256:
                return None
            return manifest
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return None

    def _load_previous(self) -> ArtworkManifest | None:
        manifest = self._completed
        if manifest is not None and manifest.catalog_id != self.manifest.catalog_id:
            # A marker is evidence of an earlier completed transaction, not a
            # substitute for checking every object's current hash and size.
            if all(self._read_card(card) is not None for card in manifest.cards.values()):
                return manifest
        return None

    def _scan_current(self) -> None:
        self._available = {key for key, card in self.manifest.cards.items() if self._read_card(card) is not None}
        self._ready = self.manifest.release_ready and len(self._available) == len(self.manifest.cards)

    def canonical_id(self, card_id: str) -> str | None:
        return self.manifest.canonical_id(card_id.lstrip("/"))

    def has_image_id(self, card_id: str) -> bool:
        return self.canonical_id(card_id) in self.manifest.cards

    def get_image(self, card_id: str) -> bytes | None:
        card_id = card_id.lstrip("/")
        canonical = self.manifest.canonical_id(card_id)
        if canonical in self.manifest.cards and self.manifest.release_ready:
            data = self._read_card(self.manifest.cards[canonical])
            if data is not None:
                return data
            with self._condition:
                self._available.discard(canonical)
                self._ready = False
                pack_id = self.manifest.cards[canonical]["pack_id"]
                if (self._running and self.manifest.release_ready and pack_id not in self._active
                        and pack_id not in self._queue and pack_id not in self._errors):
                    self._queue.append(pack_id)
                    self._condition.notify_all()
        if self._previous is not None:
            previous = self._previous.canonical_id(card_id)
            if previous in self._previous.cards:
                return self._read_card(self._previous.cards[previous])
        return None

    def ready_for(self, card_ids: Iterable[str]) -> bool:
        """Required content can use an older verified catalog during an update."""
        for card_id in card_ids:
            for manifest in (self.manifest, self._previous):
                if manifest is not None and manifest.release_ready:
                    canonical = manifest.canonical_id(card_id.lstrip("/"))
                    if canonical in manifest.generated or canonical in manifest.bundled:
                        break
            else:
                if self.get_image(card_id) is None:
                    return False
        return True

    def image_state(self, card_id: str) -> str:
        canonical = self.canonical_id(card_id)
        if canonical not in self.manifest.cards or not self.manifest.release_ready:
            return "unavailable"
        # An older verified picture can remain visible during an update, but it
        # must retain retry headers until the requested catalog's picture is
        # ready; otherwise the browser memoizes that older picture forever.
        if self._read_card(self.manifest.cards[canonical]) is not None:
            return "ready"
        with self._condition:
            if self._paused:
                return "paused"
            if self.manifest.cards[canonical]["pack_id"] in self._errors:
                return "error"
            return "pending" if self._running else "unavailable"

    def is_preparing(self, card_id: str) -> bool:
        return self.image_state(card_id) == "pending"

    def _partial_bytes(self, pack_id: str) -> int:
        pack = self.manifest.packs[pack_id]
        try:
            size = (self.root / "downloads" / f"{pack['sha256']}.part").stat().st_size
            return size if size <= pack["bytes"] else 0
        except OSError:
            return 0

    def status(self) -> dict:
        with self._condition:
            state = ("incomplete" if not self.manifest.release_ready else
                     "ready" if self._ready else "paused" if self._paused else
                     "downloading" if self._running and (self._queue or self._active) else
                     "error" if self._errors else "idle")
            completed_packs = [key for key, pack in self.manifest.packs.items()
                               if all(card_id in self._available for card_id in pack["files"])]
            partial_bytes = {key: self._partial_bytes(key) for key in self.manifest.packs
                             if key not in completed_packs}
            download_progress = {key: min(pack["bytes"], self._downloaded.get(key, partial_bytes[key]))
                                 if key in self._active else partial_bytes[key]
                                 for key, pack in self.manifest.packs.items() if key not in completed_packs}
            downloaded = sum(self.manifest.packs[key]["bytes"] for key in completed_packs)
            downloaded += sum(download_progress.values())
            unique_objects = {self.manifest.cards[key]["sha256"]: self.manifest.cards[key]["bytes"]
                              for key in self._available}
            installed_bytes = sum(unique_objects.values())
            all_objects = {card["sha256"]: card["bytes"] for card in self.manifest.cards.values()}
            total_installed_bytes = sum(all_objects.values())
            required_bytes = sum(pack["bytes"] - download_progress[key] for key, pack in self.manifest.packs.items()
                                 if key not in completed_packs)
            pack_progress = {
                key: {"downloaded_bytes": pack["bytes"] if key in completed_packs else download_progress[key],
                      "total_bytes": pack["bytes"],
                      "verified_bytes": sum({self.manifest.cards[card_id]["sha256"]: self.manifest.cards[card_id]["bytes"]
                                             for card_id in pack["files"] if card_id in self._available}.values()),
                      "ready": key in completed_packs}
                for key, pack in self.manifest.packs.items()
            }
            return {
                "state": state, "catalog_id": self.manifest.catalog_id,
                "release_ready": self.manifest.release_ready,
                "ready": self._ready, "has_previous": self._previous is not None,
                "can_play": self._ready or self._previous is not None,
                "completed_cards": len(self._available), "total_cards": len(self.manifest.cards),
                "completed_packs": len(completed_packs), "total_packs": len(self.manifest.packs),
                "downloaded_bytes": downloaded,
                "installed_bytes": installed_bytes, "required_bytes": required_bytes,
                "total_installed_bytes": total_installed_bytes,
                "required_storage_bytes": (total_installed_bytes - installed_bytes
                                           + sum(sorted((pack["bytes"] - partial_bytes[key]
                                                         for key, pack in self.manifest.packs.items()
                                                         if key not in completed_packs), reverse=True)[:2])),
                "total_bytes": sum(pack["bytes"] for pack in self.manifest.packs.values()),
                "packs": pack_progress,
                "errors": dict(self._errors),
                "error": ("The artwork catalog is incomplete and has not been approved for release."
                          if not self.manifest.release_ready else next(iter(self._errors.values()), "")),
                "folder": str(self.root),
            }

    def start(self) -> None:
        with self._condition:
            if self._stopping or not self.manifest.release_ready:
                return
            self._running = True
            self._paused = False
            self._errors.clear()
            self._ready = len(self._available) == len(self.manifest.cards)
            if self._ready:
                try:
                    self._mark_ready()
                except OSError as error:
                    self._ready = False
                    self._errors["storage"] = str(error)
            queued = set(self._queue) | self._active
            for pack_id, pack in self.manifest.packs.items():
                if pack_id not in queued and not all(key in self._available for key in pack["files"]):
                    self._queue.append(pack_id)
            if not self._threads:
                for number in range(2):
                    thread = threading.Thread(target=self._worker, name=f"Artwork-{number + 1}", daemon=True)
                    self._threads.append(thread)
                    thread.start()
            self._condition.notify_all()

    def pause(self) -> None:
        with self._condition:
            self._running = False
            self._paused = not self._ready
            self._condition.notify_all()

    def resume(self) -> None:
        self.start()

    def retry(self) -> None:
        self.start()

    def shutdown(self) -> None:
        with self._condition:
            self._stopping = True
            self._running = False
            self._condition.notify_all()
        for thread in self._threads:
            thread.join(timeout=0.2)

    def _check_running(self) -> None:
        with self._condition:
            if self._stopping or not self._running:
                raise _Interrupted()

    def _migrate_verified(self, card_ids: Iterable[str]) -> None:
        # Only inspect names from the manifest in explicitly supplied old cache
        # roots; never search Downloads or unrelated installations.
        for card_id in card_ids:
            card = self.manifest.cards[card_id]
            self._check_running()
            if self._read_card(card) is not None:
                continue
            for folder in self.legacy_folders:
                found = False
                for stem in (card_id, f"normalized-identity-sides/{card_id}"):
                    for suffix in ("jpg", "png", "webp"):
                        source = folder / f"{stem}.{suffix}"
                        try:
                            if source.stat().st_size != card["bytes"]:
                                continue
                            data = source.read_bytes()
                            _validate_image(data, card)
                            _atomic_write(self._object_path(card), data)
                            with self._condition:
                                self._available.add(card_id)
                            found = True
                            break
                        except (OSError, ValueError, SyntaxError):
                            continue
                    if found:
                        break
                if found:
                    break

    def _worker(self) -> None:
        with self._session_factory() as session:
            session.headers.update({"User-Agent": "Marvel-Champions-Digital-Artwork/1", "Accept-Encoding": "identity"})
            while True:
                with self._condition:
                    self._condition.wait_for(lambda: self._stopping or (self._running and self._queue))
                    if self._stopping:
                        return
                    pack_id = self._queue.popleft()
                    self._active.add(pack_id)
                try:
                    # The OS lock also covers migration and extraction so two
                    # installations cannot race a shared resumable pack.
                    pack = self.manifest.packs[pack_id]
                    lock_path = self.root / "locks" / f"{pack['sha256']}.lock"
                    with _pack_lock(lock_path, self._check_running):
                        self._install_pack(session, pack_id)
                except _Interrupted:
                    with self._condition:
                        if not self._stopping and pack_id not in self._queue:
                            self._queue.appendleft(pack_id)
                except (OSError, ValueError, EOFError, RuntimeError, zlib.error,
                        requests.RequestException, zipfile.BadZipFile) as error:
                    with self._condition:
                        self._errors[pack_id] = str(error) or type(error).__name__
                finally:
                    with self._condition:
                        self._active.discard(pack_id)
                        self._ready = self.manifest.release_ready and len(self._available) == len(self.manifest.cards)
                        if self._ready:
                            try:
                                self._mark_ready()
                            except OSError as error:
                                self._ready = False
                                self._errors["storage"] = str(error)
                        self._condition.notify_all()

    def _install_pack(self, session, pack_id: str) -> None:
        pack = self.manifest.packs[pack_id]
        # Another process may have installed it while this worker waited.
        complete = True
        for card_id in pack["files"]:
            if self._read_card(self.manifest.cards[card_id]) is not None:
                with self._condition:
                    self._available.add(card_id)
            else:
                complete = False
        if complete:
            return
        if self.legacy_folders:
            self._migrate_verified(pack["files"])
            if all(key in self._available for key in pack["files"]):
                return
        part = self.root / "downloads" / f"{pack['sha256']}.part"
        part.parent.mkdir(parents=True, exist_ok=True)
        missing = {self.manifest.cards[key]["sha256"]: self.manifest.cards[key]["bytes"]
                   for key in pack["files"] if key not in self._available}
        # Verify before committing more downloaded bytes. The other worker may
        # consume space too; atomic writes remain the final protection.
        partial_bytes = part.stat().st_size if part.exists() else 0
        required = sum(missing.values()) + max(0, pack["bytes"] - partial_bytes)
        if shutil.disk_usage(part.parent).free < required:
            raise OSError("Not enough free space to prepare card artwork")
        self._download(session, pack_id, part)
        self._extract(pack_id, part)
        part.unlink(missing_ok=True)

    def _download(self, session, pack_id: str, part: Path) -> None:
        pack = self.manifest.packs[pack_id]
        self._check_running()
        offset = part.stat().st_size if part.exists() else 0
        if offset > pack["bytes"]:
            part.unlink()
            offset = 0
        if offset == pack["bytes"]:
            if sha256(part.read_bytes()).hexdigest() == pack["sha256"]:
                return
            part.unlink()
            offset = 0
        with self._condition:
            self._downloaded[pack_id] = offset
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        with session.get(pack["url"], headers=headers, stream=True, timeout=DOWNLOAD_TIMEOUT) as response:
            response.raise_for_status()
            if urlsplit(getattr(response, "url", pack["url"])).scheme != "https":
                raise ArtworkError("Artwork download was redirected away from HTTPS")
            if response.status_code == 206:
                expected = f"bytes {offset}-{pack['bytes'] - 1}/{pack['bytes']}"
                if response.headers.get("Content-Range") != expected:
                    raise ArtworkError("Artwork server returned an invalid resume range")
            elif response.status_code == 200:
                offset = 0
            else:
                raise ArtworkError("Unexpected artwork download response")
            expected_remaining = pack["bytes"] - offset
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) != expected_remaining:
                raise ArtworkError("Artwork download size differs from its manifest")
            with part.open("ab" if offset else "wb") as output:
                with self._condition:
                    self._downloaded[pack_id] = offset
                for chunk in response.iter_content(64 * 1024):
                    self._check_running()
                    if not chunk:
                        continue
                    if offset + len(chunk) > pack["bytes"]:
                        raise ArtworkError("Artwork download exceeds its manifest size")
                    output.write(chunk)
                    offset += len(chunk)
                    with self._condition:
                        self._downloaded[pack_id] = offset
                output.flush()
                os.fsync(output.fileno())
        if offset != pack["bytes"]:
            raise ArtworkError("Artwork download was incomplete")
        if sha256(part.read_bytes()).hexdigest() != pack["sha256"]:
            part.unlink(missing_ok=True)
            raise ArtworkError("Artwork pack hash mismatch")

    def _extract(self, pack_id: str, path: Path) -> None:
        pack = self.manifest.packs[pack_id]
        entries = self.manifest.members(pack_id)
        current_members = {ArtworkManifest.member_name(self.manifest.cards[key]) for key in pack["files"]}
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) != len(entries) or {info.filename for info in members} != set(entries):
                raise ArtworkError("Artwork pack contains unexpected or duplicate files")
            if sum(info.file_size for info in members) > MAX_UNPACKED_BYTES:
                raise ArtworkError("Artwork pack expands beyond its size limit")
            for info in members:
                card = entries[info.filename]
                mode = info.external_attr >> 16
                if (info.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                        or info.flag_bits & 1 or info.file_size != card["bytes"]):
                    raise ArtworkError("Invalid artwork archive member")
                self._check_running()
                data = archive.read(info)
                _validate_image(data, card)
                if info.filename in current_members and self._read_card(card) is None:
                    _atomic_write(self._object_path(card), data)
        with self._condition:
            self._available.update(pack["files"])

    def _mark_ready(self) -> None:
        catalog_path = self.root / "catalogs" / f"{self.manifest.catalog_id}.json"
        marker = json.dumps({"catalog_id": self.manifest.catalog_id,
                             "manifest_sha256": self.manifest.sha256}, sort_keys=True).encode("utf-8")
        marker_path = self.root / "ready.json"
        # A completed, revalidated installation needs no writes to play offline.
        # Avoid invalidating it merely because the disk became full/read-only.
        for path, expected in ((catalog_path, self.manifest.encoded), (marker_path, marker)):
            try:
                if path.stat().st_size == len(expected) and path.read_bytes() == expected:
                    continue
            except OSError:
                pass
            _atomic_write(path, expected)


class UnavailableArtworkLibrary:
    """Keep menus and diagnostics usable when the packaged index is missing."""

    manifest = None

    def __init__(self, error: str, root: str | Path | None = None):
        self.error = error
        self.root = Path(root) if root is not None else artwork_folder()

    def status(self) -> dict:
        return {"state": "incomplete", "catalog_id": "", "release_ready": False,
                "ready": False, "has_previous": False, "can_play": False,
                "completed_cards": 0, "total_cards": 0, "completed_packs": 0, "total_packs": 0,
                "downloaded_bytes": 0, "total_bytes": 0, "installed_bytes": 0,
                "total_installed_bytes": 0, "required_bytes": 0, "required_storage_bytes": 0,
                "packs": {}, "errors": {"manifest": self.error}, "error": self.error,
                "folder": str(self.root)}

    def get_image(self, _card_id: str) -> None:
        return None

    def canonical_id(self, _card_id: str) -> None:
        return None

    def has_image_id(self, _card_id: str) -> bool:
        return False

    def ready_for(self, _card_ids: Iterable[str]) -> bool:
        return False

    def image_state(self, _card_id: str) -> str:
        return "unavailable"

    def is_preparing(self, _card_id: str) -> bool:
        return False

    def start(self) -> None:
        pass

    pause = resume = retry = shutdown = start


def load_artwork_library(manifest_path: str | Path | None = None, root: str | Path | None = None,
                         **kwargs) -> ArtworkLibrary | UnavailableArtworkLibrary:
    """Malformed/missing metadata must not crash game initialization."""
    try:
        return ArtworkLibrary(manifest_path or "./data/artwork-manifest.json", root, **kwargs)
    except (OSError, ValueError, TypeError, KeyError) as error:
        return UnavailableArtworkLibrary(f"Unable to load the artwork catalog: {error}", root)
