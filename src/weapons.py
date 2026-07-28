from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pygame

from .assets import glove_image_path, weapon_image_path


HAND_PALETTES = {
    "tactical": {
        "skin": (210, 170, 130),
        "skin_shade": (170, 130, 95),
        "glove": (45, 48, 42),
        "glove_hi": (70, 75, 65),
        "sleeve": (35, 40, 38),
        "accent": (90, 110, 70),
    },
    "bare": {
        "skin": (232, 190, 150),
        "skin_shade": (200, 155, 115),
        "glove": (232, 190, 150),
        "glove_hi": (245, 210, 175),
        "sleeve": (55, 70, 120),
        "accent": (200, 60, 60),
    },
    "gloves": {
        "skin": (200, 160, 120),
        "skin_shade": (160, 120, 90),
        "glove": (25, 25, 28),
        "glove_hi": (55, 55, 60),
        "sleeve": (20, 20, 22),
        "accent": (180, 40, 40),
    },
    "cyber": {
        "skin": (170, 200, 210),
        "skin_shade": (120, 150, 165),
        "glove": (20, 30, 45),
        "glove_hi": (40, 90, 120),
        "sleeve": (15, 20, 30),
        "accent": (0, 220, 255),
    },
}


@dataclass(frozen=True)
class WeaponProfile:
    name: str
    length: float
    barrel_w: float
    body_w: float
    body_h: float
    magazine: bool
    stock: bool
    scope: bool
    color_body: tuple[int, int, int]
    color_metal: tuple[int, int, int]
    color_accent: tuple[int, int, int]
    muzzle_size: float
    recoil_kick: float
    tracer_width: float
    pellets: int = 1


PROFILES: dict[str, WeaponProfile] = {
    "pistol": WeaponProfile(
        name="pistol",
        length=170,
        barrel_w=18,
        body_w=70,
        body_h=42,
        magazine=True,
        stock=False,
        scope=False,
        color_body=(40, 42, 48),
        color_metal=(120, 125, 135),
        color_accent=(90, 95, 105),
        muzzle_size=1.0,
        recoil_kick=10.0,
        tracer_width=2.0,
    ),
    "rifle": WeaponProfile(
        name="rifle",
        length=320,
        barrel_w=16,
        body_w=140,
        body_h=38,
        magazine=True,
        stock=True,
        scope=True,
        color_body=(48, 52, 45),
        color_metal=(95, 100, 105),
        color_accent=(70, 85, 55),
        muzzle_size=1.15,
        recoil_kick=14.0,
        tracer_width=2.5,
    ),
    "smg": WeaponProfile(
        name="smg",
        length=240,
        barrel_w=14,
        body_w=110,
        body_h=36,
        magazine=True,
        stock=True,
        scope=False,
        color_body=(35, 38, 42),
        color_metal=(110, 115, 120),
        color_accent=(80, 80, 90),
        muzzle_size=0.9,
        recoil_kick=7.0,
        tracer_width=2.0,
    ),
    "shotgun": WeaponProfile(
        name="shotgun",
        length=300,
        barrel_w=22,
        body_w=130,
        body_h=40,
        magazine=False,
        stock=True,
        scope=False,
        color_body=(70, 45, 30),
        color_metal=(90, 90, 95),
        color_accent=(120, 80, 40),
        muzzle_size=1.5,
        recoil_kick=22.0,
        tracer_width=3.5,
        pellets=6,
    ),
    "sniper": WeaponProfile(
        name="sniper",
        length=360,
        barrel_w=14,
        body_w=150,
        body_h=34,
        magazine=True,
        stock=True,
        scope=True,
        color_body=(30, 40, 35),
        color_metal=(80, 85, 90),
        color_accent=(50, 90, 70),
        muzzle_size=1.2,
        recoil_kick=26.0,
        tracer_width=2.0,
    ),
}


@dataclass
class WeaponPose:
    base_x: float
    base_y: float
    angle: float
    scale: float
    muzzle_x: float
    muzzle_y: float
    weapon_id: str
    hands_id: str
    recoil_x: float
    recoil_y: float
    use_custom_weapon: bool = False
    custom_weapon: str = ""
    custom_weapon_scale: float = 1.0
    use_custom_gloves: bool = False
    custom_gloves: str = ""
    custom_gloves_scale: float = 1.0


_IMAGE_CACHE: dict[str, pygame.Surface] = {}


def clear_image_cache() -> None:
    _IMAGE_CACHE.clear()


def _load_image(path: Path) -> pygame.Surface | None:
    key = str(path.resolve())
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]
    try:
        img = pygame.image.load(str(path)).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        return None
    _IMAGE_CACHE[key] = img
    return img


def _blit_rotated(
    surface: pygame.Surface,
    image: pygame.Surface,
    pivot: tuple[float, float],
    angle: float,
    scale: float,
    origin: tuple[float, float],
) -> None:
    """Blit image rotated around origin in image space; origin maps to pivot on screen.

    Image local +X (right) aligns with barrel forward (math angle).
    """
    w, h = image.get_size()
    sw = max(1, int(round(w * scale)))
    sh = max(1, int(round(h * scale)))
    if sw != w or sh != h:
        scaled = pygame.transform.smoothscale(image, (sw, sh))
    else:
        scaled = image

    ox = origin[0] * scale
    oy = origin[1] * scale
    # pygame positive rotation = CCW; screen y-down math angle needs negation
    deg = -math.degrees(angle)
    rotated = pygame.transform.rotate(scaled, deg)
    rw, rh = rotated.get_size()

    # vector from image origin to center, then rotate
    cx = sw * 0.5
    cy = sh * 0.5
    dx = cx - ox
    dy = cy - oy
    ca, sa = math.cos(angle), math.sin(angle)
    # screen rotation matches our tf(): (x',y') = (x ca - y sa, x sa + y ca)
    rdx = dx * ca - dy * sa
    rdy = dx * sa + dy * ca
    blit_x = pivot[0] + rdx - rw * 0.5
    blit_y = pivot[1] + rdy - rh * 0.5
    surface.blit(rotated, (int(blit_x), int(blit_y)))


def _poly(surface: pygame.Surface, color: tuple[int, int, int], points: list[tuple[float, float]]) -> None:
    if len(points) >= 3:
        pygame.draw.polygon(surface, color, [(int(x), int(y)) for x, y in points])


def _angle_to(x0: float, y0: float, x1: float, y1: float) -> float:
    return math.atan2(y1 - y0, x1 - x0)


def _shortest_angle_delta(current: float, target: float) -> float:
    return (target - current + math.pi) % (math.tau) - math.pi


def smooth_angle(current: float | None, target: float, dt: float, speed: float = 18.0) -> float:
    if current is None:
        return target
    delta = _shortest_angle_delta(current, target)
    t = 1.0 - math.exp(-speed * max(0.0, dt))
    return current + delta * t


def compute_weapon_pose(
    screen_size: tuple[int, int],
    weapon_id: str,
    hands_id: str,
    scale: float,
    offset: tuple[float, float],
    recoil: tuple[float, float],
    cursor: tuple[float, float],
    current_angle: float | None = None,
    dt: float = 1.0 / 60.0,
    *,
    use_custom_weapon: bool = False,
    custom_weapon: str = "",
    custom_weapon_scale: float = 1.0,
    use_custom_gloves: bool = False,
    custom_gloves: str = "",
    custom_gloves_scale: float = 1.0,
) -> WeaponPose:
    """Pivot at grip; barrel +X aims at cursor. Muzzle lies on that ray."""
    w, h = screen_size
    profile = PROFILES.get(weapon_id, PROFILES["rifle"])
    ox, oy = offset
    rx, ry = recoil
    s = max(0.05, float(scale))

    base_x = w * 0.62 + ox + rx
    base_y = h * 0.93 + oy + ry

    cx, cy = cursor
    target = _angle_to(base_x, base_y, cx, cy)

    min_a = -math.pi + 0.08
    max_a = -0.02
    if cy >= base_y:
        target = min_a if cx < base_x else max_a
    else:
        target = max(min_a, min(max_a, target))

    angle = smooth_angle(current_angle, target, dt, speed=22.0)

    muzzle_local_x = _muzzle_distance(
        profile, s, use_custom_weapon, custom_weapon, custom_weapon_scale
    )
    ca, sa = math.cos(angle), math.sin(angle)
    muzzle_x = base_x + muzzle_local_x * ca
    muzzle_y = base_y + muzzle_local_x * sa

    return WeaponPose(
        base_x=base_x,
        base_y=base_y,
        angle=angle,
        scale=s,
        muzzle_x=muzzle_x,
        muzzle_y=muzzle_y,
        weapon_id=weapon_id,
        hands_id=hands_id,
        recoil_x=rx,
        recoil_y=ry,
        use_custom_weapon=use_custom_weapon,
        custom_weapon=custom_weapon,
        custom_weapon_scale=custom_weapon_scale,
        use_custom_gloves=use_custom_gloves,
        custom_gloves=custom_gloves,
        custom_gloves_scale=custom_gloves_scale,
    )


def _muzzle_distance(
    profile: WeaponProfile,
    scale: float,
    use_custom: bool,
    custom_name: str,
    custom_scale: float,
) -> float:
    if use_custom and custom_name:
        path = weapon_image_path(custom_name)
        if path is not None:
            img = _load_image(path)
            if img is not None:
                # pivot ~25% width, muzzle ~ right edge
                w = img.get_width()
                return max(40.0, (w * 0.75) * scale * custom_scale)
    return (profile.length - 40 + 24) * scale


def draw_weapon_view(surface: pygame.Surface, pose: WeaponPose) -> None:
    """Draw FPV hands + weapon using a precomputed pose."""
    custom_w = None
    if pose.use_custom_weapon and pose.custom_weapon:
        path = weapon_image_path(pose.custom_weapon)
        if path is not None:
            custom_w = _load_image(path)

    custom_g = None
    if pose.use_custom_gloves and pose.custom_gloves:
        path = glove_image_path(pose.custom_gloves)
        if path is not None:
            custom_g = _load_image(path)

    if custom_w is None and custom_g is None:
        _draw_procedural_full(surface, pose)
        return

    if custom_w is not None and custom_g is None:
        _draw_procedural_hands_only(surface, pose)
        _blit_custom_weapon(surface, pose, custom_w)
        return

    if custom_w is None and custom_g is not None:
        _draw_procedural_full(surface, pose)
        _blit_custom_gloves(surface, pose, custom_g)
        return

    # both custom
    _blit_custom_gloves(surface, pose, custom_g)
    _blit_custom_weapon(surface, pose, custom_w)


def _blit_custom_gloves(surface: pygame.Surface, pose: WeaponPose, gloves_img: pygame.Surface) -> None:
    gw, gh = gloves_img.get_size()
    g_scale = pose.scale * pose.custom_gloves_scale * 0.55
    _blit_rotated(
        surface,
        gloves_img,
        pivot=(pose.base_x, pose.base_y),
        angle=pose.angle,
        scale=g_scale,
        origin=(gw * 0.45, gh * 0.55),
    )


def _blit_custom_weapon(surface: pygame.Surface, pose: WeaponPose, weapon_img: pygame.Surface) -> None:
    ww, wh = weapon_img.get_size()
    w_scale = pose.scale * pose.custom_weapon_scale * 0.85
    # Convention: barrel points RIGHT; pivot near grip (left-lower)
    _blit_rotated(
        surface,
        weapon_img,
        pivot=(pose.base_x, pose.base_y),
        angle=pose.angle,
        scale=w_scale,
        origin=(ww * 0.22, wh * 0.62),
    )


def _draw_procedural_hands_only(surface: pygame.Surface, pose: WeaponPose) -> None:
    profile = PROFILES.get(pose.weapon_id, PROFILES["rifle"])
    palette = HAND_PALETTES.get(pose.hands_id, HAND_PALETTES["tactical"])
    s = pose.scale
    ang = pose.angle
    ca, sa = math.cos(ang), math.sin(ang)
    base_x, base_y = pose.base_x, pose.base_y
    bw, bh = profile.body_w, profile.body_h

    def tf(px: float, py: float) -> tuple[float, float]:
        lx, ly = px * s, py * s
        return base_x + lx * ca - ly * sa, base_y + lx * sa + ly * ca

    _poly(
        surface,
        palette["sleeve"],
        [tf(-20, 40), tf(40, 55), tf(70, 120), tf(-10, 130), tf(-40, 90)],
    )
    _poly(
        surface,
        palette["glove"],
        [tf(10, 20), tf(55, 30), tf(75, 70), tf(35, 85), tf(5, 55)],
    )
    _poly(
        surface,
        palette["glove"],
        [tf(18, bh * 0.35), tf(48, bh * 0.3), tf(40, bh * 0.9), tf(14, bh * 0.95)],
    )
    _poly(
        surface,
        palette["sleeve"],
        [tf(bw * 0.55, bh * 0.5), tf(bw * 0.9, bh * 0.35), tf(bw * 1.05, bh * 1.1), tf(bw * 0.45, bh * 1.2)],
    )
    _poly(
        surface,
        palette["glove"],
        [
            tf(bw * 0.6, bh * 0.05),
            tf(bw * 0.95, -bh * 0.05),
            tf(bw * 1.05, bh * 0.45),
            tf(bw * 0.7, bh * 0.55),
            tf(bw * 0.55, bh * 0.35),
        ],
    )


def _draw_procedural_full(surface: pygame.Surface, pose: WeaponPose) -> None:
    profile = PROFILES.get(pose.weapon_id, PROFILES["rifle"])
    palette = HAND_PALETTES.get(pose.hands_id, HAND_PALETTES["tactical"])
    s = pose.scale
    ang = pose.angle
    ca, sa = math.cos(ang), math.sin(ang)
    base_x, base_y = pose.base_x, pose.base_y

    def tf(px: float, py: float) -> tuple[float, float]:
        lx = px * s
        ly = py * s
        return base_x + lx * ca - ly * sa, base_y + lx * sa + ly * ca

    body = profile.color_body
    metal = profile.color_metal
    accent = profile.color_accent
    bw = profile.body_w
    bh = profile.body_h
    bl = profile.length - 40
    bww = profile.barrel_w

    shadow_pts = [tf(-40, bh * 1.1), tf(bl, bh * 0.6), tf(bl, bh * 0.9), tf(-30, bh * 1.35)]
    shadow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    _poly(shadow_surf, (0, 0, 0, 50), shadow_pts)
    surface.blit(shadow_surf, (0, 0))

    _poly(
        surface,
        palette["sleeve"],
        [tf(-20, 40), tf(40, 55), tf(70, 120), tf(-10, 130), tf(-40, 90)],
    )
    _poly(
        surface,
        palette["glove"],
        [tf(10, 20), tf(55, 30), tf(75, 70), tf(35, 85), tf(5, 55)],
    )

    for i, (fx, fy, fw) in enumerate(((55, 18, 18), (68, 28, 16), (72, 42, 14), (60, 55, 12))):
        p1 = tf(fx, fy)
        p2 = tf(fx + fw, fy - 4 + i)
        p3 = tf(fx + fw - 2, fy + 10)
        p4 = tf(fx - 2, fy + 12)
        _poly(surface, palette["glove_hi"] if i % 2 == 0 else palette["glove"], [p1, p2, p3, p4])

    if profile.stock:
        _poly(
            surface,
            body,
            [tf(-90, 10), tf(-20, 5), tf(-15, 35), tf(-70, 55), tf(-100, 40)],
        )
        _poly(
            surface,
            accent,
            [tf(-85, 18), tf(-30, 14), tf(-28, 28), tf(-75, 40)],
        )

    _poly(
        surface,
        body,
        [
            tf(0, -bh * 0.3),
            tf(bw, -bh * 0.35),
            tf(bw + 10, bh * 0.25),
            tf(bw * 0.2, bh * 0.45),
            tf(-5, bh * 0.2),
        ],
    )
    _poly(
        surface,
        metal,
        [tf(15, -bh * 0.45), tf(bw - 10, -bh * 0.5), tf(bw - 8, -bh * 0.28), tf(18, -bh * 0.22)],
    )

    _poly(
        surface,
        metal,
        [
            tf(bw - 5, -bww * 0.35),
            tf(bl, -bww * 0.3),
            tf(bl + 8, bww * 0.15),
            tf(bw, bww * 0.35),
        ],
    )
    _poly(
        surface,
        (30, 30, 32),
        [
            tf(bl - 5, -bww * 0.45),
            tf(bl + 22, -bww * 0.4),
            tf(bl + 24, bww * 0.35),
            tf(bl - 3, bww * 0.4),
        ],
    )

    if profile.magazine:
        _poly(
            surface,
            (25, 28, 30),
            [tf(45, bh * 0.2), tf(70, bh * 0.15), tf(78, bh * 0.95), tf(40, bh * 1.05), tf(35, bh * 0.45)],
        )

    _poly(
        surface,
        body,
        [tf(25, bh * 0.15), tf(50, bh * 0.1), tf(42, bh * 0.95), tf(15, bh * 1.05), tf(10, bh * 0.4)],
    )
    _poly(
        surface,
        palette["glove"],
        [tf(18, bh * 0.35), tf(48, bh * 0.3), tf(40, bh * 0.9), tf(14, bh * 0.95)],
    )

    _poly(
        surface,
        accent,
        [tf(bw * 0.45, -bh * 0.15), tf(bw * 0.95, -bh * 0.2), tf(bw * 0.9, bh * 0.25), tf(bw * 0.4, bh * 0.3)],
    )

    if profile.scope:
        _poly(
            surface,
            (20, 22, 25),
            [tf(bw * 0.35, -bh * 0.95), tf(bw * 0.75, -bh * 1.0), tf(bw * 0.78, -bh * 0.55), tf(bw * 0.32, -bh * 0.5)],
        )
        scx, scy = tf(bw * 0.55, -bh * 0.78)
        pygame.draw.circle(surface, (15, 40, 50), (int(scx), int(scy)), max(3, int(8 * s)))
        pygame.draw.circle(surface, (80, 200, 220), (int(scx), int(scy)), max(2, int(4 * s)), 1)

    fs = tf(bl - 15, -bww * 0.7)
    pygame.draw.line(surface, metal, fs, tf(bl - 15, -bww * 1.3), max(1, int(2 * s)))

    _poly(
        surface,
        palette["sleeve"],
        [tf(bw * 0.55, bh * 0.5), tf(bw * 0.9, bh * 0.35), tf(bw * 1.05, bh * 1.1), tf(bw * 0.45, bh * 1.2)],
    )
    _poly(
        surface,
        palette["glove"],
        [
            tf(bw * 0.6, bh * 0.05),
            tf(bw * 0.95, -bh * 0.05),
            tf(bw * 1.05, bh * 0.45),
            tf(bw * 0.7, bh * 0.55),
            tf(bw * 0.55, bh * 0.35),
        ],
    )
    _poly(
        surface,
        palette["glove_hi"],
        [tf(bw * 0.72, -bh * 0.05), tf(bw * 0.88, -bh * 0.25), tf(bw * 0.95, bh * 0.05), tf(bw * 0.78, bh * 0.15)],
    )

    for kx, ky in ((30, 25), (42, 22), (52, 28), (bw * 0.75, bh * 0.15)):
        px, py = tf(kx, ky)
        pygame.draw.circle(surface, palette["skin_shade"], (int(px), int(py)), max(2, int(3 * s)))
