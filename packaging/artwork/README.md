# Preparing reviewed artwork

This is maintainer tooling, excluded from the game executable. The game downloads
small immutable image packs, never the large Workshop sheets or Workshop scripts.
The source pin records the exact raw BSON snapshot from Workshop item 2665262903.
Changing that pin is an explicit artwork source update.

Run these commands from the repository with the release Python environment. Only
Pillow and Requests are required. The BSON reader treats scripts as inert strings.

```powershell
.venv-release\Scripts\python.exe packaging/artwork/importer.py fetch --pin packaging/artwork/source-pin.json --output release-artifacts/artwork/source.bson
.venv-release\Scripts\python.exe packaging/artwork/importer.py inspect --pin packaging/artwork/source-pin.json --snapshot release-artifacts/artwork/source.bson --cards data/cards.json --output release-artifacts/artwork/draft
.venv-release\Scripts\python.exe packaging/artwork/importer.py fetch-sheets --mapping release-artifacts/artwork/draft/mapping-draft.json --snapshot release-artifacts/artwork/source.bson --cache release-artifacts/artwork/sheets --output-mapping release-artifacts/artwork/pinned-mapping.json --ids 21013 37001a 37001b
.venv-release\Scripts\python.exe packaging/artwork/importer.py contacts --mapping release-artifacts/artwork/pinned-mapping.json --sheets release-artifacts/artwork/sheets --output release-artifacts/artwork/contacts
```

`inspect` writes a draft, all candidate alternatives, and a coverage report. It
suggests exact names, paired reverse faces, contextual matches, and approximate
titles. **No suggestion is approved automatically.** Default first candidates can
be wrong for villain stages, schemes, reprints, and common titles. Compare printed
name, set, card number, stage, face, and orientation with the game data. Resolve
ambiguities by selecting the correct scoped object in `candidates.json`; the
Workshop object's deck key need not match the prefix of its CardID.

`fetch-sheets` accepts only exact image URLs in the pinned source objects, permits
no redirects, limits each response to 256 MiB, and uses two workers. A cache lock
coordinates simultaneous importer processes. The hash-named cache and
`sources.json` ledger preserve original bytes, dimensions, URL, and snapshot hash.
Successful acquisitions survive an interrupted batch; rerun to resume. Supply
`--seed SOURCE_URL LOCAL_FILE` to reuse a previously downloaded sheet. Seeding
records its hash and verifies image data; it does not certify which card it shows.
If an existing pin changes, acquisition stops instead of silently accepting new
content. Contacts decode each source once and mark each crop PENDING or REVIEWED.

A reviewed mapping entry has:

```json
{
  "reviewed": true,
  "review_note": "Visual comparison: printed title, set, stage and orientation verified.",
  "source": {
    "guid": "object GUID",
    "object_path": ["ObjectStates", 0],
    "deck_key": "1",
    "card_id": 100,
    "name": "Source object title",
    "parents": ["Pack name"],
    "face": "front",
    "sheet_url": "https://steamusercontent-a.akamaihd.net/ugc/ID/HASH/",
    "sheet_sha256": "64 lowercase hex characters",
    "columns": 1,
    "rows": 1,
    "index": 0
  },
  "rotation": 0
}
```

Quarter-turn rotation is counterclockwise. Face selection, grid dimensions, and
tile index are verified against the pinned object before building. Keep game IDs
and gameplay data unchanged. Store mapping-specific name corrections in review
notes, not in the card database. `full_link` and `pic_id` become artwork aliases;
`ability_link` does not.

For an official card genuinely absent from the pinned Workshop snapshot, use
`stage-alternate` with a previously downloaded source file, its exact SHA-256,
and an explicit HTTPS source URL from an allowlisted source. The initial release
uses Fantasy Flight Games and one specifically allowlisted FFG-provided Skilled
Investigator reveal. A manually reviewed clean MarvelCDB source is also accepted
by the tool; it is never fetched as a runtime fallback. This is
a reviewed exception, never an automatic fallback. For example:

```powershell
.venv-release\Scripts\python.exe packaging/artwork/importer.py stage-alternate --mapping packaging/artwork/reviewed-mapping.json --id CARD_ID --source-id REVIEWED_SOURCE_ID --url https://marvelcdb.com/bundles/cards/CARD_ID.jpg --file release-artifacts/artwork/source-image.jpg --sha256 SOURCE_SHA256 --cache release-artifacts/artwork/sheets --output-mapping release-artifacts/artwork/proposed-alternate.json
```

Use `--kind pdf_image --page ZERO_BASED_PAGE --xref EMBEDDED_IMAGE_XREF` for a
native embedded image in a pinned official PDF. Install `requirements-pdf.txt` in
the maintainer environment first. `--crop LEFT TOP RIGHT BOTTOM` selects explicit
source-image pixels when an embedded image contains multiple cards. PDF extraction
checks that the image xref belongs to the named page; it neither renders at an
arbitrary DPI nor runs document actions. Both the complete original document and
extracted-image hashes remain in provenance. When card titles or rules are PDF
vector text rather than part of an embedded image, use `--kind pdf_page --page N
--render-dpi 300` to preserve the complete card. The exact page and resolution are
pinned in the mapping; optional cropping still uses explicit rendered pixels.
Building rechecks the original and
reproduces the extraction. The resulting mapping is still PENDING until visual
review confirms the card and absence of watermarks.

Every nonnumbered image or alias target must have a reviewed `nonnumbered` entry:
`{"disposition":"builtin|generated|alias|mapped","reviewed":true,"reason":"..."}`.
An official card may not be classified as generated to bypass a missing scan.
Entries such as player/encounter backs, statuses, custom challenge text, and special
reference cards require explicit accounting. `mapped` entries also require a
reviewed artwork mapping; `alias` entries must actually have a database alias.

After all required images are reviewed:

```powershell
.venv-release\Scripts\python.exe packaging/artwork/importer.py build --pin packaging/artwork/source-pin.json --snapshot release-artifacts/artwork/source.bson --mapping packaging/artwork/reviewed-mapping.json --cards data/cards.json --sheets release-artifacts/artwork/sheets --catalog-id workshop-2026-08-v1 --base-url https://HOST/IMMUTABLE-RELEASE --output release-artifacts/artwork/workshop-2026-08-v1
.venv-release\Scripts\python.exe packaging/artwork/importer.py verify --catalog release-artifacts/artwork/workshop-2026-08-v1/catalog.json
.venv-release\Scripts\python.exe -m unittest unit_test.test_artwork_importer
```

The build stops for any uncovered numbered image or unaccounted special image.
`--draft` permits a partial diagnostic catalog but retains `release_ready:false`;
the runtime must reject it. Images retain native dimensions and are encoded as
JPEG quality 95, 4:4:4 chroma, or PNG when transparency is present. No watermark
removal or artificial resizing is performed. Each sheet is decoded once per build.
Each encoded card must fit the runtime's 4096-pixel and 16 MiB limits; an oversized
source or mistaken grid selection fails the build instead of silently resizing.
Verification checks every image's complete pixel decode as well as its hash,
dimensions, and ZIP metadata. `--draft` always produces `release_ready:false`,
even when its mapping coverage happens to be complete.

Catalog schema version 1 contains `catalog_id`, `release_ready`, `cards`, `aliases`,
`packs`, `dependencies`, `generated`, `bundled`, and provenance. Cards record SHA-256,
size, dimensions, format, and pack membership. Each pack also records a `members`
dictionary authenticating every physical ZIP member, including superseded images
inside a reused immutable archive. `files` contains only currently referenced card
IDs. Each ZIP is at most 64 MiB and holds
only `cards/<sha256>.<format>` members with deterministic timestamps. Duplicate image
bytes share a member. Dependencies cover card-data packs, registered scenarios,
encounter/nemesis sets, and campaign cards.

Publish packs at their declared immutable URLs before activating a matching
catalog in the game. Do not overwrite existing catalogs or assets. `--previous`
keeps unchanged images in their original packs and URLs, publishing corrections
in small new packs rather than repacking unaffected images. Old complete archive
inventories remain authenticated in `members`. To verify a reused catalog offline, copy or
link the referenced old ZIP files into the verification directory first. A source
or mapping update produces a new catalog; only changed packs need publication.

Release readiness is a data/coverage gate, not proof that a reviewer chose the
correct picture. Keep the reviewed mappings and review notes in Git, retain the
raw source/cache outside the executable, inspect all ambiguous cards, and run the
runtime offline, recovery, corruption, custom-override, and upgrade tests before
publishing a game release.

The initial `artwork-2026-10-11-1` catalog contains 4,060 reviewed images, 383
aliases, and 72 packs (1,818,830,230 download bytes). The individual `review-*.json`
files preserve the collection review batches; `reviewed-mapping.json` is the
complete authoritative input. Seven missing scans have pinned reviewed alternate
sources. Artwork releases must use `make_latest:false` so the application's
latest release remains unchanged; never replace assets on a published artwork tag.
