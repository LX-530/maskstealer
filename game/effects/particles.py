from __future__ import annotations

import random
from pygame.math import Vector2
import pygame


class Particle:
    def __init__(self, position, velocity, color, lifetime_ms, size):
        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.color = color
        self.lifetime_ms = lifetime_ms
        self.age_ms = 0
        self.size = size

    def update(self, delta_ms: int) -> bool:
        self.age_ms += delta_ms
        if self.age_ms >= self.lifetime_ms:
            return False
        dt = delta_ms / 16.0
        self.position += self.velocity * dt
        self.velocity *= 0.92
        self.velocity.y += 0.04 * dt
        return True

    def draw(self, screen, camera_x, camera_y):
        life = max(0.0, 1.0 - self.age_ms / self.lifetime_ms)
        size = max(1, int(self.size * life))
        color = (
            min(255, int(self.color[0] * life)),
            min(255, int(self.color[1] * life)),
            min(255, int(self.color[2] * life)),
        )
        x = int(self.position.x - camera_x)
        y = int(self.position.y - camera_y)
        pygame.draw.circle(screen, color, (x, y), size)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_burst(self, x, y, color, count=18, speed_min=1.2, speed_max=3.4):
        rng = random.Random()
        for _ in range(count):
            angle = rng.random() * 6.28318
            speed = rng.uniform(speed_min, speed_max)
            velocity = Vector2(speed, 0).rotate_rad(angle)
            lifetime = rng.randint(280, 520)
            size = rng.randint(2, 4)
            jitter = (
                max(0, min(255, color[0] + rng.randint(-20, 20))),
                max(0, min(255, color[1] + rng.randint(-20, 20))),
                max(0, min(255, color[2] + rng.randint(-20, 20))),
            )
            self.particles.append(Particle((x, y), velocity, jitter, lifetime, size))

    def update(self, delta_ms: int):
        self.particles = [p for p in self.particles if p.update(delta_ms)]

    def draw(self, screen, camera_x, camera_y):
        for particle in self.particles:
            particle.draw(screen, camera_x, camera_y)
