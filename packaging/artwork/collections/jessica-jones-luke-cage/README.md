# Jessica Jones and Luke Cage artwork

Both packs are enabled in normal play. Their reviewed mappings are integrated
into the main recipe and the published
[artwork-2026-10-16-1 catalog](https://github.com/sdolle1775/marvel-lcg/releases/tag/artwork-2026-10-16-1).
The full catalog contains 4,139 images in 75 archives, reusing 72 existing
archives and adding 36,897,821 bytes across three new archives. All public new
downloads were checked against their catalog hashes and decoded successfully.

This directory preserves the standalone artwork review. Its `cards.json`
contains only artwork identities, titles and types; it is not a replacement for
`data/cards.json`. Its `reviewed-mapping.json` records this collection's source
decisions, also merged into the main recipe.

| Pack | Reviewed card faces | October Hall of Heroes originals | Reprints |
| --- | ---: | ---: | ---: |
| Jessica Jones (`jj`) | 43 | 41 | 2 |
| Luke Cage (`luke_cage`) | 38 | 34 | 4 |

Both hero and alter-ego faces are included. Jessica's three Suggestion cards are
separate energy, mental and physical variants. Repeated physical copies of the
same card share a single image.

Sources: [Jessica Jones](https://hallofheroeslcg.com/jessica-jones/) and
[Luke Cage](https://hallofheroeslcg.com/luke-cage/), reviewed on October 16, 2026.
All 75 original files were re-fetched and matched to the hashes of the originals
used for the six reviewed contact sheets. The originals are 710 × 1,030 pixels,
or 1,030 × 710 for landscape cards. No cropping or resizing is applied. The 67
portrait originals retain their exact JPEG bytes; eight landscape originals are
rotated 90 degrees counterclockwise and saved as lossless PNG so their titles
sit on the left before the game's CSS rotation.

## Six reprint matches

Each match was checked visually for title, type, cost/resources and rules, and
against the source card data's explicit `duplicate_of_code`. Existing printed
edition numbers are retained. These are intentional reprint images, not scans
claiming to show the missing pack-specific printing.

| Missing ID | Card | Existing artwork ID |
| --- | --- | --- |
| 61018 | Lay Down the Law | 12031 (Ant-Man) |
| 61022 | Determination | 21052 (Mad Titan's Shadow) |
| 62024 | Unbreakable Bond | 61027 (Jessica Jones, Hall of Heroes) |
| 62025 | Energy | 01088 (existing library) |
| 62026 | Genius | 01089 (existing library) |
| 62027 | Strength | 01090 (existing library) |

The existing library's three resource images use its reviewed 2022 reprint
illustrations. The five Workshop matches retain their original source pins,
exact crops and encoded image hashes. Unbreakable Bond reuses the unchanged
Jessica Jones original. The result covers 81 IDs with 80 distinct images.

## Rebuild and verify

Run from the repository root with the retained source cache. The 75 original
JPEGs are pinned under `alternate_sources`; their exact bytes must exist at both
`sheets/<sha256>` and `sheets/originals/<sha256>`. The five Workshop reprints use
two existing pinned sheets in that same cache. Source files and ZIPs are excluded
from Git; all provenance and review decisions are in this directory.

```powershell
.venv-release\Scripts\python.exe packaging/artwork/importer.py build --pin packaging/artwork/source-pin.json --snapshot release-artifacts/image-source-audit/workshop-content.json --cards packaging/artwork/collections/jessica-jones-luke-cage/cards.json --mapping packaging/artwork/collections/jessica-jones-luke-cage/reviewed-mapping.json --sheets release-artifacts/artwork-production/sheets --catalog-id artwork-jj-luke-2026-10-16-1 --base-url https://github.com/sdolle1775/marvel-lcg/releases/download/artwork-jj-luke-2026-10-16-1 --output release-artifacts/hoh-packs-20261016/artwork-jj-luke-2026-10-16-1
.venv-release\Scripts\python.exe packaging/artwork/importer.py verify --catalog release-artifacts/hoh-packs-20261016/artwork-jj-luke-2026-10-16-1/catalog.json
```

These commands reproduce the original local, standalone candidate. Its
`artwork-jj-luke-2026-10-16-1` URL is not a published release. Normal play uses
the full `artwork-2026-10-16-1` catalog, built with `data/cards.json`, the main
`packaging/artwork/reviewed-mapping.json`, and `--previous` pointing to the prior
application catalog. The full recipe also needs the PDF dependencies from
`packaging/artwork/requirements-pdf.txt`. This preserves existing images,
aliases and dependencies; the standalone catalog must not replace the full one.

Use a new catalog ID/output directory for any changed recipe and publish its
assets before activating it. Keep artwork releases from replacing the latest
application release. The normal-play validation is recorded in
`data/experimental/jj_luke/normal-play-review.json`; that directory name is
retained for the historical review records.
