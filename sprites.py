import pygame

# 1 = draw, 0 = skip
# 11x8 grid example
ALIEN_A_1 = [
    "00100000100",
    "00010001000",
    "00111111100",
    "01101110110",
    "11111111111",
    "10111111101",
    "10100000101",
    "00011011000"
]

ALIEN_A_2 = [
    "00100000100",
    "10010001001",
    "10111111101",
    "11101110111",
    "11111111111",
    "01111111110",
    "00100000100",
    "01000000010"
]

# Player Ship 13x8
PLAYER_SHIP = [
    "0000001000000",
    "0000011100000",
    "0000011100000",
    "0111111111110",
    "1111111111111",
    "1111111111111",
    "1111111111111",
    "1111111111111"
]

def draw_pixel_sprite(screen: pygame.Surface, pattern: list[str], x: int, y: int, w: int, h: int, color: tuple[int, int, int]):
    """
    Draws a sprite based on a string pattern.
    Scales the 'pixels' to fit the destination w/h.
    """
    rows = len(pattern)
    cols = len(pattern[0])
    
    pixel_w = w / cols
    pixel_h = h / rows
    
    for r, row_str in enumerate(pattern):
        for c, char in enumerate(row_str):
            if char == '1':
                px = x + c * pixel_w
                py = y + r * pixel_h
                # Draw slightly larger to avoid gaps or exact
                pygame.draw.rect(screen, color, (px, py, pixel_w + 1, pixel_h + 1))
