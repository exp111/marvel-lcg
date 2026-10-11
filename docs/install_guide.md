# Install Guide

## Updating a packaged release

Do not extract a new release over an existing Marvel LCG Digital folder. Extract
each release into a new, empty folder so old application, data, and interface
files cannot be mixed with the new build.

Copy `campaign_settings.json` from the old build folder into the new build
folder, replacing or overwriting the destination file if prompted. This file
contains the saved setup choices for every campaign. Also copy any personal
saves, replays, or custom decks that you want to keep. The persistent artwork
library described below is shared between new installations on the same user
account. It does not need to be copied. Keep any existing `assets/cache` and
custom `assets/pics` files; do not delete them as an update step. Do not copy the previous
executable, `public`, `data`, or `launch.json` unless you
intentionally need to migrate a setting. If a build older than `1.0.0.1r` was
previously opened, clear the browser's site data for
`127.0.0.1:2345` once if the interface still appears out of date.

Packaged builds open a versioned main-menu URL after the local server starts.
The version in that URL changes with each application build, preventing an
older cached HTML document from replacing the current menu. Menu navigation
uses the same version when opening setup and utility pages.

## Running the development build on Windows

### 1. Install the prerequisites

Install [Python](https://www.python.org/downloads/) and
[Node.js](https://nodejs.org/en/download). Python 3.10 through Python 3.14 are
supported for running the source-code development build. The commands below use
Python 3.14 because the current development build has been verified with that
version.

This development environment is separate from the environment used to create
official releases. Reproducible release builds must use exactly Python 3.12.13
and the pinned release dependencies described in the [release guide](release_guide.md).

### 2. Download the source

Clone the repository and enter its root folder:

```powershell
git clone https://github.com/sdolle1775/marvel-lcg.git
cd marvel-lcg
```

Alternatively, download the repository ZIP from GitHub, extract it into a new
folder, and open PowerShell in that folder.

### 3. Create the Python environment

Run these commands from the repository root:

```powershell
py -3.14 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

If Python 3.14 is not installed, replace `-3.14` with the version you installed.

### 4. Compile the TypeScript client

Install TypeScript and compile the browser client once:

```powershell
npm install --global typescript
cmd /c tsc -p public\js\tsconfig.json
```

Using `cmd /c` avoids PowerShell execution-policy errors that can prevent the
`tsc.ps1` wrapper from running. Contributors actively editing TypeScript can
instead run `public\js\watch.bat` and leave that terminal open.

### 5. Start the game

Run the game from the repository root so its relative data and asset paths
resolve correctly:

```powershell
& ".\.venv\Scripts\python.exe" ".\main.py"
```

Open <http://127.0.0.1:2345/scene> if the setup page does not open
automatically. Close any older running copy of the game first because port
`2345` must be available.

### 6. Card images

Starting with **v1.3.3.1**, the artwork system prepares the complete reviewed collection before first
play. The **Card artwork** page opens automatically, shows download and storage
requirements, and provides Pause, Resume and Retry controls. Keep the host
application open while downloading. Closing and reopening the host resumes
unfinished work. Credits and diagnostics remain available during preparation.

The initial reviewed catalog contains 4,060 images in 72 packs and downloads
1,818,830,230 bytes (about 1.69 GiB). The preparation page shows the additional
storage required, including temporary download space. Later updates reuse
unchanged images and archives.

Artwork packs are separate from the application download. Once prepared, the
host serves images locally to its browser, LAN players and Cloudflare players.
They work offline and do not need to be downloaded again after extracting a
new application version into a different folder. Later versions download new
or corrected packs while previously prepared content remains available.

The default persistent library is:

| System | Location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\Marvel Champions Digital\artwork` |
| macOS | `~/Library/Application Support/Marvel Champions Digital/artwork` |
| Linux | `$XDG_DATA_HOME/marvel-champions-digital/artwork`, or `~/.local/share/marvel-champions-digital/artwork` |

Set `"artwork_folder": "D:/MarvelArtwork"` in `launch.json` to choose portable
or custom storage. Use the same folder in successive installations to reuse
the collection. An empty value selects the default location. `cache_folder`
retains its separate legacy/custom-cache meaning.

Old `assets/cache` files are left untouched. They are imported only if their
bytes match a reviewed manifest image. The first transition may therefore
download replacements for otherwise readable old images, including watermarked
copies. Explicit artwork in `image_folders`, including `assets/pics`, continues
to override managed images. Deliberately configured non-stock `image_servers`
remain available; copied stock Cerebro and MarvelCDB settings are ignored.

Sounds, card backs, Storm weather and sparkles remain bundled. This change does
not relocate saves, decks, campaign settings, statistics or replays.

#### Maintaining the local artwork library

- **Updating:** Extract the new application into a new folder and leave the artwork
  library in place. Reuse the same `artwork_folder` override if you configured one.
  The host checks the library at startup and downloads missing or changed packs.
  No manual artwork database update is needed. Open **Card artwork** on the main
  menu to see progress and maintenance help.
- **Recovering downloads:** Use **Resume** after pausing. For failures, read the
  displayed error, restore connectivity, free space or fix folder permissions,
  then use **Retry failed downloads**. Completed files are kept. Restarting the
  host checks stored images again and prepares missing or damaged files.
- **Backing up or moving:** Close every running copy of the host. Copy the entire
  artwork folder, including its subfolders, to the new location, then set
  `artwork_folder` in each installation's `launch.json` to that same location.
  Keep the original until the new location reports ready. Do not rename or edit
  managed image files; use `assets/pics` for intentional replacements.
- **Wrong images:** Check `assets/pics` and other configured `image_folders`
  first, because these personal overrides take priority. Old `assets/cache`
  contents do not certify a scan as reviewed. Do not erase the managed library
  to fix an individual image: removing it requires downloading it again.
- **Unsupported cards:** Jessica Jones and Luke Cage cards that have not been
  implemented lack both artwork and gameplay support. Importing them from
  MarvelCDB or retrying preparation does not add support.

Only the host needs the full collection. Remote players receive the images they
view from the host; Cloudflare multiplayer still needs its normal internet
connection. Artwork backup does not back up game progress: keep your saves,
replays, custom decks and `campaign_settings.json` separately.

The **v1.3.3 executable still uses the previous download system**. These library
instructions apply to v1.3.3.1 and later. A build reporting **Artwork catalog is
incomplete** cannot finish first-time preparation: its reviewed image catalog
has not passed the release gate. Retrying or deleting your files cannot fix an
incomplete catalog; use a complete application build.

## Updating the development build

The development build does not update automatically when changes are added to
GitHub. Close the game before updating, then follow the instructions that match
how you originally downloaded it.

### If you used `git clone`

Open PowerShell in your existing `marvel-lcg` folder and run:

```powershell
git pull origin master
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
cmd /c tsc -p public\js\tsconfig.json
& ".\.venv\Scripts\python.exe" ".\main.py"
```

The first command downloads the newest game files. The next two commands make
sure any updated Python requirements and browser files are ready, and the last
command starts the updated game. You normally do not need to clone the
repository again or recreate `.venv`.

If Git reports local changes, a merge conflict, or files that would be
overwritten, stop and ask for help rather than deleting or resetting files.

### If you used **Download ZIP** on GitHub

A downloaded ZIP cannot use `git pull`. Download the newest repository ZIP,
extract it into a new empty folder, and repeat steps 3 through 5 above. Do not
extract it over the old source folder. Copy personal saves, replays, custom
decks, and `campaign_settings.json` from the old folder if you want to keep
them.
