import pygame
from settings import COLORS

pygame.font.init()

TEXT_FONT = pygame.font.SysFont('Arial', 20)
NORMAL_FONT = pygame.font.Font(None, 36)
TITLE_FONT = pygame.font.SysFont('Arial', 150)

def draw_centered_text(surface, text, font, color):
    """Helper to center text on screen."""
    text_surface = font.render(text, True, color)
    size = font.size(text)
    
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    
    x = (screen_width - size[0]) // 2
    y = (screen_height - size[1]) // 2
    
    surface.blit(text_surface, (x, y))

def show_start_screen(surface):
    surface.fill(COLORS["BLACK"])
    draw_centered_text(surface, 'WELCOME PLAYER', TITLE_FONT, COLORS["WHITE"])
    pygame.display.flip()
    pygame.time.delay(1000)

def show_game_over(surface):
    surface.fill(COLORS["BLACK"])
    draw_centered_text(surface, 'YOU DIED', TITLE_FONT, COLORS["RED"])
    pygame.display.flip()
    pygame.time.delay(2000)

def show_happy_ending(surface):
    surface.fill(COLORS["BLACK"])
    draw_centered_text(surface, 'Well Done', TITLE_FONT, COLORS["WHITE"])
    pygame.display.flip()
    pygame.time.delay(2000)