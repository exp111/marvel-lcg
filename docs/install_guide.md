# Install Guide

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
