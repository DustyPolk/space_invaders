import pygame
import random
from dataclasses import dataclass, field
import src.sprites as sprites
from src.constants import *

@dataclass
class Spaceship:
    """
    Represents the player's spaceship.
    
    Attributes:
        name (str): The name of the ship.
        health (int): Current health points.
        x (int): Current x-coordinate.
        y (int): Current y-coordinate.
        lives (int): Remaining lives.
    """
    name: str
    health: int
    x: int
    y: int
    
    # Defaults / Internal state
    lives: int = 3
    dead: bool = False
    invulnerable: bool = False
    invulnerable_start: int = 0
    invulnerable_duration: int = 2000
    max_bullets: int = 3
    width: int = 50
    height: int = 30
    bullet_speed: int = 7
    last_shot_time: int = 0
    shoot_delay: int = 500
    
    # Mutable defaults need field(default_factory=...)
    bullets: list = field(default_factory=list)
    spawn_x: int = field(init=False)
    spawn_y: int = field(init=False)

    def __post_init__(self):
        self.spawn_x = self.x
        self.spawn_y = self.y

    def take_damage(self, amount: int) -> None:
        """
        Reduces health by the given amount. Handles life loss and respawning logic.
        """
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
        """Returns True if the ship has health > 0."""
        return self.health > 0
    
    def shoot(self):
        """
        Fires a bullet if the cooldown has passed and max bullets limit isn't reached.
        """
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
        """
        Updates the ship's position based on keyboard input (Left/Right arrows).
        Also updates the position of active bullets.
        """
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
        """
        Draws the ship to the screen. Handles blinking effect when invulnerable.
        """
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
    

@dataclass
class Enemy:
    """
    Represents a single alien enemy.
    """
    x: int
    y: int
    w: int
    h: int
    row: int
    col: int
    alive: bool = True
    frame: int = 0
    rect: pygame.Rect = field(init=False)

    def __post_init__(self):
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the enemy sprite using the current animation frame."""
        if not self.alive:
            return
        
        # simple two-frame animation
        pattern = sprites.ALIEN_A_1 if self.frame == 0 else sprites.ALIEN_A_2
        # Colors: Greenish
        color = (50, 255, 50)
        
        sprites.draw_pixel_sprite(screen, pattern, self.rect.x, self.rect.y, self.rect.width, self.rect.height, color)

    def hit(self) -> None:
        """Marks the enemy as dead."""
        self.alive = False


@dataclass
class Fleet:
    """
    Manages the grid of enemies, their movement, and coordinated firing.
    """
    cols: int
    rows: int
    enemy_w: int
    enemy_h: int
    h_spacing: int
    v_spacing: int
    start_x: int
    start_y: int
    screen_width: int
    
    direction: int = 1
    step_distance: int = 16
    drop_amount: int = 32
    step_interval: int = 600
    last_step: int = field(default_factory=pygame.time.get_ticks)
    enemies: list = field(init=False)

    def __post_init__(self):
        self.enemies = []  # 2D list [row][col]
        for r in range(self.rows):
            row_list = []
            for c in range(self.cols):
                x = self.start_x + c * (self.enemy_w + self.h_spacing)
                y = self.start_y + r * (self.enemy_h + self.v_spacing)
                row_list.append(Enemy(x, y, self.enemy_w, self.enemy_h, r, c))
            self.enemies.append(row_list)
        
        # Override last_step to ensure it's current if get_ticks was called early
        self.last_step = pygame.time.get_ticks()

    def all_enemies(self):
        """Returns a flat list of all enemies in the fleet."""
        return [e for row in self.enemies for e in row]

    def bounding_rect(self):
        """Calculates the bounding rectangle enclosing all living enemies."""
        alive_rects = [e.rect for e in self.all_enemies() if e.alive]
        if not alive_rects:
            return None
        br = alive_rects[0].copy()
        for r in alive_rects[1:]:
            br.union_ip(r)
        return br

    def update(self) -> None:
        """
        Updates the fleet's position. Handles side collision detection
        to reverse direction and drop down.
        """
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
        """Draws all alive enemies in the fleet."""
        for e in self.all_enemies():
            e.draw(screen)

    def pick_shooter(self):
        """Selects a random enemy from the bottom row of any column to shoot."""
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
        """Checks if any enemy is hit by the given rectangle (bullet)."""
        for e in self.all_enemies():
            if e.alive and e.rect.colliderect(rect):
                e.hit()
                return e
        return None