"""Fail a release build unless its complete reviewed artwork is already hosted.

This is a maintainer preflight. It does not publish assets or alter game data.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import Engine  # noqa: E402,F401 - project's import order
from engine.file.artwork import ArtworkManifest, MAX_PACK_BYTES  # noqa: E402


def importer_module():
    spec = importlib.util.spec_from_file_location("artwork_importer", ROOT / "packaging/artwork/importer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_release(manifest_path, mapping_path, cards_path):
    importer = importer_module()
    mapping = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
    manifest = ArtworkManifest.load(manifest_path)
    report = importer.coverage(mapping, Path(cards_path))
    if not manifest.release_ready or not report["release_ready"]:
        raise ValueError(f"Artwork release blocked: {len(report['unreviewed_images'])} images and "
                         f"{len(report['unaccounted_nonnumbered'])} special entries still need review")
    records, _, aliases = importer.card_database(Path(cards_path))
    missing = sorted(identifier for identifier in records if manifest.canonical_id(identifier) is None)
    if missing:
        raise ValueError("Artwork manifest does not cover game images: " + ", ".join(missing))
    for alias, target in aliases.items():
        if manifest.canonical_id(alias) != manifest.canonical_id(target):
            raise ValueError("Artwork alias disagrees with full_link/pic_id: " + alias)
    provenance = manifest.data.get("provenance", {})
    mapping_hash = sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()
    if provenance.get("mapping_sha256") != mapping_hash:
        raise ValueError("Artwork catalog does not match the reviewed mapping")
    if provenance.get("cards_sha256") != sha256(Path(cards_path).read_bytes()).hexdigest():
        raise ValueError("Artwork coverage must be rebuilt for the current card database")
    if provenance.get("source_pin") != mapping.get("source_pin"):
        raise ValueError("Artwork source provenance differs from the reviewed pin")
    for image_id in manifest.data.get("bundled", {}):
        if not any((ROOT / "assets/textures" / (image_id + extension)).is_file()
                   for extension in (".jpg", ".png", ".webp", ".gif")):
            raise ValueError("Missing bundled artwork: " + image_id)
    return manifest


def verify_hosted(manifest):
    """Read back every immutable asset, then validate its exact ZIP contents."""
    importer = importer_module()
    with tempfile.TemporaryDirectory(prefix="marvel-artwork-preflight-") as folder:
        directory = Path(folder)
        batches = [list(manifest.packs.items())[index::2] for index in range(2)]

        def fetch(batch):
            with requests.Session() as session:
                for pack_id, pack in batch:
                    print("Verifying hosted artwork:", pack_id, flush=True)
                    expected = pack["bytes"]
                    if expected > MAX_PACK_BYTES:
                        raise ValueError("Artwork archive exceeds 64 MiB")
                    size = 0
                    hashed = sha256()
                    with session.get(pack["url"], stream=True, timeout=(10, 30)) as response:
                        response.raise_for_status()
                        with (directory / (pack_id + ".zip")).open("wb") as output:
                            for chunk in response.iter_content(64 * 1024):
                                size += len(chunk)
                                if size > expected:
                                    raise ValueError("Hosted artwork archive exceeds declared size")
                                output.write(chunk)
                                hashed.update(chunk)
                    if size != expected or hashed.hexdigest() != pack["sha256"]:
                        raise ValueError("Hosted artwork checksum mismatch: " + pack_id)

        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(fetch, batch) for batch in batches]
            for future in futures:
                future.result()
        importer.verify(manifest.data, directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/artwork-manifest.json")
    parser.add_argument("--mapping", type=Path, default=ROOT / "packaging/artwork/reviewed-mapping.json")
    parser.add_argument("--cards", type=Path, default=ROOT / "data/cards.json")
    parser.add_argument("--verify-hosted", action="store_true")
    arguments = parser.parse_args()
    try:
        manifest = validate_release(arguments.manifest, arguments.mapping, arguments.cards)
        if arguments.verify_hosted:
            verify_hosted(manifest)
    except (OSError, ValueError, requests.RequestException) as error:
        parser.exit(1, f"Artwork release preflight failed: {error}\n")
    print(f"Artwork preflight passed: {len(manifest.cards)} images; {len(manifest.packs)} packs.")


if __name__ == "__main__":
    main()
