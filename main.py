"""
CorporateDroneAIM — FPV weapon hands overlay.

LMB: shoot toward cursor
F1: settings
F2: next weapon
Esc: quit
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.assets import ensure_asset_dirs
from src.config import Config, app_dir
from src.overlay import OverlayApp
from src.settings_ui import SettingsWindow


def _show_error(msg: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, msg, "CorporateDroneAIM", 0x10)
    except Exception:
        print(msg, file=sys.stderr)


def main() -> int:
    try:
        ensure_asset_dirs()
        config = Config()
        overlay_holder: dict[str, OverlayApp | None] = {"app": None}

        def request_quit() -> None:
            app = overlay_holder["app"]
            if app is not None:
                app.stop()

        # Tk on its own thread so window drag never blocks pygame.
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
    except Exception:
        log = app_dir() / "crash.log"
        tb = traceback.format_exc()
        try:
            log.write_text(tb, encoding="utf-8")
        except OSError:
            pass
        _show_error(f"Ошибка запуска.\n\n{tb[-1500:]}\n\nПодробности: {log}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
