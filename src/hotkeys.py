from __future__ import annotations

import threading
from collections import deque
from typing import Callable


class GlobalHotkeys:
    """Thread-safe global hotkey listener using keyboard module."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queue: deque[str] = deque()
        self._running = False
        self._pressed_keys: set = set()

    def start(self) -> None:
        if self._running:
            return
        try:
            import keyboard
        except ImportError:
            return

        # Combos that don't steal common single keys from games/apps
        combos = {
            "ctrl+shift+s": "settings",
            "ctrl+shift+q": "quit",
            "ctrl+shift+h": "toggle_help",
            "ctrl+shift+w": "next_weapon",
        }

        def make_handler(action: str) -> Callable[[], None]:
            def _handler() -> None:
                with self._lock:
                    self._queue.append(action)
            return _handler

        for combo, action in combos.items():
            keyboard.add_hotkey(combo, make_handler(action), suppress=False)

        self._running = True

    def stop(self) -> None:
        if not self._running:
            return
        try:
            import keyboard
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self._running = False

    def poll(self) -> list[str]:
        with self._lock:
            if not self._queue:
                return []
            items = list(self._queue)
            self._queue.clear()
            return items
