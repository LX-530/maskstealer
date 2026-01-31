from __future__ import annotations

import math
import pygame


class LaserBeam:
    def __init__(
        self,
        x: float,
        y: float,
        direction: str,
        length: int = 160,
        width: int = 6,
        duration_ms: int = 140,
        color=(110, 255, 255),
    ):
        self.x = x
        self.y = y
        self.direction = direction
        self.length = length
        self.width = width
        self.duration_ms = duration_ms
        self.color = color
        self.spawn_time = pygame.time.get_ticks()

        dx, dy = self._direction_vector(direction)
        self.end_x = x + dx * length
        self.end_y = y + dy * length

    def _direction_vector(self, direction):
        if direction == "up":
            return 0, -1
        if direction == "down":
            return 0, 1
        if direction == "left":
            return -1, 0
        return 1, 0

    def is_alive(self) -> bool:
        return pygame.time.get_ticks() - self.spawn_time < self.duration_ms

    def get_segment(self):
        return (self.x, self.y, self.end_x, self.end_y)

    def draw(self, screen, camera_x, camera_y):
        age = pygame.time.get_ticks() - self.spawn_time
        fade = max(0.0, 1.0 - age / self.duration_ms)
        core = self._scale_color(self.color, 0.7 + 0.3 * fade)
        mid = self._scale_color(self.color, 0.5 + 0.4 * fade)
        glow = self._scale_color(self.color, 0.3 + 0.4 * fade)

        sx = self.x - camera_x
        sy = self.y - camera_y
        ex = self.end_x - camera_x
        ey = self.end_y - camera_y

        pygame.draw.line(screen, glow, (sx, sy), (ex, ey), self.width + 6)
        pygame.draw.line(screen, mid, (sx, sy), (ex, ey), self.width + 3)
        pygame.draw.line(screen, core, (sx, sy), (ex, ey), self.width)

        pygame.draw.circle(screen, core, (int(ex), int(ey)), max(2, self.width // 2))

    def _scale_color(self, color, factor):
        return (
            min(255, int(color[0] * factor)),
            min(255, int(color[1] * factor)),
            min(255, int(color[2] * factor)),
        )
