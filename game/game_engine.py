import random
import pygame
from game.block import Block
from game.debris import Debris


class GameEngine:
    # Task 2: how close the centers must be for a "perfect" drop (pixels)
    PERFECT_THRESHOLD = 4.0
    # Task 2: width restored per perfect-streak reward
    PERFECT_GROW = 6.0
    # Task 2: every N consecutive perfects triggers width restoration
    PERFECT_STREAK_REWARD = 2

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)

        # Task 4: atmospheric sky keyframes (height, RGB)
        self.sky_stops = [
            (0,  (24, 27, 36)),    # night blue (original)
            (5,  (52, 30, 78)),    # twilight purple
            (12, (128, 52, 96)),   # sunset pink
            (20, (240, 130, 80)),  # golden hour
            (30, (120, 180, 230)), # day blue
            (45, (15, 15, 35)),    # near space
        ]

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),   # Crimson
            (240, 140, 45),  # Orange
            (245, 210, 50),  # Gold
            (60, 195, 110),  # Green
            (50, 150, 240),  # Blue
            (165, 80, 225),  # Purple
        ]
        return palette[index % len(palette)]

    def reset(self):
        self.score = 0
        self.game_over = False

        # Task 2 state
        self.perfect_streak = 0
        self.perfect_flash = 0.0
        self.perfect_y = 0

        # Task 3 state
        self.debris = []

        base_x = (self.width - self.base_width) // 2
        base_y = self.height - 60
        base_block = Block(base_x, base_y, self.base_width,
                           self.block_height, self.get_color(0), speed=0)
        self.stack = [base_block]

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]
        next_y = top_block.y - self.block_height - 4
        speed = min(10.0, 4.5 + (len(self.stack) * 0.35))
        color = self.get_color(len(self.stack))

        start_x = 25 if random.choice([True, False]) else self.width - 25 - top_block.width
        self.active_block = Block(start_x, next_y, top_block.width,
                                  self.block_height, color, speed=speed)

    # ------------------------------------------------------------------
    # Task 1: FIXED drop logic  (was: overlap <= 0 → now: overlap > 0)
    # ------------------------------------------------------------------
    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        # 1D bounding-box intersection
        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left

        if overlap > 0:
            # ----- Successful placement -----
            # Task 2: check for perfect alignment (centers nearly coincide)
            top_center = top_block.x + top_block.width / 2.0
            act_center = act.x + act.width / 2.0
            misalign = abs(top_center - act_center)

            if misalign <= self.PERFECT_THRESHOLD:
                # Perfect: snap flush, no trimming, bonus score
                new_block = Block(top_block.x, act.y, top_block.width,
                                  self.block_height, act.color, speed=0)
                self.score += 2
                self.perfect_streak += 1
                self.perfect_flash = 0.7
                self.perfect_y = act.y

                # Task 2: width restoration on a streak
                if (self.perfect_streak % self.PERFECT_STREAK_REWARD == 0
                        and new_block.width < self.base_width):
                    grow = self.PERFECT_GROW
                    new_x = new_block.x - grow / 2.0
                    new_w = new_block.width + grow
                    # Keep inside arena bounds
                    if new_x < 20:
                        new_x = 20
                    if new_x + new_w > self.width - 20:
                        new_x = self.width - 20 - new_w
                    new_block.x = new_x
                    new_block.width = min(self.base_width, new_w)
            else:
                # Imperfect but valid: trim & place, spawn debris
                self.perfect_streak = 0
                new_block = Block(left, act.y, overlap,
                                  self.block_height, act.color, speed=0)
                self.score += 1

                # Task 3: spawn debris for each off-cut
                top_right = top_block.x + top_block.width
                act_right = act.x + act.width
                if act.x < top_block.x:
                    self.debris.append(Debris(
                        act.x, act.y,
                        top_block.x - act.x,
                        self.block_height, act.color))
                if act_right > top_right:
                    self.debris.append(Debris(
                        top_right, act.y,
                        act_right - top_right,
                        self.block_height, act.color))

            self.stack.append(new_block)

            # Camera shift when tower nears the top
            if new_block.y < 180:
                shift_amount = self.block_height + 4
                for b in self.stack:
                    b.y += shift_amount
                for d in self.debris:
                    d.y += shift_amount

            self.spawn_active_block()
        else:
            # Task 1: true miss → collapse
            self.game_over = True
            # Task 3: spawn debris for the falling active block
            self.debris.append(Debris(
                act.x, act.y, act.width, act.height, act.color))

    def handle_event(self, event):
        if self.game_over:
            if (event.type == pygame.KEYDOWN and
                    event.key in (pygame.K_r, pygame.K_SPACE)) or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.reset()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drop_block()

    def update(self):
        if not self.game_over:
            self.active_block.update(self.width)

        # Task 2: perfect flash timer
        if self.perfect_flash > 0:
            self.perfect_flash -= 1.0 / 60.0
            if self.perfect_flash < 0:
                self.perfect_flash = 0.0

        # Task 3: update debris
        for d in self.debris:
            d.update()
        self.debris = [d for d in self.debris if not d.offscreen(self.height)]

    # ------------------------------------------------------------------
    # Task 4: sky color interpolation
    # ------------------------------------------------------------------
    def get_sky_color(self):
        h = self.score
        stops = self.sky_stops
        if h <= stops[0][0]:
            return stops[0][1]
        for i in range(len(stops) - 1):
            h0, c0 = stops[i]
            h1, c1 = stops[i + 1]
            if h0 <= h <= h1:
                t = (h - h0) / float(h1 - h0) if h1 > h0 else 0.0
                return tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
        return stops[-1][1]

    def render(self, screen):
        # Task 4: dynamic atmosphere
        screen.fill(self.get_sky_color())

        title_surf = self.font_title.render("Skyscraper Stack", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(f"Height: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 54))

        # Draw debris BEHIND the stack so trimmed bits appear to fall past it
        for d in self.debris:
            d.render(screen)

        for b in self.stack:
            b.render(screen)

        if not self.game_over:
            self.active_block.render(screen)

        # Task 2: "PERFECT!" popup
        if self.perfect_flash > 0:
            perfect_surf = self.font_big.render("PERFECT!", True, (255, 230, 90))
            px = self.width // 2 - perfect_surf.get_width() // 2
            py = int(self.perfect_y) - 10
            screen.blit(perfect_surf, (px, py))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True, (240, 75, 75))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2,
                                    self.height // 2 - 40))

            final_surf = self.font_hud.render(f"Final Height: {self.score}", True,
                                              (255, 255, 255))
            screen.blit(final_surf, (self.width // 2 - final_surf.get_width() // 2,
                                     self.height // 2 + 10))

            restart_surf = self.font_hud.render(
                "Press [Space] or [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2,
                                       self.height // 2 + 50))