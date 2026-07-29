from __future__ import annotations

import time

import pygame

from .assets import shot_sound_path, shell_sound_path


class SoundManager:
    """One-shot / shell audio with anti-double-play guards."""

    SHOT_CHANNEL = 0
    SHELL_CHANNEL = 1

    def __init__(self) -> None:
        self._ok = False
        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._shot_name = ""
        self._shell_name = ""
        self._shot_vol = 0.7
        self._shell_vol = 0.5
        self._enabled = True
        self._shell_queue: list[float] = []
        self._last_shot_time = 0.0
        self._min_shot_interval = 0.05  # 50ms minimum between shots
        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
            # Keep a small fixed pool; channel 0/1 reserved for shot/shell
            pygame.mixer.set_num_channels(16)
            self._ok = True
        except pygame.error:
            self._ok = False

    def configure(self, cfg: dict) -> None:
        self._enabled = bool(cfg.get("sound", True))
        new_shot = str(cfg.get("shot_sound", "") or "")
        new_shell = str(cfg.get("shell_sound", "") or "")
        if new_shot != self._shot_name:
            self._cache.pop(self._shot_name, None)
            self._shot_name = new_shot
        if new_shell != self._shell_name:
            self._cache.pop(self._shell_name, None)
            self._shell_name = new_shell
        self._shot_vol = float(max(0.0, min(1.0, cfg.get("shot_volume", 0.7))))
        self._shell_vol = float(max(0.0, min(1.0, cfg.get("shell_volume", 0.5))))

    def _load(self, name: str, kind: str = "shot") -> pygame.mixer.Sound | None:
        if not self._ok or not name:
            return None
        cached = self._cache.get(name)
        if cached is not None:
            return cached
        path = shot_sound_path(name) if kind == "shot" else shell_sound_path(name)
        if path is None:
            return None
        try:
            # Resolve once; never load the same logical name from two places
            snd = pygame.mixer.Sound(str(path.resolve()))
            self._cache[name] = snd
            return snd
        except (pygame.error, OSError):
            return None

    def play_shot(self) -> None:
        if not self._enabled or not self._ok:
            return
        
        # Anti-double-play: enforce minimum interval
        now = time.monotonic()
        if now - self._last_shot_time < self._min_shot_interval:
            return
        
        snd = self._load(self._shot_name, kind="shot")
        if snd is None:
            return
        
        try:
            ch = pygame.mixer.Channel(self.SHOT_CHANNEL)
            # Stop previous shot on same channel so it can't layer/double
            ch.stop()
            snd.set_volume(self._shot_vol)
            ch.play(snd, loops=0)
            self._last_shot_time = now
        except pygame.error:
            pass

    def queue_shell_drop(self, delay: float = 0.32) -> None:
        if not self._enabled or not self._shell_name or not self._ok:
            return
        # Don't stack dozens of shell queues while holding fire
        if len(self._shell_queue) >= 6:
            return
        self._shell_queue.append(time.monotonic() + max(0.05, delay))

    def update(self) -> None:
        if not self._enabled or not self._shell_queue:
            return
        now = time.monotonic()
        keep: list[float] = []
        played = False
        for t in self._shell_queue:
            if t <= now and not played:
                self._play_shell()
                played = True
            elif t > now:
                keep.append(t)
        self._shell_queue = keep

    def _play_shell(self) -> None:
        snd = self._load(self._shell_name, kind="shell")
        if snd is None:
            return
        try:
            ch = pygame.mixer.Channel(self.SHELL_CHANNEL)
            ch.stop()
            snd.set_volume(self._shell_vol)
            ch.play(snd, loops=0)
        except pygame.error:
            pass

    def preload(self, *names: str) -> None:
        for name in names:
            if name:
                self._load(name)

    def clear_cache(self) -> None:
        self._cache.clear()
