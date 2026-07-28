from __future__ import annotations

import sys
import threading
import time
from typing import Callable

import pygame

from .audio import SoundManager
from .config import Config
from .display_info import Monitor, list_monitors, monitor_from_point
from .effects import EffectSystem
from .weapons import WeaponPose, compute_weapon_pose, draw_weapon_view

COLOR_KEY = (255, 0, 255)


def win32api_colorref(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return r | (g << 8) | (b << 16)


def _apply_windows_overlay(
    hwnd: int,
    opacity: float,
    topmost: bool,
    click_through: bool,
    rect: tuple[int, int, int, int] | None = None,
) -> None:
    if sys.platform != "win32":
        return
    try:
        import win32con
        import win32gui
    except ImportError:
        return

    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW
    if click_through:
        ex_style |= win32con.WS_EX_TRANSPARENT
    else:
        ex_style &= ~win32con.WS_EX_TRANSPARENT
    ex_style |= win32con.WS_EX_NOACTIVATE
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    alpha = int(max(0, min(255, round(opacity * 255))))
    win32gui.SetLayeredWindowAttributes(
        hwnd,
        win32api_colorref(COLOR_KEY),
        alpha,
        win32con.LWA_COLORKEY | win32con.LWA_ALPHA,
    )

    flags = win32con.SWP_NOACTIVATE
    if rect is None:
        flags |= win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        x = y = w = h = 0
    else:
        x, y, w, h = rect

    flag = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(hwnd, flag, int(x), int(y), int(w), int(h), flags)


class OverlayApp:
    def __init__(self, config: Config, on_open_settings: Callable[[], None] | None = None) -> None:
        self.config = config
        self.on_open_settings = on_open_settings
        self.effects = EffectSystem()
        self.audio: SoundManager | None = None
        self._running = False
        self._last_shot = 0.0
        self._global_buttons = {1: False}
        self._listener = None
        self.screen: pygame.Surface | None = None
        self._hwnd = 0
        self._clock = pygame.time.Clock()
        self._pose: WeaponPose | None = None
        self._aim_angle: float | None = None
        self._style_dirty = threading.Event()
        self._style_dirty.set()
        self._applied_opacity: float | None = None
        self._applied_topmost: bool | None = None
        self._monitor: Monitor | None = None
        self._monitors_cache: list[Monitor] = []
        self._monitors_refresh_at = 0.0

    def _start_mouse_hook(self) -> None:
        try:
            from pynput import mouse
        except ImportError:
            return

        def on_click(x, y, button, pressed):
            try:
                from pynput.mouse import Button

                if button == Button.left:
                    self._global_buttons[1] = pressed
            except Exception:
                pass

        self._listener = mouse.Listener(on_click=on_click)
        self._listener.daemon = True
        self._listener.start()

    def _stop_mouse_hook(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _refresh_monitors(self, force: bool = False) -> list[Monitor]:
        now = time.monotonic()
        if force or now >= self._monitors_refresh_at or not self._monitors_cache:
            self._monitors_cache = list_monitors()
            self._monitors_refresh_at = now + 2.0
        return self._monitors_cache

    def _create_window(self, monitor: Monitor) -> None:
        pygame.display.set_caption("CorporateDroneAIM Overlay")
        # Place window on target monitor before/after mode set
        if sys.platform == "win32":
            import os

            os.environ["SDL_VIDEO_WINDOW_POS"] = f"{monitor.x},{monitor.y}"

        flags = pygame.NOFRAME | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((monitor.width, monitor.height), flags)
        wm = pygame.display.get_wm_info()
        self._hwnd = int(wm.get("window", 0) or 0)
        self._monitor = monitor
        self._apply_window_style(force=True, move_rect=monitor)
        self._aim_angle = None
        self.effects.clear()

    def _switch_monitor(self, monitor: Monitor) -> None:
        if self._monitor is not None and self._monitor.key() == monitor.key():
            return
        # Resize surface if needed; always re-position via Win32
        if self.screen is None or self.screen.get_size() != (monitor.width, monitor.height):
            flags = pygame.NOFRAME | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode((monitor.width, monitor.height), flags)
            wm = pygame.display.get_wm_info()
            self._hwnd = int(wm.get("window", 0) or 0)
        self._monitor = monitor
        self._apply_window_style(force=True, move_rect=monitor)
        self._aim_angle = None
        self.effects.clear()

    def _on_config_changed(self, _data: dict) -> None:
        self._style_dirty.set()

    def _apply_window_style(self, force: bool = False, move_rect: Monitor | None = None) -> None:
        if not self._hwnd:
            return
        cfg = self.config.as_dict()
        opacity = float(cfg["opacity"])
        topmost = bool(cfg["always_on_top"])
        mon = move_rect or self._monitor
        need_move = move_rect is not None
        if (
            not force
            and not need_move
            and self._applied_opacity == opacity
            and self._applied_topmost == topmost
        ):
            self._style_dirty.clear()
            return

        rect = None
        if mon is not None:
            rect = (mon.x, mon.y, mon.width, mon.height)

        _apply_windows_overlay(
            self._hwnd,
            opacity=opacity,
            topmost=topmost,
            click_through=True,
            rect=rect,
        )
        self._applied_opacity = opacity
        self._applied_topmost = topmost
        self._style_dirty.clear()

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.font.init()
        self.audio = SoundManager()

        mons = self._refresh_monitors(force=True)
        cx, cy = self._cursor_pos_abs()
        start = monitor_from_point(cx, cy, mons)
        self._create_window(start)
        self._start_mouse_hook()
        self.config.on_change(self._on_config_changed)
        cfg0 = self.config.as_dict()
        self.audio.configure(cfg0)
        self.audio.preload(str(cfg0.get("shot_sound") or ""), str(cfg0.get("shell_sound") or ""))

        font = pygame.font.SysFont("consolas", 16)
        self._running = True
        hint_until = time.time() + 5.0

        while self._running:
            dt = self._clock.tick(60) / 1000.0
            self.config.flush_if_due()
            if self._style_dirty.is_set():
                self._apply_window_style()

            cfg = self.config.as_dict()
            if self.audio is not None:
                self.audio.configure(cfg)
                self.audio.update()

            mons = self._refresh_monitors()
            cursor_abs = self._cursor_pos_abs()
            mon = monitor_from_point(cursor_abs[0], cursor_abs[1], mons)
            if self._monitor is None or mon.key() != self._monitor.key():
                self._switch_monitor(mon)

            assert self._monitor is not None
            cursor_local = self._monitor.to_local(*cursor_abs)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._running = False
                    elif event.key == pygame.K_F1 and self.on_open_settings:
                        self.on_open_settings()
                    elif event.key == pygame.K_F2:
                        from .config import WEAPONS

                        cur = cfg["weapon"]
                        idx = WEAPONS.index(cur) if cur in WEAPONS else 0
                        self.config.update(
                            immediate_save=True,
                            weapon=WEAPONS[(idx + 1) % len(WEAPONS)],
                        )

            self._pose = compute_weapon_pose(
                screen_size=self.screen.get_size() if self.screen else (mon.width, mon.height),
                weapon_id=cfg["weapon"],
                hands_id=cfg["hands"],
                scale=float(cfg["scale"]),
                offset=(float(cfg["offset_x"]), float(cfg["offset_y"])),
                recoil=self.effects.recoil_offset,
                cursor=cursor_local,
                current_angle=self._aim_angle,
                dt=dt,
                use_custom_weapon=bool(cfg.get("use_custom_weapon")),
                custom_weapon=str(cfg.get("custom_weapon") or ""),
                custom_weapon_scale=float(cfg.get("custom_weapon_scale", 1.0)),
                use_custom_gloves=bool(cfg.get("use_custom_gloves")),
                custom_gloves=str(cfg.get("custom_gloves") or ""),
                custom_gloves_scale=float(cfg.get("custom_gloves_scale", 1.0)),
            )
            self._aim_angle = self._pose.angle

            pressed = bool(self._global_buttons.get(1))
            if not self._listener:
                pressed = pygame.mouse.get_pressed()[0]

            now = time.time()
            if pressed:
                rate = max(0.04, cfg["fire_rate_ms"] / 1000.0)
                if now - self._last_shot >= rate:
                    self._fire(cfg, cursor_local)
                    self._last_shot = now

            self.effects.update(dt)
            self._draw_frame(cfg, font, hint_until, cursor_local)

        self.config.save(force=True)
        self._stop_mouse_hook()
        pygame.quit()

    def _cursor_pos_abs(self) -> tuple[int, int]:
        if sys.platform == "win32":
            try:
                import win32api

                return win32api.GetCursorPos()
            except Exception:
                pass
        if self.screen and self._monitor:
            lx, ly = pygame.mouse.get_pos()
            return self._monitor.x + lx, self._monitor.y + ly
        return pygame.mouse.get_pos()

    def _fire(self, cfg: dict, cursor_local: tuple[int, int]) -> None:
        if not self.screen or self._pose is None:
            return
        self.effects.shoot(
            (self._pose.muzzle_x, self._pose.muzzle_y),
            cursor_local,
            cfg["weapon"],
            muzzle_flash=cfg["muzzle_flash"],
            tracer=cfg["tracer"],
            impact=cfg["impact"],
            recoil=cfg["recoil"],
            shell_eject=cfg["shell_eject"],
            barrel_angle=self._pose.angle,
        )
        if self.audio is not None:
            self.audio.play_shot()
            if cfg.get("shell_eject"):
                self.audio.queue_shell_drop(delay=0.30)

    def _draw_frame(
        self,
        cfg: dict,
        font: pygame.font.Font,
        hint_until: float,
        cursor_local: tuple[int, int],
    ) -> None:
        assert self.screen is not None
        assert self._pose is not None
        self.screen.fill(COLOR_KEY)

        draw_weapon_view(self.screen, self._pose)
        self.effects.draw(self.screen)

        cx, cy = cursor_local
        if cfg["impact"]:
            layer = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(layer, (255, 255, 255, 40), (10, 10), 6, 1)
            self.screen.blit(layer, (cx - 10, cy - 10))

        if time.time() < hint_until:
            mon = self._monitor
            mon_txt = f"{mon.width}x{mon.height} @ {mon.x},{mon.y}" if mon else "?"
            text = font.render(
                f"CorporateDroneAIM  |  LMB  |  F1  |  F2  |  Esc  |  {mon_txt}",
                True,
                (230, 230, 230),
            )
            bg = pygame.Surface((text.get_width() + 12, text.get_height() + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            self.screen.blit(bg, (12, 12))
            self.screen.blit(text, (18, 16))

        pygame.display.flip()
