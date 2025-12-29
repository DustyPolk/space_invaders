import pygame
import random
import sprites

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
            bullet_w = 4
            bullet_h = 10
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
    

def init_pygame() -> None:
    pygame.init()
    
    # Define screen dimensions variables so we can use them in math
    # Modern 1080p resolution
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Invaders — 1920x1080")
    clock = pygame.time.Clock()
    
    # --- MATH FOR SPAWNING ---
    ship_width = 50
    ship_height = 30
    padding = 10

    # 1. Find the horizontal middle, then shift left by half the ship's width
    start_x = (SCREEN_WIDTH // 2) - (ship_width // 2)

    # 2. Find the bottom, then move up by ship height and padding
    start_y = SCREEN_HEIGHT - ship_height - padding

    spaceship = Spaceship("Falcon", 100, x=start_x, y=start_y)

    # --- GAME STATE ---
    score = 0
    level = 1
    level_transition_start = 0

    # --- ENEMY FLEET SETUP (scaled for 1080p) ---
    ENEMY_COLS = 11
    ENEMY_ROWS = 5
    ENEMY_W = 64
    ENEMY_H = 48
    ENEMY_H_SPACING = 20
    ENEMY_V_SPACING = 18

    fleet_width = ENEMY_COLS * ENEMY_W + (ENEMY_COLS - 1) * ENEMY_H_SPACING
    fleet_start_x = (SCREEN_WIDTH - fleet_width) // 2
    fleet_start_y = 100

    fleet = Fleet(ENEMY_COLS, ENEMY_ROWS, ENEMY_W, ENEMY_H, ENEMY_H_SPACING, ENEMY_V_SPACING, fleet_start_x, fleet_start_y, SCREEN_WIDTH)

    enemy_bullets = []
    enemy_bullet_speed = 5
    last_enemy_shot = pygame.time.get_ticks()
    enemy_shot_interval = 1500
    
    # --- STARFIELD ---
    stars = []
    for _ in range(100):
        # x, y, speed (brightness linked to speed)
        stars.append([random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1, 3)])

    game_state = "MENU" # MENU, PLAYING, GAMEOVER

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Draw background (clear)
        screen.fill("black")
        
        # Update and Draw Stars
        for star in stars:
            star[1] += star[2] # move down
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)
            
            # dim stars are slower, bright are faster
            color_val = min(255, star[2] * 80)
            pygame.draw.circle(screen, (color_val, color_val, color_val), (star[0], star[1]), 2 if star[2] > 2 else 1)

        keys = pygame.key.get_pressed()

        if game_state == "MENU":
            # Title Screen
            title_font = pygame.font.SysFont(None, 120)
            title_surf = title_font.render("SPACE INVADERS", True, (0, 255, 0))
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
            screen.blit(title_surf, title_rect)

            instr_font = pygame.font.SysFont(None, 48)
            instr_surf = instr_font.render("Press SPACE to Start", True, (255, 255, 255))
            instr_rect = instr_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(instr_surf, instr_rect)

            if keys[pygame.K_SPACE]:
                game_state = "PLAYING"
                # Reset game
                spaceship.lives = 3
                spaceship.health = 100
                spaceship.dead = False
                spaceship.invulnerable = True
                spaceship.invulnerable_start = pygame.time.get_ticks()
                spaceship.x = spaceship.spawn_x
                spaceship.y = spaceship.spawn_y
                score = 0
                level = 1
                level_transition_start = 0
                fleet = Fleet(ENEMY_COLS, ENEMY_ROWS, ENEMY_W, ENEMY_H, ENEMY_H_SPACING, ENEMY_V_SPACING, fleet_start_x, fleet_start_y, SCREEN_WIDTH)
                enemy_bullets.clear()
                spaceship.bullets.clear()

        elif game_state == "PLAYING":
            spaceship.move()
            # keep ship onscreen
            spaceship.x = max(0, min(spaceship.x, SCREEN_WIDTH - spaceship.width))

            # Player firing only when pressing Space
            if keys[pygame.K_SPACE]:
                spaceship.shoot()

            # Logic depends on whether we are transitioning between levels
            if level_transition_start > 0:
                # We are in transition (delay before next level)
                if pygame.time.get_ticks() - level_transition_start > 2000:
                    # Time to spawn new fleet
                    fleet = Fleet(ENEMY_COLS, ENEMY_ROWS, ENEMY_W, ENEMY_H, ENEMY_H_SPACING, ENEMY_V_SPACING, fleet_start_x, fleet_start_y, SCREEN_WIDTH)
                    
                    # Increase difficulty
                    new_interval = max(100, 600 - (level - 1) * 50)
                    fleet.step_interval = new_interval
                    
                    level_transition_start = 0
                else:
                    # Draw "Level X" message
                    lvl_font = pygame.font.SysFont(None, 100)
                    lvl_surf = lvl_font.render(f"LEVEL {level}", True, (255, 255, 0))
                    lvl_rect = lvl_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                    screen.blit(lvl_surf, lvl_rect)

            else:
                # Normal Gameplay Logic
                
                # Fleet movement/animation
                fleet.update()

                # Enemy shooting (choose bottom-most enemy in a random column)
                now = pygame.time.get_ticks()
                if now - last_enemy_shot > enemy_shot_interval:
                    shooter = fleet.pick_shooter()
                    if shooter:
                        bw, bh = 6, 14
                        bx = shooter.rect.x + shooter.rect.width // 2 - bw // 2
                        by = shooter.rect.bottom
                        enemy_bullets.append(pygame.Rect(bx, by, bw, bh))
                    last_enemy_shot = now

                # Update enemy bullets
                ship_rect = pygame.Rect(spaceship.x, spaceship.y, spaceship.width, spaceship.height)
                for b in enemy_bullets[:]:
                    b.y += enemy_bullet_speed
                    if b.y > SCREEN_HEIGHT:
                        enemy_bullets.remove(b)
                        continue
                    if b.colliderect(ship_rect):
                        # enemy hit should be lethal
                        spaceship.take_damage(100)
                        try:
                            enemy_bullets.remove(b)
                        except ValueError:
                            pass

                # Check player bullets vs enemies
                for bullet in spaceship.bullets[:]:
                    hit = fleet.hit_enemy(bullet)
                    if hit:
                        score += 10 * level  # Points increase with level
                        try:
                            spaceship.bullets.remove(bullet)
                        except ValueError:
                            pass
                
                # Check for level complete
                if not any(e.alive for e in fleet.all_enemies()):
                    level += 1
                    spaceship.bullets.clear()
                    enemy_bullets.clear()
                    level_transition_start = pygame.time.get_ticks()

            if spaceship.dead:
                game_state = "GAMEOVER"

            # Draw fleet and enemy bullets
            if level_transition_start == 0:
                fleet.draw(screen)
                for b in enemy_bullets:
                    pygame.draw.rect(screen, (255, 128, 0), b)

            # Draw player
            spaceship.draw_ship(screen)

            # Draw UI: lives, score, level
            font = pygame.font.SysFont(None, 36)
            lives_surf = font.render(f"Lives: {spaceship.lives}", True, (255, 255, 255))
            screen.blit(lives_surf, (10, SCREEN_HEIGHT - 40))
            
            score_surf = font.render(f"Score: {score}", True, (255, 255, 255))
            screen.blit(score_surf, (10, 10))
            
            level_surf = font.render(f"Level: {level}", True, (255, 255, 255))
            # align level to top right
            level_rect = level_surf.get_rect(topright=(SCREEN_WIDTH - 10, 10))
            screen.blit(level_surf, level_rect)

        elif game_state == "GAMEOVER":
            # Draw game state (static)
            fleet.draw(screen)
            for b in enemy_bullets:
                pygame.draw.rect(screen, (255, 128, 0), b)
            spaceship.draw_ship(screen)

            # Draw overlay
            go_font = pygame.font.SysFont(None, 120)
            go_surf = go_font.render("GAME OVER", True, (255, 0, 0))
            go_rect = go_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            screen.blit(go_surf, go_rect)
            
            info_font = pygame.font.SysFont(None, 36)
            info = info_font.render("Press R to restart or Q to Quit", True, (255, 255, 255))
            info_rect = info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
            screen.blit(info, info_rect)
            
            final_score = info_font.render(f"Final Score: {score}", True, (255, 255, 0))
            fs_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            screen.blit(final_score, fs_rect)
            
            if keys[pygame.K_r]:
                game_state = "PLAYING"
                spaceship.lives = 3
                spaceship.health = 100
                spaceship.dead = False
                spaceship.invulnerable = True
                spaceship.invulnerable_start = pygame.time.get_ticks()
                spaceship.x = spaceship.spawn_x
                spaceship.y = spaceship.spawn_y
                spaceship.bullets.clear()
                score = 0
                level = 1
                level_transition_start = 0
                fleet = Fleet(ENEMY_COLS, ENEMY_ROWS, ENEMY_W, ENEMY_H, ENEMY_H_SPACING, ENEMY_V_SPACING, fleet_start_x, fleet_start_y, SCREEN_WIDTH)
                enemy_bullets.clear()
            
            if keys[pygame.K_q]:
                running = False

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


def main() -> None:
    init_pygame()


if __name__ == "__main__":
    main()