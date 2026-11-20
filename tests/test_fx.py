"""Tests for the particle effect pool."""

from __future__ import annotations

from snake.fx import ParticleSystem


def test_particles_burst_and_expire() -> None:
    fx = ParticleSystem(capacity=8)
    fx.burst(10, 10, (255, 0, 0), count=4)
    assert sum(p is not None for p in fx.particles) == 4
    fx.update(1.0)
    assert all(p is None or p.life <= 0 for p in fx.particles)
