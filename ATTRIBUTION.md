# Attribution and distribution notice

Marvel LCG Digital was originally developed by the [Irefrixs Team](https://github.com/irefrixs/marvel-lcg) and is distributed by them on [itch.io](https://irefrixs.itch.io/marvel-lcg).

This repository is a community-maintained derivative build. The upstream developers have given permission for modified builds to be published while they work toward a permissive software license intended to keep the game free to play. No separate software license is asserted here on behalf of the upstream team.

Marvel, Marvel Champions: The Card Game, character names, card artwork, and related marks and assets belong to their respective owners. This project is unofficial, non-commercial, and is not affiliated with or endorsed by Marvel, Fantasy Flight Games, or their licensors.

The main application package does not contain standard card scans. The persistent artwork system uses separately distributed, verified artwork packs prepared from [Unicorn Snuggler's Marvel Champions High-Resolution Scans](https://steamcommunity.com/sharedfiles/filedetails/?id=2665262903), including the contributors credited in that Workshop collection. Source snapshot and sheet hashes, exact crops, faces and rotations are recorded by the maintainer importer. Printed illustrator credits and borders are retained. The Workshop scripts are not executed. Scanning and preparation credits do not imply ownership of the underlying card artwork.

Players download the prepared packs to their host's local library once and reuse unchanged content between application updates. Small sounds and interface textures remain bundled with the app. Published v1.3.3 assets are unchanged and continue to use their original artwork delivery code.

The initial catalog includes seven reviewed exceptions for scans absent from the pinned Workshop snapshot: Fantasy Flight Games' official Kree Fanatic print-and-play cards and Dynamic Duo preview, plus the FFG-provided Second Chance reveal published by [Skilled Investigator](https://skilledinvestigator.com/a-hardspoiled-investigator-previewing-every-unrevealed-card-for-jessica-jones-and-luke-cage-reacting-to-my-final-predictions/). Exact original file hashes and extraction details are retained in the catalog and reviewed mapping. No unreviewed MarvelCDB fallback is used.

The Jessica Jones and Luke Cage artwork collection uses 75 October 2026 original scans from [Hall of Heroes](https://hallofheroeslcg.com/), plus six reviewed reprint mappings to existing scans. Portrait originals retain their exact JPEG bytes; landscape originals use lossless PNG rotation for the game's display. The collection recipe records source URLs, hashes, matching card IDs and visual review notes. Both packs are included in the current source build and the published `artwork-2026-10-16-1` catalog.

Their bundled pack-selection thumbnails use the unchanged transparent product images from Fantasy Flight Games' [Jessica Jones](https://www.fantasyflightgames.com/product/jessica-jones/) and [Luke Cage](https://www.fantasyflightgames.com/product/luke-cage/) listings. Exact URLs and hashes are recorded in `packaging/artwork/collections/jessica-jones-luke-cage/pack-textures.json`.

`assets/textures/sparkles.gif` is an original community-build replacement animation for the ultra-rare card effect. The upstream source references this filename, but the upstream v0.5.9.200 download does not contain it.
