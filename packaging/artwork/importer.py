"""Maintainer-only, reproducible Workshop artwork preparation.

Workshop saves are data: Lua, XML, and object scripts are never executed. Runtime
clients consume the resulting immutable catalog/packs, never this importer.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from difflib import SequenceMatcher
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
import threading
import time
from urllib.parse import urlsplit
import warnings
import zipfile

from PIL import Image
import requests

SCHEMA_VERSION = 1
MAX_PACK_BYTES = 64 * 1024 * 1024
MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4096
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024
MAX_SHEET_BYTES = 256 * 1024 * 1024
MAX_PIXELS = 100_000_000
SOURCE_HOSTS = frozenset({
    "steamusercontent-a.akamaihd.net", "steamuserimages-a.akamaihd.net",
    "cdn.steamusercontent.com", "images.steamusercontent.com",
})
ALTERNATE_HOSTS = frozenset({"images-cdn.fantasyflightgames.com", "images.fantasyflightgames.com", "marvelcdb.com", "cdn.svc.asmodee.net", "skilledinvestigator.com"})
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
NUMBERED_ID = re.compile(r"^\d{5}[a-z]?$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", encoding="utf-8", delete=False) as file:
            temporary = Path(file.name)
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def safe_id(value: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"Unsafe identifier: {value!r}")
    return value


def source_url(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in SOURCE_HOSTS
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or not parsed.path.startswith("/ugc/") or parsed.query or parsed.fragment):
        raise ValueError(f"Unapproved Workshop source URL: {url}")
    return url


def alternate_url(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in ALTERNATE_HOSTS or parsed.username
            or parsed.password or parsed.port not in (None, 443) or parsed.query or parsed.fragment):
        raise ValueError("Alternate artwork must use an explicitly supported HTTPS source host")
    if parsed.hostname == "cdn.svc.asmodee.net" and not parsed.path.startswith("/production-fantasyflightgames/uploads/"):
        raise ValueError("Asmodee alternate sources must be published Fantasy Flight Games uploads")
    if parsed.hostname == "skilledinvestigator.com" and not parsed.path.startswith("/wp-content/uploads/2026/07/"):
        raise ValueError("Skilled Investigator alternatives are limited to the reviewed July 2026 FFG reveal uploads")
    return url


def download(url: str, destination: Path, expected_hash: str | None, expected_bytes: int | None,
             limit: int, session=None) -> None:
    """No unpinned downloads, unchecked redirects, or partially installed files."""
    if expected_hash is not None and not SHA256.fullmatch(expected_hash):
        raise ValueError("A pinned SHA-256 is required before downloading")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_url(url)
    temporary = None
    try:
        with (requests.Session() if session is None else nullcontext(session)) as session:
            response = session.get(url, stream=True, timeout=(10, 60), allow_redirects=False)
            with response:
                response.raise_for_status()
                if response.status_code != 200:
                    raise ValueError("Workshop source must return HTTP 200 without redirect")
                size = int(response.headers.get("Content-Length", 0))
                if size > limit:
                    raise ValueError("Source exceeds the download size limit")
                hasher = hashlib.sha256()
                total = 0
                with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as file:
                    temporary = Path(file.name)
                    for chunk in response.iter_content(1024 * 1024):
                        total += len(chunk)
                        if total > limit:
                            raise ValueError("Source exceeds the download size limit")
                        hasher.update(chunk)
                        file.write(chunk)
                if (expected_hash is not None and hasher.hexdigest() != expected_hash) or (
                        expected_bytes is not None and total != expected_bytes):
                    raise ValueError("Source hash or size differs from the reviewed pin")
                temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def decode_snapshot(raw: bytes) -> dict:
    """Decode bounded JSON/BSON data without importing or running Workshop code."""
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise ValueError("Workshop snapshot too large")
    if raw.lstrip().startswith(b"{"):
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError("Workshop snapshot must be an object")
        return result

    def document(start: int, limit: int, depth: int = 0, array: bool = False):
        if depth > 100 or start + 5 > limit:
            raise ValueError("Invalid BSON document")
        length = struct.unpack_from("<i", raw, start)[0]
        end = start + length
        if length < 5 or end > limit or raw[end - 1] != 0:
            raise ValueError("Invalid BSON length or terminator")
        cursor = start + 4
        output = {}
        while cursor < end - 1:
            kind = raw[cursor]
            cursor += 1
            key_end = raw.find(b"\0", cursor, end)
            if key_end == -1:
                raise ValueError("Unterminated BSON key")
            key = raw[cursor:key_end].decode("utf-8")
            if key in output:
                raise ValueError("Duplicate BSON key")
            cursor = key_end + 1

            def take(size):
                nonlocal cursor
                if size < 0 or cursor + size > end - 1:
                    raise ValueError("Truncated BSON value")
                data = raw[cursor:cursor + size]
                cursor += size
                return data

            if kind == 1:
                value = struct.unpack("<d", take(8))[0]
            elif kind == 2:
                size = struct.unpack("<i", take(4))[0]
                encoded = take(size)
                if size < 1 or encoded[-1] != 0:
                    raise ValueError("Invalid BSON string")
                value = encoded[:-1].decode("utf-8")
            elif kind in (3, 4):
                value, cursor = document(cursor, end - 1, depth + 1, kind == 4)
            elif kind == 8:
                encoded = take(1)[0]
                if encoded not in (0, 1):
                    raise ValueError("Invalid BSON boolean")
                value = bool(encoded)
            elif kind == 10:
                value = None
            elif kind in (9, 16, 18):
                value = struct.unpack("<i" if kind == 16 else "<q", take(4 if kind == 16 else 8))[0]
            else:
                raise ValueError(f"Unsupported BSON type {kind}; source requires review")
            output[key] = value
        if cursor != end - 1:
            raise ValueError("Invalid BSON boundary")
        if array:
            if list(output) != [str(i) for i in range(len(output))]:
                raise ValueError("Invalid BSON array indexes")
            return list(output.values()), end
        return output, end

    result, end = document(0, len(raw))
    if end != len(raw):
        raise ValueError("Trailing BSON bytes")
    return result


def load_snapshot(path: Path, pin: dict) -> dict:
    raw = path.read_bytes()
    expected = pin["snapshot"]
    if len(raw) != expected["bytes"] or digest(raw) != expected["sha256"]:
        raise ValueError("Workshop snapshot does not match the pinned source")
    return decode_snapshot(raw)


def card_database(path: Path):
    records, groups, aliases = {}, {}, {}
    for group, values in read_json(path).items():
        if not isinstance(values, list):
            continue
        for card in values:
            identifier = safe_id(card["card_id"])
            if identifier in records:
                raise ValueError(f"Duplicate card ID {identifier}")
            records[identifier] = card
            groups[identifier] = group or "builtins"
            if target := card.get("full_link", card.get("pic_id")):
                aliases[identifier] = safe_id(target)
    for identifier in aliases:
        canonical(identifier, aliases)
    return records, groups, aliases


def canonical(identifier: str, aliases: dict) -> str:
    seen = set()
    while identifier in aliases:
        if identifier in seen:
            raise ValueError(f"Artwork alias cycle at {identifier}")
        seen.add(identifier)
        identifier = aliases[identifier]
    return identifier


def workshop_cards(snapshot: dict) -> list[dict]:
    output = []

    def walk(value, path, parents):
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + [index], parents)
        elif isinstance(value, dict):
            name = value.get("Nickname", "")
            if isinstance(value.get("CardID"), int) and value.get("CustomDeck"):
                decks = value["CustomDeck"]
                # Some TTS saves retain an old CardID prefix after rekeying a
                # single deck. Never take an unrelated global deck definition.
                key = str(value["CardID"] // 100)
                if key not in decks:
                    key = next(iter(decks)) if len(decks) == 1 else None
                if key is not None:
                    output.append({"name": name, "guid": value.get("GUID"),
                                   "object_path": path, "parents": parents,
                                   "card_id": value["CardID"], "deck_key": key,
                                   "deck": decks[key], "sideways": value.get("SidewaysCard", False)})
            for key in ("ObjectStates", "ContainedObjects", "States"):
                if key in value:
                    child = value[key]
                    if key == "States" and isinstance(child, dict):
                        for state, obj in child.items():
                            walk(obj, path + [key, state], parents + ([name] if name else []))
                    else:
                        walk(child, path + [key], parents + ([name] if name else []))

    walk(snapshot, [], [])
    return output


def normalized_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def candidate_rank(source: dict, card: dict) -> int:
    """Order review candidates; this score never certifies a mapping."""
    parents = normalized_name(" ".join(source["parents"]))
    kind = card.get("type", "")
    card_set = normalized_name(card.get("set_name", ""))
    score = 20 if card_set and card_set in parents else 0
    marker = {"Hero": "heropack", "AlterEgo": "heropack", "Villain": "villain",
              "MainScheme": "mainscheme", "Ally": "allies", "Event": "events",
              "Resource": "resources", "Upgrade": "upgrades", "Support": "supports"}.get(kind)
    if marker and marker in parents:
        score += 15
    if kind in ("Hero", "AlterEgo") and any(token in parents for token in ("aspect", "modular", "nemesis", "herodeck")):
        score -= 50
    if kind == "Villain" and any(token in parents for token in ("aspect", "nemesis")):
        score -= 50
    if kind not in ("Villain", "MainScheme", "Hero", "AlterEgo") and "herodeck" in parents and card_set:
        score += 10
    aspect = normalized_name(card.get("desc", {}).get("Class", ""))
    if aspect and aspect + "aspect" in parents:
        score += 10
    return score


def candidate(source: dict, face: str = "front") -> dict:
    sheet = source["deck"]
    url = source_url(sheet["FaceURL" if face == "front" else "BackURL"])
    # Shared reverse images may be full-card art, not another tile grid.
    tiled = face == "front" or sheet.get("UniqueBack", False)
    return {
        "reviewed": False, "review_note": "",
        "source": {"guid": source["guid"], "object_path": source["object_path"],
                   "deck_key": source["deck_key"], "card_id": source["card_id"],
                   "name": source["name"], "parents": source["parents"], "face": face,
                   "sheet_url": url, "sheet_sha256": None,
                   "columns": sheet["NumWidth"] if tiled else 1,
                   "rows": sheet["NumHeight"] if tiled else 1,
                   "index": source["card_id"] % 100 if tiled else 0},
        "rotation": 0,
    }


def inspect(snapshot: dict, cards_path: Path, pin: dict, output: Path):
    records, _, aliases = card_database(cards_path)
    sources = workshop_cards(snapshot)
    by_name = defaultdict(list)
    for source in sources:
        by_name[normalized_name(source["name"])].append(source)
    choices, mappings = {}, {}
    for identifier, card in records.items():
        if identifier in aliases:
            continue
        name = card.get("name", "")
        face = "front"
        if card.get("type") == "AlterEgo" and identifier.endswith("b"):
            hero = records.get(identifier[:-1] + "a", {})
            if hero.get("type") == "Hero":
                name, face = hero["name"], "back"
        lookup = normalized_name(name)
        matches = by_name.get(lookup, [])
        basis = "exact name; requires visual confirmation"
        if not matches and card.get("type") in ("MainScheme", "Villain", "SideScheme"):
            lookup = normalized_name(re.sub(r"\s+\d*[AB]$", "", name))
            matches = by_name.get(lookup, [])
            basis = "name without game-specific stage/face suffix; requires visual confirmation"
        if not matches and identifier.endswith("b") and identifier[:-1] + "a" in records:
            front = records[identifier[:-1] + "a"]
            lookup = normalized_name(re.sub(r"\s+\d*[AB]$", "", front.get("name", "")))
            matches = by_name.get(lookup, [])
            face = "back"
            basis = "opposite side of paired game card; requires visual confirmation"
        if not matches and NUMBERED_ID.fullmatch(identifier):
            # Typographical differences are candidate suggestions only. Retain
            # the match reason; no fuzzy result may become reviewed by tooling.
            near = [(SequenceMatcher(None, lookup, key).ratio(), key) for key in by_name]
            near.sort(reverse=True)
            if near and near[0][0] >= .82:
                matches = by_name[near[0][1]]
                basis = f"approximate title ({near[0][0]:.3f}); requires manual identification"
        matches = sorted(matches, key=lambda item: (-candidate_rank(item, card), str(item["object_path"])))
        proposals = [candidate(source, face) for source in matches]
        # Identical physical sheets/crops can have multiple object copies.
        unique = {}
        for proposal in proposals:
            s = proposal["source"]
            key = (s["sheet_url"], s["columns"], s["rows"], s["index"])
            unique.setdefault(key, proposal)
        choices[identifier] = {"name": card.get("name"), "type": card.get("type"),
                               "set_name": card.get("set_name"), "basis": basis, "candidates": list(unique.values())}
        if unique:
            proposal = next(iter(unique.values()))
            proposal["proposal_basis"] = basis
            proposal["candidate_count"] = len(unique)
            mappings[identifier] = proposal
    draft = {"schema_version": SCHEMA_VERSION, "source_pin": pin, "mappings": mappings,
             "nonnumbered": {identifier: {"disposition": "pending", "reviewed": False, "reason": ""}
                             for identifier in sorted(set(records) | set(aliases.values()))
                             if not NUMBERED_ID.fullmatch(identifier)}}
    write_json(output / "mapping-draft.json", draft)
    write_json(output / "candidates.json", choices)
    write_json(output / "coverage.json", coverage(draft, cards_path))
    return draft


def coverage(mapping: dict, cards_path: Path) -> dict:
    records, _, aliases = card_database(cards_path)
    required = sorted({canonical(identifier, aliases) for identifier in records
                       if NUMBERED_ID.fullmatch(identifier)})
    entries = mapping.get("mappings", {})
    reviewed = {identifier for identifier, entry in entries.items()
                if entry.get("reviewed") is True and entry.get("review_note", "").strip()
                and SHA256.fullmatch(entry.get("source", {}).get("sheet_sha256") or "")}
    missing = sorted(set(required) - reviewed)
    nonnumbered = mapping.get("nonnumbered", {})
    pending = sorted(identifier for identifier in set(records) | set(aliases.values()) if not NUMBERED_ID.fullmatch(identifier)
                     and not (nonnumbered.get(identifier, {}).get("reviewed") is True
                              and nonnumbered[identifier].get("reason", "").strip()
                              and nonnumbered[identifier].get("disposition") in ("builtin", "generated", "alias", "mapped")
                              and (nonnumbered[identifier]["disposition"] != "mapped" or identifier in reviewed)
                              and (nonnumbered[identifier]["disposition"] != "alias" or identifier in aliases)))
    return {"schema_version": SCHEMA_VERSION, "numbered_ids": sum(bool(NUMBERED_ID.fullmatch(k)) for k in records),
            "required_images": len(required), "reviewed_images": len(set(required) & reviewed),
            "unreviewed_images": missing, "unaccounted_nonnumbered": pending,
            "release_ready": not missing and not pending}


def validate_source(entry: dict, snapshot: dict, require_review=True, require_hash=True, alternate_sources=None):
    source = entry["source"]
    if source.get("kind", "workshop") != "workshop":
        pin = (alternate_sources or {}).get(source.get("source_id"))
        if source.get("kind") not in ("image", "pdf_image", "pdf_page") or not pin:
            raise ValueError("Unpinned alternate artwork source")
        alternate_url(pin["url"])
        if not SHA256.fullmatch(pin.get("sha256", "")) or type(pin.get("bytes")) is not int or not 0 < pin["bytes"] <= MAX_SHEET_BYTES:
            raise ValueError("Invalid alternate source hash or size")
        if source["sheet_url"] != pin["url"] or source["file_sha256"] != pin["sha256"]:
            raise ValueError("Alternate source differs from its explicit pin")
        if (source["columns"], source["rows"], source["index"]) != (1, 1, 0):
            raise ValueError("Alternate sources require an explicit single-image crop")
        if source["kind"] == "pdf_image" and (type(source.get("pdf_page")) is not int or type(source.get("pdf_xref")) is not int
                                                  or source["pdf_page"] < 0 or source["pdf_xref"] < 1):
            raise ValueError("PDF artwork requires explicit page and embedded-image xref")
        if source["kind"] == "pdf_page" and (type(source.get("pdf_page")) is not int or source["pdf_page"] < 0
                                                 or type(source.get("render_dpi")) is not int or not 150 <= source["render_dpi"] <= 600):
            raise ValueError("PDF page artwork requires an explicit page and bounded rendering resolution")
        if require_hash and not SHA256.fullmatch(source.get("sheet_sha256") or ""):
            raise ValueError("Alternate image requires an exact extracted-image hash")
        if entry.get("rotation") not in (0, 90, 180, 270):
            raise ValueError("Invalid explicit image rotation")
        if require_review and (entry.get("reviewed") is not True or not entry.get("review_note", "").strip()):
            raise ValueError("An alternate source requires visual review and a review note")
        return
    obj = snapshot
    for part in source["object_path"]:
        obj = obj[part]
    if obj.get("GUID") != source["guid"] or obj.get("CardID") != source["card_id"]:
        raise ValueError("Reviewed mapping no longer matches the pinned Workshop object")
    deck = obj["CustomDeck"][source["deck_key"]]
    if source["face"] not in ("front", "back"):
        raise ValueError("Mapping must explicitly choose front or back")
    expected = candidate({"guid": source["guid"], "object_path": source["object_path"],
                          "deck_key": source["deck_key"], "card_id": source["card_id"],
                          "name": obj.get("Nickname", ""), "parents": [], "deck": deck}, source["face"])["source"]
    for key in ("sheet_url", "columns", "rows", "index"):
        if source[key] != expected[key]:
            raise ValueError(f"Reviewed mapping differs from pinned source: {key}")
    if require_hash and not SHA256.fullmatch(source.get("sheet_sha256") or ""):
        raise ValueError("Reviewed image requires an exact source-sheet hash")
    if entry.get("rotation") not in (0, 90, 180, 270):
        raise ValueError("Rotation must be explicit, in quarter turns counterclockwise")
    if require_review and (entry.get("reviewed") is not True or not entry.get("review_note", "").strip()):
        raise ValueError("A visually reviewed mapping and review note are required")


def alternate_image_bytes(raw, kind, page=None, xref=None, render_dpi=300):
    if kind == "image":
        return raw
    if kind not in ("pdf_image", "pdf_page"):
        raise ValueError("Unsupported alternate source type")
    try:
        import fitz
    except ImportError as error:
        raise ValueError("PDF source preparation requires the maintainer-only PyMuPDF dependency") from error
    with fitz.open(stream=raw, filetype="pdf") as document:
        if type(page) is not int or not 0 <= page < len(document):
            raise ValueError("Invalid PDF page")
        if kind == "pdf_page":
            if type(render_dpi) is not int or not 150 <= render_dpi <= 600:
                raise ValueError("Invalid explicit PDF rendering resolution")
            target = document[page]
            if target.rect.width * target.rect.height * (render_dpi / 72) ** 2 > MAX_PIXELS:
                raise ValueError("Rendered PDF page is too large")
            return target.get_pixmap(matrix=fitz.Matrix(render_dpi / 72, render_dpi / 72), alpha=False).tobytes("png")
        if xref not in {image[0] for image in document[page].get_images(full=True)}:
            raise ValueError("Embedded-image xref is not present on the selected PDF page")
        return document.extract_image(xref)["image"]


def stage_alternate(mapping, identifier, source_id, url, path, expected_hash, cache,
                    kind="image", page=None, xref=None, crop=None, render_dpi=300):
    safe_id(identifier)
    safe_id(source_id)
    alternate_url(url)
    raw = path.read_bytes()
    if len(raw) > MAX_SHEET_BYTES or digest(raw) != expected_hash:
        raise ValueError("Alternate source does not match its explicit hash")
    image_raw = alternate_image_bytes(raw, kind, page, xref, render_dpi)
    with Image.open(BytesIO(image_raw)) as image:
        if image.width * image.height > MAX_PIXELS or image.format not in ("JPEG", "PNG", "WEBP"):
            raise ValueError("Unsupported alternate image")
        image.verify()
    pin = {"url": url, "sha256": expected_hash, "bytes": len(raw), "kind": kind}
    pins = mapping.setdefault("alternate_sources", {})
    if source_id in pins and pins[source_id] != pin:
        raise ValueError("Refusing to change an existing alternate source pin")
    pins[source_id] = pin
    original = cache / "originals" / expected_hash
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(raw)
    hashed = digest(image_raw)
    (cache / hashed).write_bytes(image_raw)
    source = {"kind": kind, "source_id": source_id, "sheet_url": url,
              "file_sha256": expected_hash, "sheet_sha256": hashed,
              "face": "front", "columns": 1, "rows": 1, "index": 0}
    if kind == "pdf_image":
        source.update(pdf_page=page, pdf_xref=xref)
    elif kind == "pdf_page":
        source.update(pdf_page=page, render_dpi=render_dpi)
    if crop is not None:
        source["pixel_crop"] = list(crop)
    mapping["mappings"][identifier] = {"reviewed": False, "review_note": "", "source": source, "rotation": 0}
    return mapping


@contextmanager
def sheet_cache_lock(cache):
    """Coordinate the two-worker limit and provenance ledger across processes."""
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / ".fetch.lock").open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        start = time.monotonic()
        while True:
            try:
                lock.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() - start >= 120:
                    raise TimeoutError("Another sheet acquisition is using this cache; rerun after it finishes")
                time.sleep(.1)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def fetch_sheets(mapping: dict, snapshot: dict, cache: Path, identifiers=None, seeds=None):
    with sheet_cache_lock(cache):
        return _fetch_sheets_unlocked(mapping, snapshot, cache, identifiers, seeds)


def _fetch_sheets_unlocked(mapping: dict, snapshot: dict, cache: Path, identifiers=None, seeds=None):
    """Acquire only sheets referenced by the pinned snapshot; never approve art."""
    entries = {key: value for key, value in mapping["mappings"].items()
               if identifiers is None or key in identifiers}
    if identifiers is not None and set(identifiers) - set(entries):
        raise ValueError(f"No proposed mapping for {sorted(set(identifiers) - set(entries))}")
    by_url = defaultdict(list)
    for identifier, entry in entries.items():
        if entry["source"].get("kind", "workshop") != "workshop":
            continue  # Alternate sources are prepared with stage-alternate.
        validate_source(entry, snapshot, require_review=False, require_hash=False)
        by_url[entry["source"]["sheet_url"]].append(identifier)
    cache.mkdir(parents=True, exist_ok=True)
    ledger_path = cache / "sources.json"
    ledger = read_json(ledger_path) if ledger_path.exists() else {}
    seeds = seeds or {}
    if set(seeds) - set(by_url):
        raise ValueError("Seed URLs must be among the requested pinned sources")

    def acquire(url, session):
        existing_hashes = {entries[key]["source"].get("sheet_sha256") for key in by_url[url]} - {None}
        if len(existing_hashes) > 1:
            raise ValueError("Conflicting reviewed hashes for the same sheet")
        expected = next(iter(existing_hashes), None)
        previous = ledger.get(url, {})
        if expected is None:
            expected = previous.get("sha256")
        staged = cache / (digest(url.encode()) + ".download")
        if url in seeds:
            raw = Path(seeds[url]).read_bytes()
        elif expected and (cache / expected).exists():
            raw = (cache / expected).read_bytes()
        else:
            download(url, staged, expected, previous.get("bytes"), MAX_SHEET_BYTES, session)
            raw = staged.read_bytes()
        if len(raw) > MAX_SHEET_BYTES or (expected and digest(raw) != expected):
            raise ValueError("Sheet bytes differ from the existing pin")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.width * image.height > MAX_PIXELS or image.format not in ("JPEG", "PNG", "WEBP"):
                    raise ValueError("Invalid Workshop source image")
                width, height, image_format = image.width, image.height, image.format
                image.verify()
        hashed = digest(raw)
        destination = cache / hashed
        if not destination.exists():
            if staged.exists():
                staged.replace(destination)
            else:
                destination.write_bytes(raw)
        if staged.exists():
            staged.unlink()
        return url, {"sha256": hashed, "bytes": len(raw), "width": width, "height": height,
                     "format": image_format, "snapshot_sha256": mapping["source_pin"]["snapshot"]["sha256"]}

    urls = sorted(by_url)
    failures = []
    checkpoint_lock = threading.Lock()
    def worker(batch):
        results, errors = [], []
        with requests.Session() as session:
            for url in batch:
                try:
                    result = acquire(url, session)
                    results.append(result)
                    # Record every completed sheet so a killed batch can resume
                    # without reacquiring already downloaded large sources.
                    with checkpoint_lock:
                        ledger[result[0]] = result[1]
                        atomic_json(ledger_path, ledger)
                except Exception as error:
                    errors.append({"url": url, "error": str(error)})
        return results, errors
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(worker, urls[part::2]) for part in range(2)]
        for job in jobs:
            results, errors = job.result()
            failures.extend(errors)
            for url, record in results:
                ledger[url] = record
                for identifier in by_url[url]:
                    entries[identifier]["source"]["sheet_sha256"] = record["sha256"]
    write_json(ledger_path, ledger)
    return failures


def extract(entry: dict, sheet_path: Path) -> tuple[bytes, int, int, str]:
    source = entry["source"]
    if sheet_path.stat().st_size > MAX_SHEET_BYTES:
        raise ValueError("Source sheet is too large")
    data = sheet_path.read_bytes()
    if digest(data) != source["sheet_sha256"]:
        raise ValueError("Source sheet differs from the reviewed hash")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(BytesIO(data)) as image:
            if image.width * image.height > MAX_PIXELS or image.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError("Unsupported source image")
            return encode_crop(entry, image)


def encode_crop(entry, image):
    source = entry["source"]
    columns, rows, index = source["columns"], source["rows"], source["index"]
    if any(type(n) is not int for n in (columns, rows, index)) or not (
            1 <= columns <= 100 and 1 <= rows <= 100 and 0 <= index < columns * rows):
        raise ValueError("Invalid tile coordinates")
    col, row = index % columns, index // columns
    bounds = (col * image.width // columns, row * image.height // rows,
              (col + 1) * image.width // columns, (row + 1) * image.height // rows)
    if "pixel_crop" in source:
        bounds = source["pixel_crop"]
        if (not isinstance(bounds, (list, tuple)) or len(bounds) != 4 or any(type(n) is not int for n in bounds)
                or not (0 <= bounds[0] < bounds[2] <= image.width and 0 <= bounds[1] < bounds[3] <= image.height)):
            raise ValueError("Explicit image crop is outside source bounds")
    with image.crop(bounds) as original:
        crop = original.rotate(entry["rotation"], expand=True)
        try:
            if min(crop.size) < 100:
                raise ValueError("Card crop is unexpectedly small")
            if max(crop.size) > MAX_IMAGE_DIMENSION:
                raise ValueError("Card crop exceeds the runtime 4096-pixel limit; review its source/crop")
            # Native resolution; no upscaling, sharpening, or watermark editing.
            output = BytesIO()
            transparent = False
            if "A" in crop.getbands():
                with crop.getchannel("A") as alpha:
                    transparent = alpha.getextrema()[0] < 255
            elif "transparency" in crop.info:
                with crop.convert("RGBA") as rgba, rgba.getchannel("A") as alpha:
                    transparent = alpha.getextrema()[0] < 255
            if transparent:
                crop.save(output, format="PNG", optimize=True)
                extension = "png"
            else:
                crop.convert("RGB").save(output, format="JPEG", quality=95, subsampling=0, optimize=True)
                extension = "jpg"
            payload = output.getvalue()
            if len(payload) > MAX_IMAGE_BYTES:
                raise ValueError("Encoded card exceeds the runtime 16 MiB limit")
            return payload, crop.width, crop.height, extension
        finally:
            crop.close()


def iter_extracted(entries, sheets):
    """Decode each large source sheet once, with at most one sheet held open."""
    grouped = defaultdict(list)
    for identifier, entry in entries.items():
        hashed = entry["source"].get("sheet_sha256")
        if not isinstance(hashed, str) or not SHA256.fullmatch(hashed):
            raise ValueError(f"No sheet hash for {identifier}")
        grouped[hashed].append((identifier, entry))
    for hashed, items in sorted(grouped.items()):
        path = sheets / hashed
        if path.stat().st_size > MAX_SHEET_BYTES:
            raise ValueError("Source sheet is too large")
        raw = path.read_bytes()
        if digest(raw) != hashed:
            raise ValueError("Source sheet differs from the reviewed hash")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as sheet:
                if sheet.width * sheet.height > MAX_PIXELS or sheet.format not in ("JPEG", "PNG", "WEBP"):
                    raise ValueError("Unsupported source image")
                sheet.load()
                for identifier, entry in items:
                    yield identifier, encode_crop(entry, sheet)


def content_dependencies(cards_path: Path, records: dict, groups: dict, aliases: dict,
                         available: set) -> dict:
    dependencies = defaultdict(set)
    for identifier in records:
        target = canonical(identifier, aliases)
        if target in available:
            dependencies[f"pack:{groups[identifier]}"] .add(target)
    base = cards_path.parent
    definitions = {}
    for folder in ("encounter_sets", "nemesis", "scenarios"):
        for path in sorted((base / folder).glob("*.json")):
            definition = read_json(path)
            ids = set(re.findall(r"(?<![a-zA-Z0-9_])\d{5}[a-z]?(?![a-zA-Z0-9_])", json.dumps(definition)))
            resolved = {canonical(identifier, aliases) for identifier in ids} & available
            definitions[path.stem] = (definition, resolved)
    # Scenario references to modular/encounter sets must be included as well.
    for identifier, (definition, resolved) in definitions.items():
        expanded = set(resolved)
        for name in definition.get("encounter_sets", []) + definition.get("modular_sets", []):
            if name in definitions:
                expanded.update(definitions[name][1])
        dependencies[identifier].update(expanded)
        dependencies[definition.get("name", identifier)].update(expanded)
    campaign_prefixes = {"rise_of_red_skull": "04", "galaxys_most_wanted": "16",
                         "mad_titans_shadow": "21", "sinister_motives": "27",
                         "mutant_genesis": "32", "next_evolution": "40",
                         "age_of_apocalypse": "45", "agents_of_shield": "50", "fear_no_evil": "60"}
    for name, prefix in campaign_prefixes.items():
        dependencies[name].update(canonical(identifier, aliases) for identifier in records
                                  if identifier.startswith(prefix) and canonical(identifier, aliases) in available)
    return {key: sorted(value) for key, value in sorted(dependencies.items()) if value}


def zip_bytes(images: dict[str, bytes]) -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in sorted(images.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload)
    return output.getvalue()


def build(mapping: dict, cards_path: Path, snapshot: dict, sheets: Path, output: Path,
          catalog_id: str, base_url: str, draft: bool = False, previous: dict | None = None):
    safe_id(catalog_id)
    parsed = urlsplit(base_url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.port not in (None, 443) or parsed.query or parsed.fragment):
        raise ValueError("Pack base URL must be an HTTPS directory")
    report = coverage(mapping, cards_path)
    if not report["release_ready"] and not draft:
        raise ValueError(f"Release blocked: {len(report['unreviewed_images'])} images and "
                         f"{len(report['unaccounted_nonnumbered'])} special entries need review")
    records, groups, raw_aliases = card_database(cards_path)
    cards, payloads, grouped = {}, {}, defaultdict(list)
    accepted = {}
    for identifier, entry in sorted(mapping.get("mappings", {}).items()):
        safe_id(identifier)
        if entry.get("reviewed") is not True:
            continue
        validate_source(entry, snapshot, alternate_sources=mapping.get("alternate_sources"))
        source = entry["source"]
        if source.get("kind", "workshop") != "workshop":
            original = (sheets / "originals" / source["file_sha256"]).read_bytes()
            if digest(original) != source["file_sha256"]:
                raise ValueError("Alternate original source hash differs from its pin")
            raw = alternate_image_bytes(original, source["kind"], source.get("pdf_page"), source.get("pdf_xref"), source.get("render_dpi", 300))
            if digest(raw) != source["sheet_sha256"]:
                raise ValueError("Alternate extracted image differs from its reviewed hash")
        accepted[identifier] = entry
    for identifier, (payload, width, height, extension) in iter_extracted(accepted, sheets):
        hashed = digest(payload)
        cards[identifier] = {"sha256": hashed, "bytes": len(payload), "width": width,
                             "height": height, "format": extension, "pack_id": ""}
        payloads[f"cards/{hashed}.{extension}"] = payload
        grouped[groups.get(identifier, "special")].append(identifier)
    packs = {}
    reused = set()
    if previous:
        # Keep old immutable archives for unchanged objects. Their explicit
        # inventory also authenticates superseded members which still physically
        # exist in the old ZIP; those members are not active card mappings.
        for pack_id, pack in previous.get("packs", {}).items():
            ids = [identifier for identifier in pack["files"] if identifier in cards and
                   all(cards[identifier][key] == previous["cards"][identifier][key]
                       for key in ("sha256", "bytes", "width", "height", "format"))]
            if ids:
                members = pack.get("members") or {
                    f"cards/{previous['cards'][identifier]['sha256']}.{previous['cards'][identifier]['format']}":
                    {key: previous["cards"][identifier][key] for key in ("sha256", "bytes", "width", "height", "format")}
                    for identifier in pack["files"]}
                packs[pack_id] = {**pack, "files": sorted(ids), "members": members}
                for identifier in ids:
                    cards[identifier]["pack_id"] = pack_id
                    reused.add(identifier)
    output.mkdir(parents=True, exist_ok=True)
    for group, identifiers in sorted(grouped.items()):
        batch, batch_images, estimated = [], {}, 22

        def flush():
            if not batch:
                return
            payload = zip_bytes(batch_images)
            if len(payload) > MAX_PACK_BYTES:
                raise ValueError("Pack exceeds 64 MiB")
            hashed = digest(payload)
            slug = re.sub(r"[^A-Za-z0-9_.-]", "-", group).strip("-.") or "special"
            pack_id = safe_id(f"{slug[:40]}-{hashed[:20]}")
            path = output / f"{pack_id}.zip"
            if path.exists() and digest(path.read_bytes()) != hashed:
                raise ValueError("Refusing to replace an immutable pack")
            path.write_bytes(payload)
            packs[pack_id] = {"url": f"{base_url.rstrip('/')}/{pack_id}.zip", "sha256": hashed,
                              "bytes": len(payload), "files": list(batch),
                              "members": {f"cards/{cards[identifier]['sha256']}.{cards[identifier]['format']}":
                                          {key: cards[identifier][key] for key in ("sha256", "bytes", "width", "height", "format")}
                                          for identifier in batch}}
            for identifier in batch:
                cards[identifier]["pack_id"] = pack_id

        for identifier in identifiers:
            if identifier in reused:
                continue
            card = cards[identifier]
            name = f"cards/{card['sha256']}.{card['format']}"
            payload = payloads[name]
            addition = 0 if name in batch_images else len(payload) + 76 + 2 * len(name.encode())
            if estimated + addition > MAX_PACK_BYTES and batch:
                flush()
                batch, batch_images, estimated = [], {}, 22
                addition = len(payload) + 76 + 2 * len(name.encode())
            if estimated + addition > MAX_PACK_BYTES:
                raise ValueError("An individual image cannot fit in a pack")
            batch.append(identifier)
            batch_images[name] = payload
            estimated += addition
        flush()
    local = mapping.get("nonnumbered", {})
    generated = {identifier: entry["reason"] for identifier, entry in local.items()
                 if entry.get("reviewed") is True and entry.get("disposition") == "generated" and entry.get("reason", "").strip()}
    bundled = {identifier: entry["reason"] for identifier, entry in local.items()
               if entry.get("reviewed") is True and entry.get("disposition") == "builtin" and entry.get("reason", "").strip()}
    available = set(cards) | set(generated) | set(bundled)
    aliases = {identifier: canonical(identifier, raw_aliases) for identifier in raw_aliases
               if canonical(identifier, raw_aliases) in available}
    catalog = {"schema_version": SCHEMA_VERSION, "catalog_id": catalog_id,
               "release_ready": report["release_ready"] and not draft, "cards": cards, "aliases": aliases,
               "packs": packs, "dependencies": content_dependencies(cards_path, records, groups, raw_aliases, available),
               "generated": generated, "bundled": bundled,
               "provenance": {"source_pin": mapping.get("source_pin"),
                              "alternate_sources": mapping.get("alternate_sources", {}),
                              "mapping_sha256": digest(json.dumps(mapping, sort_keys=True).encode()),
                              "cards_sha256": digest(cards_path.read_bytes()), "encoder": "JPEG95 4:4:4 / PNG; native dimensions"}}
    manifest_path = output / "catalog.json"
    if len((json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")) > MAX_MANIFEST_BYTES:
        raise ValueError("Catalog exceeds the runtime 16 MiB manifest limit")
    if manifest_path.exists() and read_json(manifest_path) != catalog:
        raise ValueError("Output already contains a different catalog; use a new version directory")
    write_json(manifest_path, catalog)
    write_json(output / "coverage.json", report)
    return catalog


def validate_image_metadata(card):
    if (not isinstance(card, dict) or not isinstance(card.get("sha256"), str)
            or not SHA256.fullmatch(card["sha256"]) or card.get("format") not in ("jpg", "png")
            or type(card.get("bytes")) is not int or not 0 < card["bytes"] <= MAX_IMAGE_BYTES
            or any(type(card.get(key)) is not int or not 0 < card[key] <= MAX_IMAGE_DIMENSION
                   for key in ("width", "height"))):
        raise ValueError("Image metadata exceeds the runtime format, size, or dimension limits")


def verify(catalog: dict, directory: Path, allow_draft: bool = False):
    if catalog.get("schema_version") != SCHEMA_VERSION or (not allow_draft and catalog.get("release_ready") is not True):
        raise ValueError("Unsupported or incomplete artwork catalog")
    safe_id(catalog["catalog_id"])
    if len((json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")) > MAX_MANIFEST_BYTES:
        raise ValueError("Catalog exceeds the runtime 16 MiB manifest limit")
    for identifier, card in catalog["cards"].items():
        safe_id(identifier)
        validate_image_metadata(card)
    declared = set()
    for pack_id, pack in catalog["packs"].items():
        safe_id(pack_id)
        path = directory / f"{pack_id}.zip"
        if path.stat().st_size > MAX_PACK_BYTES:
            raise ValueError("Pack exceeds the runtime 64 MiB limit")
        payload = path.read_bytes()
        if len(payload) > MAX_PACK_BYTES or len(payload) != pack["bytes"] or digest(payload) != pack["sha256"]:
            raise ValueError("Pack integrity check failed")
        required = {}
        for identifier in pack["files"]:
            if identifier in declared or catalog["cards"][identifier]["pack_id"] != pack_id:
                raise ValueError("Duplicate or inconsistent pack membership")
            declared.add(identifier)
            card = catalog["cards"][identifier]
            required[f"cards/{card['sha256']}.{card['format']}"] = {
                key: card[key] for key in ("sha256", "bytes", "width", "height", "format")}
        expected = pack.get("members", required)
        if any(name not in expected or expected[name] != card for name, card in required.items()):
            raise ValueError("Current artwork does not match the archive member inventory")
        for name, card in expected.items():
            validate_image_metadata(card)
            if name != f"cards/{card['sha256']}.{card['format']}":
                raise ValueError("Invalid archive member inventory")
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != set(expected):
                raise ValueError("Unexpected, duplicate, or missing pack files")
            for name, card in expected.items():
                info = archive.getinfo(name)
                if (info.file_size != card["bytes"] or info.compress_type != zipfile.ZIP_STORED
                        or info.is_dir() or info.flag_bits & 1
                        or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)):
                    raise ValueError("Unexpected ZIP compression or image size")
                raw = archive.read(name)
                if digest(raw) != card["sha256"] or len(raw) != card["bytes"]:
                    raise ValueError("Card integrity check failed")
                with Image.open(BytesIO(raw)) as image:
                    if image.size != (card["width"], card["height"]) or image.format != {"jpg": "JPEG", "png": "PNG"}[card["format"]]:
                        raise ValueError("Image dimensions or format mismatch")
                    if getattr(image, "n_frames", 1) != 1:
                        raise ValueError("Animated files are not card artwork")
                    image.verify()
                # JPEG verify() validates its header but can accept truncated
                # pixel data; the runtime also decodes before installing.
                with Image.open(BytesIO(raw)) as image:
                    image.load()
    if declared != set(catalog["cards"]):
        raise ValueError("Some artwork is not assigned to a pack")
    for identifier in catalog["aliases"]:
        if canonical(identifier, catalog["aliases"]) not in set(catalog["cards"]) | set(catalog.get("generated", {})) | set(catalog.get("bundled", {})):
            raise ValueError("Dangling artwork alias")


def contacts(mapping: dict, sheets: Path, output: Path, identifiers=None):
    """Preview reviewed or unreviewed pinned crops, without changing review flags."""
    from PIL import ImageDraw, ImageFont
    output.mkdir(parents=True, exist_ok=True)
    entries = {key: value for key, value in mapping.get("mappings", {}).items()
               if (identifiers is None or key in identifiers) and value["source"].get("sheet_sha256")}
    thumbnails = {}
    for identifier, (raw, _, _, _) in iter_extracted(entries, sheets):
        with Image.open(BytesIO(raw)) as image:
            image.thumbnail((258, 388))
            out = BytesIO()
            image.save(out, format="PNG")
            thumbnails[identifier] = out.getvalue()
    items = list(sorted(entries.items()))
    font = ImageFont.load_default(size=18)
    for offset in range(0, len(items), 24):
        page = Image.new("RGB", (1600, 1800), "white")
        draw = ImageDraw.Draw(page)
        for slot, (identifier, entry) in enumerate(items[offset:offset + 24]):
            x, y = (slot % 6) * 266, (slot // 6) * 450
            with Image.open(BytesIO(thumbnails[identifier])) as image:
                page.paste(image, (x, y))
            draw.text((x + 3, y + 391), identifier + " " + entry["source"]["face"], fill="black", font=font)
            label = entry.get("expected", entry["source"].get("name", ""))
            draw.text((x + 3, y + 415), str(label)[:25], fill="black", font=font)
            draw.text((x + 3, y + 435), "REVIEWED" if entry.get("reviewed") else "PENDING", fill="black", font=font)
        page.save(output / f"contact-{offset // 24 + 1:04}.jpg", quality=92)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="Fetch the exact pinned Workshop snapshot")
    fetch.add_argument("--pin", type=Path, required=True)
    fetch.add_argument("--output", type=Path, required=True)
    acquire = commands.add_parser("fetch-sheets", help="Stage exact Workshop sheets for review, with two workers maximum")
    acquire.add_argument("--mapping", type=Path, required=True)
    acquire.add_argument("--snapshot", type=Path, required=True)
    acquire.add_argument("--cache", type=Path, required=True)
    acquire.add_argument("--output-mapping", type=Path, required=True)
    acquire.add_argument("--ids", nargs="+")
    acquire.add_argument("--seed", action="append", nargs=2, metavar=("SOURCE_URL", "LOCAL_FILE"))
    alternate = commands.add_parser("stage-alternate", help="Pin a manually sourced clean image or native PDF embedded image")
    alternate.add_argument("--mapping", type=Path, required=True)
    alternate.add_argument("--id", required=True)
    alternate.add_argument("--source-id", required=True)
    alternate.add_argument("--url", required=True)
    alternate.add_argument("--file", type=Path, required=True)
    alternate.add_argument("--sha256", required=True)
    alternate.add_argument("--cache", type=Path, required=True)
    alternate.add_argument("--kind", choices=("image", "pdf_image", "pdf_page"), default="image")
    alternate.add_argument("--page", type=int)
    alternate.add_argument("--xref", type=int)
    alternate.add_argument("--crop", nargs=4, type=int)
    alternate.add_argument("--render-dpi", type=int, default=300)
    alternate.add_argument("--output-mapping", type=Path, required=True)
    for command in ("inspect", "build"):
        sub = commands.add_parser(command)
        sub.add_argument("--pin", type=Path, required=True)
        sub.add_argument("--snapshot", type=Path, required=True)
        sub.add_argument("--cards", type=Path, default=Path("data/cards.json"))
        sub.add_argument("--output", type=Path, required=True)
        if command == "build":
            sub.add_argument("--mapping", type=Path, required=True)
            sub.add_argument("--sheets", type=Path, required=True)
            sub.add_argument("--catalog-id", required=True)
            sub.add_argument("--base-url", required=True)
            sub.add_argument("--previous", type=Path)
            sub.add_argument("--draft", action="store_true")
    check = commands.add_parser("verify")
    check.add_argument("--catalog", type=Path, required=True)
    check.add_argument("--allow-draft", action="store_true")
    preview = commands.add_parser("contacts")
    preview.add_argument("--mapping", type=Path, required=True)
    preview.add_argument("--sheets", type=Path, required=True)
    preview.add_argument("--output", type=Path, required=True)
    preview.add_argument("--ids", nargs="+")
    args = parser.parse_args(argv)
    if args.command == "fetch":
        pin = read_json(args.pin)["snapshot"]
        download(pin["url"], args.output, pin["sha256"], pin["bytes"], MAX_SNAPSHOT_BYTES)
    elif args.command == "verify":
        verify(read_json(args.catalog), args.catalog.parent, args.allow_draft)
    elif args.command == "contacts":
        contacts(read_json(args.mapping), args.sheets, args.output, args.ids)
    elif args.command == "fetch-sheets":
        mapping = read_json(args.mapping)
        snapshot = load_snapshot(args.snapshot, mapping["source_pin"])
        failures = fetch_sheets(mapping, snapshot, args.cache, args.ids, dict(args.seed or []))
        write_json(args.output_mapping, mapping)
        if failures:
            write_json(args.cache / "fetch-failures.json", failures)
            raise ValueError(f"{len(failures)} source sheets failed; successful pins saved; rerun to resume")
    elif args.command == "stage-alternate":
        mapping = stage_alternate(read_json(args.mapping), args.id, args.source_id, args.url,
                                  args.file, args.sha256, args.cache, args.kind, args.page, args.xref, args.crop, args.render_dpi)
        write_json(args.output_mapping, mapping)
    else:
        pin = read_json(args.pin)
        snapshot = load_snapshot(args.snapshot, pin)
        if args.command == "inspect":
            inspect(snapshot, args.cards, pin, args.output)
        else:
            mapping = read_json(args.mapping)
            if mapping.get("source_pin") != pin:
                raise ValueError("Mapping uses a different pinned Workshop snapshot")
            build(mapping, args.cards, snapshot, args.sheets, args.output, args.catalog_id,
                  args.base_url, args.draft, read_json(args.previous) if args.previous else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
