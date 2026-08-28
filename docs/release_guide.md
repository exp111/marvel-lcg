# Release build guide

This repository produces an official-style Windows package: application code and required interface assets are included, while standard card artwork is downloaded on demand and cached on the user's computer.

## Package contents

The main archive contains:

- `marvel-lcg.exe`
- game data and the compiled browser interface
- starter decks
- sounds and interface textures, including card backs, status cards, placeholders, and set images
- default `launch.json`
- patch notes and attribution

The package deliberately excludes:

- `assets/cache`, which is populated with downloaded card artwork during play
- `assets/pics`, which is reserved for an optional offline or custom image pack
- `campaign_settings.json`, which users carry forward from their previous build to retain saved campaign setup choices
- saves, statistics, crash logs, virtual environments, source maps, and developer build output

The empty `assets/cache` and `assets/pics` paths are created at staging time. Empty directories do not necessarily appear in the final ZIP, and the game can create its cache when needed.

## Local preparation

Release packages are frozen to Python 3.12.13 and the fully pinned dependency graph in `requirements-release.txt`. From the repository root, create the virtual environment with that exact interpreter and install the release dependencies:

```powershell
$releasePython = "C:\path\to\python-3.12.13\python.exe"
& $releasePython -m venv .venv-release
& ".\.venv-release\Scripts\python.exe" -m pip install -r requirements-release.txt
npm install --global typescript
```

The release build intentionally uses PyInstaller's one-folder mode with UPX disabled. The ZIP contains `marvel-lcg.exe` beside an `_internal` dependency directory, avoiding the temporary self-extraction behavior of one-file executables.

The v1.2.0 `-CustomBootloader` comparison build also requires the hash-verified v1.1.1 bootloader at PyInstaller's `Windows-64bit-intel\run.exe` path. Preflight verifies its SHA-256 before packaging and refuses a drifted runtime or bootloader.

Run the non-mutating preflight first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\packaging\build_release.ps1" -PreflightOnly
```

Build the archive and SHA-256 checksum:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\packaging\build_release.ps1"
```

Artifacts are written to `release-artifacts/`. The build script stages only an explicit allowlist; it never copies `assets/cache` or `assets/pics` into the main package.

## GitHub build

The **Build Windows release** workflow can be run manually for testing. Pushing a `v*` tag also builds and retains the package as a workflow artifact. It does not publish a GitHub Release automatically, leaving publication as an explicit maintainer decision.

## Release checklist

1. Confirm `PATCH_NOTES.md` describes the final implementation rather than intermediate or reverted work.
2. Update the four-part application version in `build.py` if a new application build number is required.
3. Regenerate and verify the checksum stored in `data/cards.json` after any card-database edit.
4. Run the unit tests and compile the TypeScript client.
5. Run `build_release.ps1 -PreflightOnly`, then build the archive.
6. Inspect the ZIP and verify that `assets/cache`, `assets/pics`, saves, statistics, and crash logs contain no files.
7. Extract the ZIP into a clean directory and start `marvel-lcg.exe` from that directory.
8. Smoke-test a new game, campaign setup, a remote card-image download, settings persistence, and hotseat play.
9. Verify the published ZIP against its `.sha256` file.
10. Scan `marvel-lcg.exe` with Microsoft Defender and review the result before publishing. Submit the ZIP or executable to VirusTotal only when release policy permits third-party redistribution of the sample.
11. Publish the archive with `PATCH_NOTES.md`, remind users to copy and overwrite `campaign_settings.json` into the new build folder, and credit the Irefrixs Team.

Public releases should eventually be Authenticode-signed. Azure Artifact Signing is Microsoft's recommended non-Store option; qualifying open-source projects can also investigate SignPath Foundation.

## Optional image package

An offline image collection should be distributed separately. Its directory structure should begin with `assets/pics`, allowing users to merge it into the installation or reference it through `image_folders` in `launch.json`. Do not build that optional package from a developer's unreviewed runtime cache.
