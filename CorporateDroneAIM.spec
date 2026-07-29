# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

datas = [
    (str(root / "sounds" / "shot"), str(Path("sounds") / "shot")),
    (str(root / "sounds" / "shell"), str(Path("sounds") / "shell")),
    (str(root / "assets"), "assets"),
]

hiddenimports = [
    "pygame",
    "pygame.mixer",
    "pygame.font",
    "pygame.image",
    "pygame.transform",
    "pygame.display",
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "win32api",
    "win32con",
    "win32gui",
    "pywintypes",
    "keyboard",
    "keyboard._winkeyboard",
]

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pygame.tests",
        "pygame.examples",
        "cv2",
        "numpy.tests",
        "matplotlib",
        "scipy",
        "IPython",
        "notebook",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_file = root / "assets" / "icon" / "app.ico"
if not icon_file.is_file():
    # fallback: any .ico in assets/icon
    icons = list((root / "assets" / "icon").glob("*.ico")) if (root / "assets" / "icon").is_dir() else []
    icon_file = icons[0] if icons else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="CorporateDroneAIM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_file) if icon_file else None,
)
