from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import pygame

from .weapons import PROFILES


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple[int, int, int]
    kind: str = "spark"


@dataclass
class Tracer:
    x0: float
    y0: float
    x1: float
    y1: float
    life: float
    max_life: float
    width: float
    color: tuple[int, int, int] = (255, 230, 120)


@dataclass
class Impact:
    x: float
    y: float
    life: float
    max_life: float
    radius: float
    color: tuple[int, int, int] = (255, 200, 80)


@dataclass
class Shell:
    x: float
    y: float
    vx: float
    vy: float
    rot: float
    vrot: float
    life: float
    max_life: float


@dataclass
class MuzzleFlash:
    x: float
    y: float
    angle: float
    life: float
    max_life: float
    scale: float


@dataclass
class EffectState:
    particles: list[Particle] = field(default_factory=list)
    tracers: list[Tracer] = field(default_factory=list)
    impacts: list[Impact] = field(default_factory=list)
    shells: list[Shell] = field(default_factory=list)
    flashes: list[MuzzleFlash] = field(default_factory=list)
    recoil_x: float = 0.0
    recoil_y: float = 0.0
    recoil_rot: float = 0.0


class EffectSystem:
    def __init__(self) -> None:
        self.state = EffectState()

    def clear(self) -> None:
        self.state = EffectState()

    def shoot(
        self,
        muzzle: tuple[float, float],
        target: tuple[float, float],
        weapon_id: str,
        *,
        muzzle_flash: bool,
        tracer: bool,
        impact: bool,
        recoil: bool,
        shell_eject: bool,
        barrel_angle: float | None = None,
    ) -> None:
        profile = PROFILES.get(weapon_id, PROFILES["rifle"])
        mx, my = muzzle
        tx, ty = target
        # Prefer weapon barrel angle so flash/tracer match the drawn gun
        angle = float(barrel_angle) if barrel_angle is not None else math.atan2(ty - my, tx - mx)
        dist = max(1.0, math.hypot(tx - mx, ty - my))

        if recoil:
            kick = profile.recoil_kick
            # Recoil opposite to barrel direction (screen space)
            self.state.recoil_x += -math.cos(angle) * kick * random.uniform(0.15, 0.35)
            self.state.recoil_y += -math.sin(angle) * kick * random.uniform(0.35, 0.7)
            self.state.recoil_x += random.uniform(-kick * 0.12, kick * 0.12)
            self.state.recoil_y += kick * random.uniform(0.25, 0.55)
            self.state.recoil_rot += random.uniform(-0.04, 0.02)

        if muzzle_flash:
            self.state.flashes.append(
                MuzzleFlash(
                    x=mx,
                    y=my,
                    angle=angle,
                    life=0.06,
                    max_life=0.06,
                    scale=profile.muzzle_size * random.uniform(0.85, 1.2),
                )
            )
            for _ in range(10):
                a = angle + random.uniform(-0.6, 0.6)
                sp = random.uniform(120, 420)
                self.state.particles.append(
                    Particle(
                        x=mx,
                        y=my,
                        vx=math.cos(a) * sp,
                        vy=math.sin(a) * sp,
                        life=random.uniform(0.04, 0.12),
                        max_life=0.12,
                        size=random.uniform(2, 5),
                        color=random.choice(
                            ((255, 240, 160), (255, 180, 60), (255, 255, 220), (255, 120, 30))
                        ),
                        kind="spark",
                    )
                )
            for _ in range(4):
                a = angle + random.uniform(-0.4, 0.4)
                sp = random.uniform(20, 80)
                self.state.particles.append(
                    Particle(
                        x=mx + random.uniform(-4, 4),
                        y=my + random.uniform(-4, 4),
                        vx=math.cos(a) * sp,
                        vy=math.sin(a) * sp - 30,
                        life=random.uniform(0.2, 0.45),
                        max_life=0.45,
                        size=random.uniform(6, 14),
                        color=(160, 160, 160),
                        kind="smoke",
                    )
                )

        pellets = profile.pellets
        for _i in range(pellets):
            spread = 0.0 if pellets == 1 else random.uniform(-0.08, 0.08)
            shot_ang = angle + spread
            # Project along barrel (or spread) to cursor distance — aligned with gun
            px = mx + math.cos(shot_ang) * dist
            py = my + math.sin(shot_ang) * dist
            if pellets == 1:
                # Snap impact exactly to cursor; tracer still barrel-aligned path
                px, py = tx, ty
                # Tracer end on barrel ray at cursor range (not a crooked chord)
                tr_x = mx + math.cos(angle) * dist
                tr_y = my + math.sin(angle) * dist
            else:
                tr_x, tr_y = px, py

            if tracer:
                self.state.tracers.append(
                    Tracer(
                        x0=mx,
                        y0=my,
                        x1=tr_x,
                        y1=tr_y,
                        life=0.07 if pellets == 1 else 0.05,
                        max_life=0.07,
                        width=profile.tracer_width * (0.7 if pellets > 1 else 1.0),
                        color=random.choice(
                            ((255, 230, 120), (255, 200, 80), (255, 255, 200))
                        ),
                    )
                )

            if impact:
                self.state.impacts.append(
                    Impact(
                        x=px + random.uniform(-3, 3),
                        y=py + random.uniform(-3, 3),
                        life=0.18,
                        max_life=0.18,
                        radius=random.uniform(10, 18) * (0.7 if pellets > 1 else 1.0),
                    )
                )
                for _ in range(6 if pellets == 1 else 3):
                    a = random.uniform(0, math.tau)
                    sp = random.uniform(80, 280)
                    self.state.particles.append(
                        Particle(
                            x=px,
                            y=py,
                            vx=math.cos(a) * sp,
                            vy=math.sin(a) * sp,
                            life=random.uniform(0.08, 0.2),
                            max_life=0.2,
                            size=random.uniform(1.5, 3.5),
                            color=random.choice(
                                ((255, 220, 100), (255, 160, 50), (255, 255, 255), (200, 200, 200))
                            ),
                            kind="spark",
                        )
                    )

        if shell_eject:
            # Eject roughly perpendicular to barrel
            perp = angle - math.pi * 0.5
            side = 1.0 if random.random() > 0.15 else -1.0
            ej = random.uniform(120, 240) * side
            self.state.shells.append(
                Shell(
                    x=mx - math.cos(angle) * 28,
                    y=my - math.sin(angle) * 28,
                    vx=math.cos(perp) * ej + random.uniform(-30, 30),
                    vy=math.sin(perp) * ej + random.uniform(-220, -80),
                    rot=random.uniform(0, math.tau),
                    vrot=random.uniform(-12, 12),
                    life=0.7,
                    max_life=0.7,
                )
            )

    def update(self, dt: float) -> None:
        st = self.state

        # recoil spring-back
        st.recoil_x *= max(0.0, 1.0 - 10.0 * dt)
        st.recoil_y *= max(0.0, 1.0 - 9.0 * dt)
        st.recoil_rot *= max(0.0, 1.0 - 8.0 * dt)
        st.recoil_x += (0.0 - st.recoil_x) * min(1.0, 8.0 * dt)
        st.recoil_y += (0.0 - st.recoil_y) * min(1.0, 7.0 * dt)

        def alive(items: list, attr: str = "life") -> list:
            out = []
            for item in items:
                setattr(item, attr, getattr(item, attr) - dt)
                if getattr(item, attr) > 0:
                    out.append(item)
            return out

        for p in st.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 40 * dt if p.kind == "smoke" else 0
            p.vx *= 0.92
            p.vy *= 0.92
        st.particles = alive(st.particles)

        st.tracers = alive(st.tracers)
        st.impacts = alive(st.impacts)
        st.flashes = alive(st.flashes)

        for sh in st.shells:
            sh.x += sh.vx * dt
            sh.y += sh.vy * dt
            sh.vy += 900 * dt
            sh.rot += sh.vrot * dt
        st.shells = alive(st.shells)

    def draw(self, surface: pygame.Surface) -> None:
        st = self.state

        for tr in st.tracers:
            t = tr.life / tr.max_life
            alpha = int(255 * t)
            col = (*tr.color, alpha)
            layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.line(
                layer,
                col,
                (int(tr.x0), int(tr.y0)),
                (int(tr.x1), int(tr.y1)),
                max(1, int(tr.width)),
            )
            # bright core
            core = (255, 255, 240, alpha)
            pygame.draw.line(
                layer,
                core,
                (int(tr.x0), int(tr.y0)),
                (int(tr.x1), int(tr.y1)),
                1,
            )
            surface.blit(layer, (0, 0))

        for flash in st.flashes:
            t = flash.life / flash.max_life
            self._draw_muzzle_flash(surface, flash.x, flash.y, flash.angle, flash.scale * (0.6 + 0.4 * t), t)

        for imp in st.impacts:
            t = imp.life / imp.max_life
            alpha = int(220 * t)
            r = imp.radius * (1.3 - t)
            layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.circle(layer, (*imp.color, alpha), (int(imp.x), int(imp.y)), int(r), 2)
            pygame.draw.circle(
                layer,
                (255, 255, 255, alpha),
                (int(imp.x), int(imp.y)),
                max(1, int(r * 0.25)),
            )
            # cross sparks
            for a in (0.2, 1.0, 2.0, 2.8):
                ex = imp.x + math.cos(a) * r * 1.2
                ey = imp.y + math.sin(a) * r * 1.2
                pygame.draw.line(
                    layer,
                    (255, 220, 120, alpha),
                    (int(imp.x), int(imp.y)),
                    (int(ex), int(ey)),
                    1,
                )
            surface.blit(layer, (0, 0))

        for p in st.particles:
            t = p.life / p.max_life
            if p.kind == "smoke":
                alpha = int(70 * t)
                size = p.size * (1.5 - t)
                layer = pygame.Surface((int(size * 2 + 2), int(size * 2 + 2)), pygame.SRCALPHA)
                pygame.draw.circle(
                    layer,
                    (*p.color, alpha),
                    (int(size + 1), int(size + 1)),
                    max(1, int(size)),
                )
                surface.blit(layer, (p.x - size, p.y - size))
            else:
                alpha = int(255 * t)
                layer = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(layer, (*p.color, alpha), (4, 4), max(1, int(p.size * t)))
                surface.blit(layer, (p.x - 4, p.y - 4))

        for sh in st.shells:
            t = sh.life / sh.max_life
            alpha = int(255 * min(1.0, t * 2))
            layer = pygame.Surface((16, 16), pygame.SRCALPHA)
            cx, cy = 8, 8
            ca, sa = math.cos(sh.rot), math.sin(sh.rot)
            pts = [
                (cx + (-4) * ca - (-1.5) * sa, cy + (-4) * sa + (-1.5) * ca),
                (cx + 4 * ca - (-1.5) * sa, cy + 4 * sa + (-1.5) * ca),
                (cx + 4 * ca - 1.5 * sa, cy + 4 * sa + 1.5 * ca),
                (cx + (-4) * ca - 1.5 * sa, cy + (-4) * sa + 1.5 * ca),
            ]
            pygame.draw.polygon(layer, (220, 180, 60, alpha), pts)
            surface.blit(layer, (sh.x - 8, sh.y - 8))

    def _draw_muzzle_flash(
        self,
        surface: pygame.Surface,
        x: float,
        y: float,
        angle: float,
        scale: float,
        t: float,
    ) -> None:
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        alpha = int(255 * t)
        # main star
        spikes = 7
        pts_outer = []
        pts_inner = []
        for i in range(spikes * 2):
            a = angle + (i / (spikes * 2)) * math.tau
            r = (28 if i % 2 == 0 else 12) * scale
            pts_outer.append((x + math.cos(a) * r, y + math.sin(a) * r))
            ri = r * 0.45
            pts_inner.append((x + math.cos(a) * ri, y + math.sin(a) * ri))
        pygame.draw.polygon(layer, (255, 200, 60, alpha), pts_outer)
        pygame.draw.polygon(layer, (255, 255, 220, alpha), pts_inner)
        pygame.draw.circle(layer, (255, 255, 255, alpha), (int(x), int(y)), int(6 * scale))
        # elongated blast toward aim
        ex = x + math.cos(angle) * 40 * scale
        ey = y + math.sin(angle) * 40 * scale
        pygame.draw.line(layer, (255, 230, 120, alpha), (int(x), int(y)), (int(ex), int(ey)), max(2, int(6 * scale)))
        surface.blit(layer, (0, 0))

    @property
    def recoil_offset(self) -> tuple[float, float]:
        return self.state.recoil_x, self.state.recoil_y
