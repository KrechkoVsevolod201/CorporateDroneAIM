from __future__ import annotations

import shutil
from pathlib import Path

from .config import app_dir, bundle_dir

AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac"}
IMAGE_EXTS = {".png", ".webp"}

NONE_LABEL = "(нет)"


def _user_shot_sounds() -> Path:
    return app_dir() / "sounds" / "shot"


def _user_shell_sounds() -> Path:
    return app_dir() / "sounds" / "shell"


def _user_weapons() -> Path:
    return app_dir() / "assets" / "weapons"


def _user_gloves() -> Path:
    return app_dir() / "assets" / "gloves"


def _bundle_shot_sounds() -> Path:
    return bundle_dir() / "sounds" / "shot"


def _bundle_shell_sounds() -> Path:
    return bundle_dir() / "sounds" / "shell"


def _bundle_weapons() -> Path:
    return bundle_dir() / "assets" / "weapons"


def _bundle_gloves() -> Path:
    return bundle_dir() / "assets" / "gloves"


# Back-compat aliases
SOUNDS_DIR = app_dir() / "sounds"
WEAPONS_DIR = app_dir() / "assets" / "weapons"
GLOVES_DIR = app_dir() / "assets" / "gloves"


def ensure_asset_dirs() -> None:
    _user_shot_sounds().mkdir(parents=True, exist_ok=True)
    _user_shell_sounds().mkdir(parents=True, exist_ok=True)
    _user_weapons().mkdir(parents=True, exist_ok=True)
    _user_gloves().mkdir(parents=True, exist_ok=True)
    _seed_defaults()


def _seed_defaults() -> None:
    """Copy bundled defaults next to exe on first run (if missing)."""
    _copy_missing(_bundle_shot_sounds(), _user_shot_sounds(), AUDIO_EXTS)
    _copy_missing(_bundle_shell_sounds(), _user_shell_sounds(), AUDIO_EXTS)
    _copy_missing(_bundle_weapons(), _user_weapons(), IMAGE_EXTS)
    _copy_missing(_bundle_gloves(), _user_gloves(), IMAGE_EXTS)


def _copy_missing(src: Path, dst: Path, exts: set[str]) -> None:
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    try:
        for p in src.iterdir():
            if p.is_file() and p.suffix.lower() in exts:
                target = dst / p.name
                if not target.exists():
                    shutil.copy2(p, target)
    except OSError:
        pass


def _list_files(dirs: list[Path], exts: set[str]) -> list[str]:
    names: dict[str, Path] = {}
    # later dirs override earlier — put user last so it wins
    for d in dirs:
        if not d.is_dir():
            continue
        try:
            for p in d.iterdir():
                if p.is_file() and p.suffix.lower() in exts:
                    names[p.name] = p
        except OSError:
            continue
    return sorted(names.keys(), key=str.lower)


def list_shot_sound_files() -> list[str]:
    ensure_asset_dirs()
    return _list_files([_bundle_shot_sounds(), _user_shot_sounds()], AUDIO_EXTS)


def list_shell_sound_files() -> list[str]:
    ensure_asset_dirs()
    return _list_files([_bundle_shell_sounds(), _user_shell_sounds()], AUDIO_EXTS)


def list_weapon_images() -> list[str]:
    ensure_asset_dirs()
    return _list_files([_bundle_weapons(), _user_weapons()], IMAGE_EXTS)


def list_glove_images() -> list[str]:
    ensure_asset_dirs()
    return _list_files([_bundle_gloves(), _user_gloves()], IMAGE_EXTS)


def _resolve(name: str, dirs: list[Path]) -> Path | None:
    if not name or name == NONE_LABEL:
        return None
    fname = Path(name).name
    for d in dirs:
        path = d / fname
        if path.is_file():
            return path
    return None


def shot_sound_path(name: str) -> Path | None:
    return _resolve(name, [_user_shot_sounds(), _bundle_shot_sounds()])


def shell_sound_path(name: str) -> Path | None:
    return _resolve(name, [_user_shell_sounds(), _bundle_shell_sounds()])


def weapon_image_path(name: str) -> Path | None:
    return _resolve(name, [_user_weapons(), _bundle_weapons()])


def glove_image_path(name: str) -> Path | None:
    return _resolve(name, [_user_gloves(), _bundle_gloves()])


def import_image(src: str | Path, kind: str) -> str:
    """Copy image into user assets. kind: 'weapon' | 'gloves'."""
    ensure_asset_dirs()
    src_path = Path(src)
    if not src_path.is_file():
        raise FileNotFoundError(str(src_path))
    if src_path.suffix.lower() not in IMAGE_EXTS:
        raise ValueError("Нужен PNG/WebP с прозрачностью")
    dest_dir = _user_weapons() if kind == "weapon" else _user_gloves()
    dest = dest_dir / src_path.name
    if src_path.resolve() != dest.resolve():
        shutil.copy2(src_path, dest)
    return dest.name


def import_sound(src: str | Path, kind: str = "shot") -> str:
    ensure_asset_dirs()
    src_path = Path(src)
    if not src_path.is_file():
        raise FileNotFoundError(str(src_path))
    if src_path.suffix.lower() not in AUDIO_EXTS:
        raise ValueError("Поддерживаются mp3/wav/ogg")
    dest_dir = _user_shot_sounds() if kind == "shot" else _user_shell_sounds()
    dest = dest_dir / src_path.name
    if src_path.resolve() != dest.resolve():
        shutil.copy2(src_path, dest)
    return dest.name
