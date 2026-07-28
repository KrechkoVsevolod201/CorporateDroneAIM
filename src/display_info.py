from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Monitor:
    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px < self.right and self.y <= py < self.bottom

    def to_local(self, px: int, py: int) -> tuple[int, int]:
        return px - self.x, py - self.y

    def key(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height


def list_monitors() -> list[Monitor]:
    if sys.platform == "win32":
        try:
            return _list_monitors_win32()
        except Exception:
            pass
    return [Monitor(0, 0, 1920, 1080, True)]


def _list_monitors_win32() -> list[Monitor]:
    import win32api
    import win32con

    mons: list[Monitor] = []
    for hmonitor, _hdc, _rect in win32api.EnumDisplayMonitors(None, None):
        info = win32api.GetMonitorInfo(hmonitor)
        l, t, r, b = info["Monitor"]
        primary = bool(info.get("Flags", 0) & win32con.MONITORINFOF_PRIMARY)
        mons.append(Monitor(int(l), int(t), int(r - l), int(b - t), primary))

    if not mons:
        w = int(win32api.GetSystemMetrics(0))
        h = int(win32api.GetSystemMetrics(1))
        mons.append(Monitor(0, 0, w, h, True))
    return mons


def monitor_from_point(px: int, py: int, monitors: list[Monitor] | None = None) -> Monitor:
    mons = monitors if monitors is not None else list_monitors()
    for m in mons:
        if m.contains(px, py):
            return m
    best = mons[0]
    best_d = float("inf")
    for m in mons:
        cx = m.x + m.width * 0.5
        cy = m.y + m.height * 0.5
        d = (cx - px) ** 2 + (cy - py) ** 2
        if d < best_d:
            best_d = d
            best = m
    return best


def primary_monitor(monitors: list[Monitor] | None = None) -> Monitor:
    mons = monitors if monitors is not None else list_monitors()
    for m in mons:
        if m.is_primary:
            return m
    return mons[0]
