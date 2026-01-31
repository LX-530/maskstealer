from __future__ import annotations

import math
import pygame


class PlayerProjectile:
    def __init__(
        self,
        x: float,
        y: float,
        direction: str,
        speed: float,
        damage: int,
        color,
        radius: int,
        ttl_ms: int,
        kind: str,
    ):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.color = color
        self.radius = radius
        self.ttl_ms = ttl_ms
        self.kind = kind
        self.age_ms = 0

        self.dx, self.dy = self._direction_vector(direction)

    def _direction_vector(self, direction):
        if direction == "up":
            return 0, -1
        if direction == "down":
            return 0, 1
        if direction == "left":
            return -1, 0
        return 1, 0

    def update(self, delta_ms: int):
        self.age_ms += delta_ms
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

    def is_alive(self) -> bool:
        return self.age_ms < self.ttl_ms

    def check_collision(self, monster) -> bool:
        distance = math.hypot(self.x - monster.x, self.y - monster.y)
        return distance < self.radius + monster.hit_radius

    def draw(self, screen, camera_x, camera_y):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        if self.kind == "wave":
            pygame.draw.circle(screen, self.color, (sx, sy), self.radius)
            pygame.draw.circle(screen, (180, 220, 255), (sx, sy), max(2, self.radius - 4), 2)
        elif self.kind == "fireball":
            pygame.draw.circle(screen, (255, 80, 40), (sx, sy), self.radius + 2)
            pygame.draw.circle(screen, self.color, (sx, sy), self.radius)
            pygame.draw.circle(screen, (255, 200, 140), (sx, sy), max(2, self.radius - 4))
        else:
            pygame.draw.circle(screen, self.color, (sx, sy), self.radius)
