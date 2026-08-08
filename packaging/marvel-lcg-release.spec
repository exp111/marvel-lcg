from pathlib import Path
import os
import re

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)


project_root = Path(SPECPATH).resolve().parent


def python_modules_under(folder: Path) -> list[str]:
    """Return dynamically imported Python modules for PyInstaller."""
    modules: set[str] = set()
    for source in folder.rglob("*.py"):
        parts = list(source.relative_to(project_root).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            modules.add(".".join(parts))
    return sorted(modules)


# Card abilities are imported dynamically from card IDs. PyInstaller cannot
# discover those imports from the static import graph.
card_hiddenimports = python_modules_under(project_root / "cards")
release_hiddenimports = ["numpy", *card_hiddenimports]

# Developer-only modules provide source editing and arbitrary debug-command
# evaluation. They are useful in a checkout but are not release functionality.
release_excludes = [
    "editor",
    "engine.file.code_editor",
    "engine.security.command_validation",
    "game.world.cheat.cheat_cmd_helper",
    "unit_test",
]


def application_version() -> tuple[int, int, int, int]:
    build_text = (project_root / "build.py").read_text(encoding="utf-8")
    parts = []
    for name in ("MAJOR", "MINOR", "PATCH", "BUILD"):
        match = re.search(rf"(?m)^\s*{name}\s*=\s*(\d+)\s*$", build_text)
        if not match:
            raise ValueError(f"Could not read {name} from build.py")
        parts.append(int(match.group(1)))
    return tuple(parts)


version = application_version()
noarchive = os.environ.get("MARVEL_LCG_NOARCHIVE") == "1"
version_text = ".".join(str(part) for part in version)
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=version,
        prodvers=version,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable("040904B0", [
                StringStruct("CompanyName", "Marvel Champions Digital Community"),
                StringStruct("FileDescription", "Marvel Champions: Digital Edition Community Build"),
                StringStruct("FileVersion", version_text),
                StringStruct("InternalName", "marvel-lcg"),
                StringStruct("LegalCopyright", "Community-maintained open-source build"),
                StringStruct("OriginalFilename", "marvel-lcg.exe"),
                StringStruct("ProductName", "Marvel Champions: Digital Edition Community Build"),
                StringStruct("ProductVersion", version_text),
            ])
        ]),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)


a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=release_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=release_excludes,
    noarchive=noarchive,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="marvel-lcg",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(project_root / "public" / "favicon.ico")],
    version=version_info,
    contents_directory="_internal",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="marvel-lcg",
)
