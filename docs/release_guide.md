# Release build guide

This repository produces a Windows application package containing code, game data,
the artwork manifest and required interface assets. Reviewed standard card scans
are distributed separately in immutable artwork packs and prepared in a persistent
user library before first play.

## Package contents

The main archive contains:

- `marvel-lcg.exe`
- game data and the compiled browser interface
- starter decks
- sounds and interface textures, including card backs, status cards, placeholders, and set images
- default `launch.json`
- patch notes and attribution

The package deliberately excludes:

- `assets/cache`, which retains legacy and custom-provider downloads
- `assets/pics`, which is reserved for an optional offline or custom image pack
- `campaign_settings.json`, which users carry forward from their previous build to retain saved campaign setup choices
- saves, statistics, crash logs, virtual environments, source maps, and developer build output

The empty `assets/cache` and `assets/pics` paths are created at staging time. Empty
directories do not necessarily appear in the ZIP. The managed artwork library is
outside this staging directory and is never copied into the application archive.

## Artwork preparation and release gate

Follow [the maintainer artwork workflow](../packaging/artwork/README.md). Use the
pinned Workshop snapshot, record exact sheet hashes and provenance, and review
every mapping. Check contact sheets for the complete collection and inspect each
ambiguous title, resource variant, reverse face, villain stage and reprint.
Keep native scan dimensions, borders and printed credits. Sources genuinely
missing from the Workshop need a separately pinned, visually verified alternative.

Build immutable archives no larger than 64 MiB, grouped by content release. Publish
them as versioned GitHub release assets separately from the executable. Never put
scan bytes in Git history, replace an existing immutable archive, or certify a
developer's old runtime cache as reviewed artwork. Later corrections add small
packs; unchanged archives remain reusable.

Commit `packaging/artwork/reviewed-mapping.json` and the matching
`data/artwork-manifest.json`. The build preflight checks complete official image
coverage, aliases, reviewed mapping provenance and bundled textures, then reads
back every hosted archive and verifies all image hashes, dimensions and contents.
It fails before packaging if anything is incomplete or unavailable. Publishing
artwork assets does not publish an application release. Published v1.3.3 files
must remain unchanged.

## Local preparation

Release packages are frozen to Python 3.12.13 and the fully pinned dependency graph in `requirements-release.txt`. From the repository root, create the virtual environment with that exact interpreter and install the release dependencies:

```powershell
$releasePython = "C:\path\to\python-3.12.13\python.exe"
& $releasePython -m venv .venv-release
& ".\.venv-release\Scripts\python.exe" -m pip install -r requirements-release.txt
npm install --global typescript
```

The release build intentionally uses PyInstaller's one-folder mode with UPX disabled. The ZIP contains `marvel-lcg.exe` beside an `_internal` dependency directory, avoiding the temporary self-extraction behavior of one-file executables.

The established v1.3.2/v1.3.3 workflow uses `-CustomBootloader` with the hash-verified v1.1.1 bootloader at PyInstaller's `Windows-64bit-intel\run.exe` path. Preflight verifies its SHA-256 before packaging and refuses a drifted runtime or bootloader. Retain this option for the artwork update.

Run the non-mutating preflight first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\packaging\build_release.ps1" -CustomBootloader -PreflightOnly
```

Build the archive and SHA-256 checksum:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\packaging\build_release.ps1" -CustomBootloader
```

Artifacts are written to `release-artifacts/`. The build script stages only an explicit allowlist; it never copies `assets/cache` or `assets/pics` into the main package.

## GitHub build

The **Build Windows release** workflow can be run manually for testing. Pushing a `v*` tag also builds and retains the package as a workflow artifact. It does not publish a GitHub Release automatically, leaving publication as an explicit maintainer decision.

## Release checklist

1. Confirm `PATCH_NOTES.md` describes the final implementation rather than intermediate or reverted work.
2. Update the four-part application version in `build.py` if a new application build number is required.
3. Regenerate and verify the checksum stored in `data/cards.json` after any card-database edit.
4. Run the focused artwork, identity, WebP, preview, replay and release tests and compile the TypeScript client. Do not run the mutating full test-discovery workflow or `unit_test.test_task`.
5. Run `build_release.ps1 -PreflightOnly`, then build the archive.
6. Inspect the ZIP and verify that `assets/cache`, `assets/pics`, saves, statistics, and crash logs contain no files.
7. Extract the ZIP into a clean directory and start `marvel-lcg.exe` from that directory.
8. Smoke-test first-time preparation, pause/restart/failure recovery, offline reuse from another installation directory, deck editing, browsing, flips, saves/replays, campaign setup, hotseat, LAN and Cloudflare in source and frozen builds. Confirm updates preserve existing games and only fetch missing/changed artwork. Inspect White Tiger, Gambit/Iceman identities, reversed physical identities, both Rhino scheme faces, villain stages, duplicates and reprints.
9. Verify the published ZIP against its `.sha256` file.
10. Scan `marvel-lcg.exe` with Microsoft Defender and review the result before publishing. Submit the ZIP or executable to VirusTotal only when release policy permits third-party redistribution of the sample.
11. Publish the archive with `PATCH_NOTES.md`, remind users to copy and overwrite `campaign_settings.json` into the new build folder, and credit the Irefrixs Team.

Public releases should eventually be Authenticode-signed. Azure Artifact Signing is Microsoft's recommended non-Store option; qualifying open-source projects can also investigate SignPath Foundation.

## Local artwork overrides

Users can still place their own art in `assets/pics` or configure `image_folders`.
These explicit local overrides take precedence over managed images. The managed
pack library and the original `cache_folder` setting have separate meanings; do
not migrate saves or other user files into the artwork directory.
