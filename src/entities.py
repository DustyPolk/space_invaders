import pygame
import random
import src.sprites as sprites
from src.constants import *

class Spaceship:
    def __init__(self, name: str, health: int, x: int, y: int) -> None:
        self.name = name
        self.health = health
        self.x = x
        self.y = y
        # spawn position for respawn
        self.spawn_x = x
        self.spawn_y = y
        # lives and death state
        self.lives = 3
        self.dead = False
        # temporary invulnerability after respawn (ms)
        self.invulnerable = False
        self.invulnerable_start = 0
        self.invulnerable_duration = 2000
        # limit simultaneous player bullets
        self.max_bullets = 3
        
        # Ship dimensions (used for math and drawing)
        self.width = 50
        self.height = 30
        
        # Bullet settings
        self.bullets = []  # List to hold bullet rectangles
        self.bullet_speed = 7
        self.last_shot_time = 0
        self.shoot_delay = 500  # Milliseconds between shots (increase to shoot slower)

    def take_damage(self, amount: int) -> None:
        if self.invulnerable or self.dead:
            return

        self.health -= amount
        if self.health <= 0:
            # lose a life
            self.lives -= 1
            if self.lives > 0:
                # respawn
                self.health = 100
                self.x = self.spawn_x
                self.y = self.spawn_y
                self.bullets.clear()
                self.invulnerable = True
                self.invulnerable_start = pygame.time.get_ticks()
            else:
                # final death
                self.health = 0
                self.dead = True

    def is_alive(self) -> bool:
        return self.health > 0
    
    def shoot(self):
        # Check current time
        current_time = pygame.time.get_ticks()
        
        # Only shoot if enough time has passed since the last shot
        if current_time - self.last_shot_time > self.shoot_delay and len(self.bullets) < self.max_bullets:
            # Create a bullet rect centered on the ship
            # Math: Bullet X = Ship X + (Ship Width / 2) - (Bullet Width / 2)
            bullet_w = BULLET_WIDTH
            bullet_h = BULLET_HEIGHT
            bullet_x = self.x + (self.width // 2) - (bullet_w // 2)
            bullet_y = self.y
            
            new_bullet = pygame.Rect(bullet_x, bullet_y, bullet_w, bullet_h)
            self.bullets.append(new_bullet)
            
            self.last_shot_time = current_time

    def move(self) -> None:
        # Update ship position based on input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= 5
        if keys[pygame.K_RIGHT]:
            self.x += 5
            
        # Update bullets
        # Iterate over a copy of the list [:] so we can remove items while looping
        for bullet in self.bullets[:]:
            bullet.y -= self.bullet_speed
            # Remove bullet if it goes off screen
            if bullet.y < 0:
                self.bullets.remove(bullet)
    
    def draw_ship(self, screen: pygame.Surface) -> None:
        # Draw the ship (with invulnerability blink)
        now = pygame.time.get_ticks()
        draw = True
        if self.invulnerable:
            if now - self.invulnerable_start >= self.invulnerable_duration:
                self.invulnerable = False
            else:
                # blinking effect while invulnerable
                if (now - self.invulnerable_start) % 300 < 150:
                    draw = False
        
        if draw and not self.dead:
            sprites.draw_pixel_sprite(screen, sprites.PLAYER_SHIP, self.x, self.y, self.width, self.height, (0, 255, 255)) # Cyan ship

        # Draw the bullets
        for bullet in self.bullets:
            pygame.draw.rect(screen, (255, 255, 0), bullet)
    

class Enemy:
    def __init__(self, x: int, y: int, w: int, h: int, row: int, col: int) -> None:
        self.rect = pygame.Rect(x, y, w, h)
        self.row = row
        self.col = col
        self.alive = True
        self.frame = 0

    def draw(self, screen: pygame.Surface) -> None:
        if not self.alive:
            return
        
        # simple two-frame animation
        pattern = sprites.ALIEN_A_1 if self.frame == 0 else sprites.ALIEN_A_2
        # Colors: Greenish
        color = (50, 255, 50)
        
        sprites.draw_pixel_sprite(screen, pattern, self.rect.x, self.rect.y, self.rect.width, self.rect.height, color)

    def hit(self) -> None:
        self.alive = False


class Fleet:
    def __init__(self, cols: int, rows: int, enemy_w: int, enemy_h: int, h_spacing: int, v_spacing: int, start_x: int, start_y: int, screen_width: int) -> None:
        self.cols = cols
        self.rows = rows
        self.enemy_w = enemy_w
        self.enemy_h = enemy_h
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        self.screen_width = screen_width

        self.enemies = []  # 2D list [row][col]
        for r in range(rows):
            row_list = []
            for c in range(cols):
                x = start_x + c * (enemy_w + h_spacing)
                y = start_y + r * (enemy_h + v_spacing)
                row_list.append(Enemy(x, y, enemy_w, enemy_h, r, c))
            self.enemies.append(row_list)

        self.direction = 1  # 1 = right, -1 = left
        self.step_distance = 16
        self.drop_amount = 32
        self.step_interval = 600  # milliseconds between fleet steps
        self.last_step = pygame.time.get_ticks()

    def all_enemies(self):
        return [e for row in self.enemies for e in row]

    def bounding_rect(self):
        alive_rects = [e.rect for e in self.all_enemies() if e.alive]
        if not alive_rects:
            return None
        br = alive_rects[0].copy()
        for r in alive_rects[1:]:
            br.union_ip(r)
        return br

    def update(self) -> None:
        now = pygame.time.get_ticks()
        if now - self.last_step < self.step_interval:
            return
        self.last_step = now

        br = self.bounding_rect()
        if not br:
            return

        would_hit_left = (br.left + self.direction * self.step_distance) < 0
        would_hit_right = (br.right + self.direction * self.step_distance) > self.screen_width

        if would_hit_left or would_hit_right:
            # reverse and drop
            self.direction *= -1
            for e in self.all_enemies():
                if e.alive:
                    e.rect.y += self.drop_amount
            # speed up slightly when changing direction
            self.step_interval = max(100, int(self.step_interval * 0.95))
        else:
            for e in self.all_enemies():
                if e.alive:
                    e.rect.x += self.direction * self.step_distance

        # toggle simple animation frame
        for e in self.all_enemies():
            if e.alive:
                e.frame ^= 1

    def draw(self, screen: pygame.Surface) -> None:
        for e in self.all_enemies():
            e.draw(screen)

    def pick_shooter(self):
        # collect the bottom-most alive enemy in each column
        candidates = []
        for c in range(self.cols):
            for r in range(self.rows - 1, -1, -1):
                e = self.enemies[r][c]
                if e.alive:
                    candidates.append(e)
                    break
        if not candidates:
            return None
        return random.choice(candidates)

    def hit_enemy(self, rect: pygame.Rect):
        for e in self.all_enemies():
            if e.alive and e.rect.colliderect(rect):
                e.hit()
                return e
        return None
