from __future__ import annotations

import pygame


def draw_crosshair(
    surface: pygame.Surface,
    pos: tuple[int, int],
    *,
    enabled: bool = True,
    style: str = "cross",
    size: float = 14,
    thickness: float = 2,
    gap: float = 4,
    opacity: float = 0.85,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    if not enabled:
        return
    cx, cy = int(pos[0]), int(pos[1])
    alpha = int(max(0, min(255, round(opacity * 255))))
    col = (*color, alpha)
    s = max(2, int(size))
    th = max(1, int(thickness))
    g = max(0, int(gap))
    layer = pygame.Surface((s * 2 + 8, s * 2 + 8), pygame.SRCALPHA)
    ox, oy = s + 4, s + 4

    if style == "dot":
        pygame.draw.circle(layer, col, (ox, oy), max(1, th + 1))
    elif style == "circle":
        pygame.draw.circle(layer, col, (ox, oy), s, th)
        if g <= 2:
            pygame.draw.circle(layer, col, (ox, oy), max(1, th))
    elif style == "t":
        pygame.draw.line(layer, col, (ox - s, oy), (ox + s, oy), th)
        pygame.draw.line(layer, col, (ox, oy), (ox, oy + s), th)
    elif style == "crossdot":
        pygame.draw.line(layer, col, (ox - s, oy), (ox - g, oy), th)
        pygame.draw.line(layer, col, (ox + g, oy), (ox + s, oy), th)
        pygame.draw.line(layer, col, (ox, oy - s), (ox, oy - g), th)
        pygame.draw.line(layer, col, (ox, oy + g), (ox, oy + s), th)
        pygame.draw.circle(layer, col, (ox, oy), max(1, th))
    else:  # cross
        pygame.draw.line(layer, col, (ox - s, oy), (ox - g, oy), th)
        pygame.draw.line(layer, col, (ox + g, oy), (ox + s, oy), th)
        pygame.draw.line(layer, col, (ox, oy - s), (ox, oy - g), th)
        pygame.draw.line(layer, col, (ox, oy + g), (ox, oy + s), th)

    surface.blit(layer, (cx - ox, cy - oy))
