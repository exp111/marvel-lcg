# Install Guide

## Updating a packaged release

Do not extract a new release over an existing Marvel LCG Digital folder. Extract
each release into a new, empty folder so old application, data, and interface
files cannot be mixed with the new build.

Copy `campaign_settings.json` from the old build folder into the new build
folder, replacing or overwriting the destination file if prompted. This file
contains the saved setup choices for every campaign. Also copy any personal
saves, replays, or custom decks that you want to keep. Do not copy the previous
executable, `public`, `data`, `assets/cache`, or `launch.json` unless you
intentionally need to migrate a setting. If a build older than `1.0.0.1r` was
previously opened, clear the browser's site data for
`127.0.0.1:2345` once if the interface still appears out of date.

## Running the development build on Windows

### 1. Install the prerequisites

Install [Python](https://www.python.org/downloads/) and
[Node.js](https://nodejs.org/en/download). Python 3.10 and Python 3.14 are
supported; the current development build has been verified with Python 3.14.

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

The repository includes the small sounds and interface textures required to run the game. Standard card artwork is downloaded on demand from the image servers configured in `launch.json` and stored in `assets/cache`.

For offline play, an optional image package can be placed in `assets/pics` or referenced through `image_folders` in `launch.json`.
