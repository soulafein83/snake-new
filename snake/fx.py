"""Lightweight particle effects for visual polish."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple[int, int, int]
    size: int


class ParticleSystem:
    """Fixed-size pool; no allocations during updates."""

    def __init__(self, capacity: int = 160) -> None:
        self.capacity = capacity
        self.particles: list[Particle | None] = [None] * capacity
        self.rng = random.Random()

    def burst(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        count: int = 14,
        speed: float = 90.0,
    ) -> None:
        for _ in range(count):
            angle = self.rng.random() * math.tau
            velocity = speed * (0.4 + 0.6 * self.rng.random())
            life = 0.35 + 0.35 * self.rng.random()
            particle = Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * velocity,
                vy=math.sin(angle) * velocity,
                life=life,
                max_life=life,
                color=color,
                size=2 + int(self.rng.random() * 3),
            )
            for index, existing in enumerate(self.particles):
                if existing is None or existing.life <= 0:
                    self.particles[index] = particle
                    break

    def update(self, dt: float) -> None:
        for particle in self.particles:
            if particle is None or particle.life <= 0:
                continue
            particle.life -= dt
            particle.x += particle.vx * dt
            particle.vy += 140.0 * dt
            particle.y += particle.vy * dt

    def draw(self, surface) -> None:  # type: ignore[no-untyped-def]
        import pygame

        for particle in self.particles:
            if particle is None or particle.life <= 0:
                continue
            alpha = int(255 * max(0.0, particle.life / particle.max_life))
            color = (*particle.color, alpha)
            cell = pygame.Rect(
                int(particle.x) - particle.size,
                int(particle.y) - particle.size,
                particle.size * 2,
                particle.size * 2,
            )
            pygame.draw.rect(surface, color, cell, border_radius=2)
