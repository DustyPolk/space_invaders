import pygame
import random
from src.constants import *
from src.entities import Spaceship, Fleet

def run_game() -> None:
    """
    Initializes Pygame, sets up the game state, and runs the main game loop.
    Handles events, updates game logic, and renders the scene.
    """
    pygame.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"Space Invaders — {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
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

    # --- ENEMY FLEET SETUP ---
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
            title_surf = title_font.render("SPACE INVADERS", True, COLOR_GREEN)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
            screen.blit(title_surf, title_rect)

            instr_font = pygame.font.SysFont(None, 48)
            instr_surf = instr_font.render("Press SPACE to Start", True, COLOR_WHITE)
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
                    lvl_surf = lvl_font.render(f"LEVEL {level}", True, COLOR_YELLOW)
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
                        bw, bh = ENEMY_BULLET_WIDTH, ENEMY_BULLET_HEIGHT
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
                    pygame.draw.rect(screen, COLOR_ORANGE, b)

            # Draw player
            spaceship.draw_ship(screen)

            # Draw UI: lives, score, level
            font = pygame.font.SysFont(None, 36)
            lives_surf = font.render(f"Lives: {spaceship.lives}", True, COLOR_WHITE)
            screen.blit(lives_surf, (10, SCREEN_HEIGHT - 40))
            
            score_surf = font.render(f"Score: {score}", True, COLOR_WHITE)
            screen.blit(score_surf, (10, 10))
            
            level_surf = font.render(f"Level: {level}", True, COLOR_WHITE)
            # align level to top right
            level_rect = level_surf.get_rect(topright=(SCREEN_WIDTH - 10, 10))
            screen.blit(level_surf, level_rect)

        elif game_state == "GAMEOVER":
            # Draw game state (static)
            fleet.draw(screen)
            for b in enemy_bullets:
                pygame.draw.rect(screen, COLOR_ORANGE, b)
            spaceship.draw_ship(screen)

            # Draw overlay
            go_font = pygame.font.SysFont(None, 120)
            go_surf = go_font.render("GAME OVER", True, COLOR_RED)
            go_rect = go_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            screen.blit(go_surf, go_rect)
            
            info_font = pygame.font.SysFont(None, 36)
            info = info_font.render("Press R to restart or Q to Quit", True, COLOR_WHITE)
            info_rect = info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
            screen.blit(info, info_rect)
            
            final_score = info_font.render(f"Final Score: {score}", True, COLOR_YELLOW)
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
