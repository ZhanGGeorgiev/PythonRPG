"""
Configuration settings and constants for the game.
"""

# Screen Settings
TILE_SIZE = 25

MAP_WIDTH = 52
MAP_HEIGHT = 33
PANEL_WIDTH = 250
FPS = 60
FONT_SIZE = 20


COLORS = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "RED": (125, 0, 0),
    "BRIGHT_RED": (255, 0, 0),
    "GREEN": (0, 125, 0),
    "BRIGHT_GREEN": (0, 255, 0),
    "BLUE": (0, 0, 125),
    "PURPLE": (50, 0, 50),
    "GOLD": (255, 215, 0),
    "GREY": (100, 100, 100),
    "DARK_GREY": (50, 50, 50),
    "BROWN": (139, 69, 19),
    "FOREST_GREEN": (34, 139, 34),
    "TREE_GREEN": (0, 255, 0),
    "DARK_BLUE_BG": (20, 20, 40)
}


HIT_CHANCE = 1
DIRECTION_CHANGE_CHANCE = 1
HIT_DELAY_MS = 800
GLOBAL_COOLDOWN_MS = 1200