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

From the repository root, create the virtual environment and install the runtime and release dependencies:

```powershell
py -3.14 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-release.txt
npm install --global typescript
```

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
10. Publish the archive with `PATCH_NOTES.md`, remind users to copy and overwrite `campaign_settings.json` into the new build folder, and credit the Irefrixs Team.

## Optional image package

An offline image collection should be distributed separately. Its directory structure should begin with `assets/pics`, allowing users to merge it into the installation or reference it through `image_folders` in `launch.json`. Do not build that optional package from a developer's unreviewed runtime cache.
