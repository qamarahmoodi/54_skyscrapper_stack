import pygame
import random


class Debris:
    """Animated off-cut remnant that falls, spins, and fades off-screen."""

    def __init__(self, x, y, w, h, color):
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)
        self.color = color
        self.vy = random.uniform(1.5, 3.0)
        self.vx = random.uniform(-2.0, 2.0)
        self.angle = 0.0
        self.spin = random.uniform(-8.0, 8.0)
        self.alpha = 255

    def update(self):
        self.vy += 0.35          # gravity
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin
        # Fade out after falling a bit
        if self.y > 200:
            self.alpha = max(0, self.alpha - 4)

    def offscreen(self, height):
        return self.y > height + 100 or self.alpha <= 0

    def render(self, surface):
        w = max(1, int(self.w))
        h = max(1, int(self.h))
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((self.color[0], self.color[1], self.color[2], self.alpha))
        rotated = pygame.transform.rotate(surf, self.angle)
        rect = rotated.get_rect(center=(self.x + self.w / 2, self.y + self.h / 2))
        surface.blit(rotated, rect)