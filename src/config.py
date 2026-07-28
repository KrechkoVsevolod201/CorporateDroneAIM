from __future__ import annotations

import json
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"

DEFAULTS: dict[str, Any] = {
    "scale": 1.0,
    "offset_x": 0,
    "offset_y": 0,
    "opacity": 0.92,
    "weapon": "rifle",
    "hands": "tactical",
    "muzzle_flash": True,
    "tracer": True,
    "impact": True,
    "recoil": True,
    "shell_eject": True,
    "sound": True,
    "shot_sound": "shot_sound_1.mp3",
    "shell_sound": "bullet_shell_drop.mp3",
    "shot_volume": 0.75,
    "shell_volume": 0.55,
    "use_custom_weapon": False,
    "custom_weapon": "",
    "custom_weapon_scale": 1.0,
    "use_custom_gloves": False,
    "custom_gloves": "",
    "custom_gloves_scale": 1.0,
    "fire_rate_ms": 90,
    "always_on_top": True,
    "click_through_idle": False,
}

WEAPONS = ("pistol", "rifle", "smg", "shotgun", "sniper")
HANDS = ("tactical", "bare", "gloves", "cyber")


class Config:
    """Thread-safe config with debounced disk writes."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._data = deepcopy(DEFAULTS)
        self._listeners: list[Callable[[dict[str, Any]], None]] = []
        self._dirty = False
        self._last_save = 0.0
        self._save_delay = 0.25
        self.load()

    def load(self) -> None:
        with self._lock:
            if CONFIG_PATH.exists():
                try:
                    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                    if isinstance(raw, dict):
                        for key in DEFAULTS:
                            if key in raw:
                                self._data[key] = raw[key]
                except (OSError, json.JSONDecodeError):
                    self._data = deepcopy(DEFAULTS)
            self._sanitize()
            self._dirty = False

    def save(self, force: bool = True) -> None:
        with self._lock:
            if not force and not self._dirty:
                return
            self._sanitize()
            payload = json.dumps(self._data, indent=2, ensure_ascii=False) + "\n"
            self._dirty = False
            self._last_save = time.monotonic()
        try:
            CONFIG_PATH.write_text(payload, encoding="utf-8")
        except OSError:
            pass

    def flush_if_due(self) -> None:
        with self._lock:
            if not self._dirty:
                return
            if time.monotonic() - self._last_save < self._save_delay:
                return
        self.save(force=True)

    def _sanitize(self) -> None:
        self._data["scale"] = float(max(0.4, min(2.5, float(self._data["scale"]))))
        self._data["offset_x"] = int(round(float(self._data["offset_x"])))
        self._data["offset_y"] = int(round(float(self._data["offset_y"])))
        self._data["opacity"] = float(max(0.15, min(1.0, float(self._data["opacity"]))))
        if self._data["weapon"] not in WEAPONS:
            self._data["weapon"] = "rifle"
        if self._data["hands"] not in HANDS:
            self._data["hands"] = "tactical"
        self._data["fire_rate_ms"] = int(max(40, min(600, int(self._data["fire_rate_ms"]))))
        self._data["shot_volume"] = float(max(0.0, min(1.0, float(self._data["shot_volume"]))))
        self._data["shell_volume"] = float(max(0.0, min(1.0, float(self._data["shell_volume"]))))
        self._data["custom_weapon_scale"] = float(
            max(0.2, min(3.0, float(self._data["custom_weapon_scale"])))
        )
        self._data["custom_gloves_scale"] = float(
            max(0.2, min(3.0, float(self._data["custom_gloves_scale"])))
        )
        self._data["shot_sound"] = str(self._data.get("shot_sound") or "")
        self._data["shell_sound"] = str(self._data.get("shell_sound") or "")
        self._data["custom_weapon"] = str(self._data.get("custom_weapon") or "")
        self._data["custom_gloves"] = str(self._data.get("custom_gloves") or "")
        for flag in (
            "muzzle_flash",
            "tracer",
            "impact",
            "recoil",
            "shell_eject",
            "sound",
            "always_on_top",
            "click_through_idle",
            "use_custom_weapon",
            "use_custom_gloves",
        ):
            self._data[flag] = bool(self._data[flag])

    def get(self, key: str) -> Any:
        with self._lock:
            return self._data[key]

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)

    def update(self, *, immediate_save: bool = False, **kwargs: Any) -> None:
        listeners: list[Callable[[dict[str, Any]], None]] = []
        snapshot: dict[str, Any] | None = None
        with self._lock:
            changed = False
            for key, value in kwargs.items():
                if key in DEFAULTS and self._data.get(key) != value:
                    self._data[key] = value
                    changed = True
            if not changed:
                return
            self._sanitize()
            self._dirty = True
            snapshot = deepcopy(self._data)
            listeners = list(self._listeners)

        if immediate_save:
            self.save(force=True)
        else:
            with self._lock:
                if self._last_save == 0:
                    self._last_save = time.monotonic()

        for listener in listeners:
            try:
                listener(snapshot)  # type: ignore[arg-type]
            except Exception:
                pass

    def on_change(self, callback: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            self._listeners.append(callback)
