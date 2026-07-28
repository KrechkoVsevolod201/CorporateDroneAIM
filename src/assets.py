from __future__ import annotations

import shutil
from pathlib import Path

from .config import ROOT

SOUNDS_DIR = ROOT / "sounds"
WEAPONS_DIR = ROOT / "assets" / "weapons"
GLOVES_DIR = ROOT / "assets" / "gloves"

AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac"}
IMAGE_EXTS = {".png", ".webp"}

NONE_LABEL = "(нет)"


def ensure_asset_dirs() -> None:
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    WEAPONS_DIR.mkdir(parents=True, exist_ok=True)
    GLOVES_DIR.mkdir(parents=True, exist_ok=True)


def list_sound_files() -> list[str]:
    ensure_asset_dirs()
    files = [
        p.name
        for p in sorted(SOUNDS_DIR.iterdir(), key=lambda x: x.name.lower())
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    ]
    return files


def list_weapon_images() -> list[str]:
    ensure_asset_dirs()
    return [
        p.name
        for p in sorted(WEAPONS_DIR.iterdir(), key=lambda x: x.name.lower())
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]


def list_glove_images() -> list[str]:
    ensure_asset_dirs()
    return [
        p.name
        for p in sorted(GLOVES_DIR.iterdir(), key=lambda x: x.name.lower())
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]


def sound_path(name: str) -> Path | None:
    if not name or name == NONE_LABEL:
        return None
    path = SOUNDS_DIR / Path(name).name
    return path if path.is_file() else None


def weapon_image_path(name: str) -> Path | None:
    if not name or name == NONE_LABEL:
        return None
    path = WEAPONS_DIR / Path(name).name
    return path if path.is_file() else None


def glove_image_path(name: str) -> Path | None:
    if not name or name == NONE_LABEL:
        return None
    path = GLOVES_DIR / Path(name).name
    return path if path.is_file() else None


def import_image(src: str | Path, kind: str) -> str:
    """Copy image into assets folder. kind: 'weapon' | 'gloves'. Returns stored filename."""
    ensure_asset_dirs()
    src_path = Path(src)
    if not src_path.is_file():
        raise FileNotFoundError(str(src_path))
    if src_path.suffix.lower() not in IMAGE_EXTS:
        raise ValueError("Нужен PNG/WebP с прозрачностью")
    dest_dir = WEAPONS_DIR if kind == "weapon" else GLOVES_DIR
    dest = dest_dir / src_path.name
    if src_path.resolve() != dest.resolve():
        shutil.copy2(src_path, dest)
    return dest.name


def import_sound(src: str | Path) -> str:
    ensure_asset_dirs()
    src_path = Path(src)
    if not src_path.is_file():
        raise FileNotFoundError(str(src_path))
    if src_path.suffix.lower() not in AUDIO_EXTS:
        raise ValueError("Поддерживаются mp3/wav/ogg")
    dest = SOUNDS_DIR / src_path.name
    if src_path.resolve() != dest.resolve():
        shutil.copy2(src_path, dest)
    return dest.name
