import pygame

class Spaceship:
    def __init__(self, name: str, health: int, x: int, y: int) -> None:
        self.name = name
        self.health = health
        self.x = x
        self.y = y
        
        # Ship dimensions (used for math and drawing)
        self.width = 50
        self.height = 30
        
        # Bullet settings
        self.bullets = []  # List to hold bullet rectangles
        self.bullet_speed = 7
        self.last_shot_time = 0
        self.shoot_delay = 500  # Milliseconds between shots (increase to shoot slower)

    def take_damage(self, amount: int) -> None:
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def is_alive(self) -> bool:
        return self.health > 0
    
    def shoot(self):
        # Check current time
        current_time = pygame.time.get_ticks()
        
        # Only shoot if enough time has passed since the last shot
        if current_time - self.last_shot_time > self.shoot_delay:
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
        # Draw the ship
        pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.width, self.height))
        
        # Draw the bullets
        for bullet in self.bullets:
            pygame.draw.rect(screen, (255, 255, 0), bullet)
    

def init_pygame() -> None:
    pygame.init()
    
    # Define screen dimensions variables so we can use them in math
    SCREEN_WIDTH = 256
    SCREEN_HEIGHT = 224
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update game state
        spaceship.move()
        spaceship.shoot() # Called every frame for constant shooting

        screen.fill("black")

        spaceship.draw_ship(screen)

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


def main() -> None:
    init_pygame()


if __name__ == "__main__":
    main()