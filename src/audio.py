from __future__ import annotations

import time
from pathlib import Path

import pygame

from .assets import sound_path


class SoundManager:
    def __init__(self) -> None:
        self._ok = False
        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._shot_name = ""
        self._shell_name = ""
        self._shot_vol = 0.7
        self._shell_vol = 0.5
        self._enabled = True
        self._shell_queue: list[float] = []
        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
            self._ok = True
        except pygame.error:
            self._ok = False

    def configure(self, cfg: dict) -> None:
        self._enabled = bool(cfg.get("sound", True))
        self._shot_name = str(cfg.get("shot_sound", "") or "")
        self._shell_name = str(cfg.get("shell_sound", "") or "")
        self._shot_vol = float(max(0.0, min(1.0, cfg.get("shot_volume", 0.7))))
        self._shell_vol = float(max(0.0, min(1.0, cfg.get("shell_volume", 0.5))))

    def _load(self, name: str) -> pygame.mixer.Sound | None:
        if not self._ok or not name:
            return None
        if name in self._cache:
            return self._cache[name]
        path = sound_path(name)
        if path is None:
            return None
        try:
            snd = pygame.mixer.Sound(str(path))
            self._cache[name] = snd
            return snd
        except pygame.error:
            return None

    def play_shot(self) -> None:
        if not self._enabled:
            return
        snd = self._load(self._shot_name)
        if snd is None:
            return
        ch = snd.play()
        if ch is not None:
            ch.set_volume(self._shot_vol)

    def queue_shell_drop(self, delay: float = 0.32) -> None:
        if not self._enabled or not self._shell_name:
            return
        self._shell_queue.append(time.monotonic() + max(0.05, delay))

    def update(self) -> None:
        if not self._enabled or not self._shell_queue:
            return
        now = time.monotonic()
        keep: list[float] = []
        for t in self._shell_queue:
            if t <= now:
                self._play_shell()
            else:
                keep.append(t)
        self._shell_queue = keep

    def _play_shell(self) -> None:
        snd = self._load(self._shell_name)
        if snd is None:
            return
        ch = snd.play()
        if ch is not None:
            ch.set_volume(self._shell_vol)

    def preload(self, *names: str) -> None:
        for name in names:
            if name:
                self._load(name)

    def clear_cache(self) -> None:
        self._cache.clear()
