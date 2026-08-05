# Install Guide

## Updating a packaged release

Do not extract a new release over an existing Marvel LCG Digital folder. Extract
each release into a new, empty folder so old application, data, and interface
files cannot be mixed with the new build.

Copy only personal saves, replays, or custom decks that you want to keep. Do not
copy the previous executable, `public`, `data`, `assets/cache`, or `launch.json`
unless you intentionally need to migrate a setting. If a build older than
`1.0.0.1r` was previously opened, clear the browser's site data for
`127.0.0.1:2345` once if the interface still appears out of date.

## 1. Install python

https://www.python.org/ftp/python/

We've tested in py 3.10.5 and py 3.14.2

## 2. Install requirements

```cmd
pip install -r requirements.txt
```

## 3. Download nodejs

https://nodejs.org/en/download

## 4. Install typescript

```
npm install -g typescript
```

## 5. Compile ts to js

Double click to run "\public\js\watch.bat"

## 6. Card images

The repository includes the small sounds and interface textures required to run the game. Standard card artwork is downloaded on demand from the image servers configured in `launch.json` and stored in `assets/cache`.

For offline play, an optional image package can be placed in `assets/pics` or referenced through `image_folders` in `launch.json`.

## 7. Start the game

Run the game from the repository root so its relative data and asset paths resolve correctly:

```powershell
& ".\.venv\Scripts\python.exe" ".\main.py"
```
