"""
CorporateDroneAIM — FPV weapon hands overlay.

LMB: shoot toward cursor
F1: settings
F2: next weapon
Esc: quit
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import Config
from src.overlay import OverlayApp
from src.settings_ui import SettingsWindow


def main() -> int:
    config = Config()
    overlay_holder: dict[str, OverlayApp | None] = {"app": None}

    def request_quit() -> None:
        app = overlay_holder["app"]
        if app is not None:
            app.stop()

    # Tk lives on its own thread/mainloop so window drag never blocks pygame.
    settings = SettingsWindow(config, on_quit=request_quit)
    settings.show()

    overlay = OverlayApp(config, on_open_settings=settings.show)
    overlay_holder["app"] = overlay

    try:
        overlay.run()
    finally:
        config.save(force=True)
        settings.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
