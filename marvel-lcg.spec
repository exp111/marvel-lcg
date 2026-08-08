from pathlib import Path


project_root = Path(SPECPATH).resolve()


def python_modules_under(folder: Path) -> list[str]:
    modules: set[str] = set()
    for source in folder.rglob("*.py"):
        parts = list(source.relative_to(project_root).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            modules.add(".".join(parts))
    return sorted(modules)


# Card abilities are imported dynamically from IDs such as
# cards.pack.mut_gen.sabretooth.32060. PyInstaller cannot discover those
# imports automatically, and collect_submodules("cards") fails because
# importing the package in isolation encounters the engine's circular imports.
card_hiddenimports = python_modules_under(project_root / "cards")


a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=card_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="marvel-lcg",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(project_root / "public" / "favicon.ico")],
)
