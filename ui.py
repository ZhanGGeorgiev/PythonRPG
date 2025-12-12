import pygame
import math
from settings import COLORS, PANEL_WIDTH, FONT_SIZE
from items import Coins

BOX_SIZE = 40
BOX_PADDING = 5

class UI:
    """Handles all on-screen rendering."""
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        # Use dynamic dimensions from the screen surface
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.font = pygame.font.SysFont('Arial', FONT_SIZE)
        self.small_font = pygame.font.SysFont('Arial', 14)
        
        self.panel_rect = pygame.Rect(self.width - PANEL_WIDTH, 0, PANEL_WIDTH, self.height)
        self.hex_center = (self.width - PANEL_WIDTH // 2, 150)
        self.hex_radius = 60
        self.messages = []

        self.pile_rects = []
        self.player_rects = []

    def draw(self, fight_instance=None):
        pygame.draw.rect(self.screen, (30, 30, 30), self.panel_rect)
        pygame.draw.line(self.screen, COLORS["WHITE"], (self.width - PANEL_WIDTH, 0), (self.width - PANEL_WIDTH, self.height))

        self.draw_text(f"HP: {self.player.health}", self.width - PANEL_WIDTH + 10, 10, COLORS["RED"])
        self.draw_text(f"STR: {self.player.strength}", self.width - PANEL_WIDTH + 100, 10, COLORS["BLUE"])
        
        coin_item = self.find_coins()
        money = coin_item.price if coin_item else 0
        self.draw_text(f"Gold: {money}", self.width - PANEL_WIDTH + 10, 35, COLORS["GOLD"])

        self.draw_combat_hex(fight_instance)
        self.draw_inventory_sidebar(300)
        self.draw_messages(self.height - 200)
        self.draw_hotbar()

    def draw_hotbar(self):
        game_view_width = self.width - PANEL_WIDTH
        start_x = (game_view_width // 2) - ((BOX_SIZE + BOX_PADDING) * 2.5)
        start_y = self.height - BOX_SIZE - 20

        for i in range(5):
            x = start_x + i * (BOX_SIZE + BOX_PADDING)
            box_rect = pygame.Rect(x, start_y, BOX_SIZE, BOX_SIZE)
            
            pygame.draw.rect(self.screen, COLORS["DARK_GREY"], box_rect)
            pygame.draw.rect(self.screen, COLORS["WHITE"], box_rect, 1)

            # Draw Number
            num_txt = self.small_font.render(str(i+1), True, (200, 200, 200))
            self.screen.blit(num_txt, (x + 2, start_y + 2))

            item = self.player.hotbar[i]
            if item:
                if item not in self.player.items:
                    self.player.hotbar[i] = None
                    continue
                self.draw_item_symbol(item, box_rect)

    def draw_item_symbol(self, item, rect):
        color = item.color
        if hasattr(item, 'equipped') and item.equipped:
            color = COLORS["PURPLE"]
        txt = self.font.render(item.symbol, True, color)
        text_rect = txt.get_rect(center=rect.center)
        self.screen.blit(txt, text_rect)

    def draw_loot_interface(self, loot_container, name="CONTAINER"):
        self.draw_overlay()
        self.draw_text(f"{name} (Left-Click to Take, 'T' to close)", 50, 50, COLORS["GREEN"])
        self.pile_rects = self.draw_item_grid(loot_container.items, 50, 80, 10) 

        self.draw_text("YOUR BAG (Right-Click to Drop)", 50, 300, COLORS["BLUE"])
        self.player_rects = self.draw_item_grid(self.player.items, 50, 330, 10)

    def draw_equip_menu(self):
        self.draw_overlay()
        self.draw_text("INVENTORY (Hover+1-5: Hotbar, Left: Equip, Right: Drop)", 50, 50, COLORS["WHITE"])
        self.player_rects = self.draw_item_grid(self.player.items, 50, 100, 10)

    def draw_overlay(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(COLORS["BLACK"])
        self.screen.blit(overlay, (0, 0))

    def draw_item_grid(self, items, start_x, start_y, cols):
        rect_list = []
        for i, item in enumerate(items):
            row = i // cols
            col = i % cols
            x = start_x + col * (BOX_SIZE + BOX_PADDING)
            y = start_y + row * (BOX_SIZE + BOX_PADDING)
            
            box_rect = pygame.Rect(x, y, BOX_SIZE, BOX_SIZE)
            pygame.draw.rect(self.screen, COLORS["DARK_GREY"], box_rect)
            pygame.draw.rect(self.screen, COLORS["WHITE"], box_rect, 1)
            self.draw_item_symbol(item, box_rect)
            
            rect_list.append((box_rect, item, i))
        return rect_list

    def draw_tooltip(self, item, mouse_pos):
        mx, my = mouse_pos
        lines = [f"{item.name}"]
        if item.damage > 0: lines.append(f"Damage: {item.damage}")
        if item.protection > 0: lines.append(f"Armor: {item.protection}")
        if hasattr(item, 'price'): lines.append(f"Value: {item.price}")
        
        width = 0
        height = len(lines) * 20 + 10
        for line in lines:
            w = self.small_font.size(line)[0]
            if w > width: width = w
        width += 20
        
        rect = pygame.Rect(mx + 15, my + 15, width, height)
        # Bounds check
        if rect.right > self.width: rect.x -= width + 30
        if rect.bottom > self.height: rect.y -= height + 30
        
        pygame.draw.rect(self.screen, COLORS["DARK_BLUE_BG"], rect)
        pygame.draw.rect(self.screen, COLORS["WHITE"], rect, 1)
        
        y = rect.y + 5
        for line in lines:
            txt = self.small_font.render(line, True, COLORS["WHITE"])
            self.screen.blit(txt, (rect.x + 10, y))
            y += 20

    def draw_text(self, text, x, y, color=COLORS["WHITE"]):
        surf = self.font.render(text, True, color)
        self.screen.blit(surf, (x, y))

    def draw_combat_hex(self, fight):
        cx, cy = self.hex_center
        radius = self.hex_radius
        colors = [COLORS["WHITE"]] * 5
        if fight:
            colors = fight.get_arrow_colors(self.player)

        start_angle = -math.pi / 2 
        step = (2 * math.pi) / 5
        for i in range(5):
            angle = start_angle + (i * step)
            ex = cx + math.cos(angle) * radius
            ey = cy + math.sin(angle) * radius
            pygame.draw.line(self.screen, colors[i], (cx, cy), (ex, ey), 4)
            pygame.draw.circle(self.screen, colors[i], (int(ex), int(ey)), 5)

    def draw_inventory_sidebar(self, start_y):
        self.draw_text("EQUIPPED:", self.width - PANEL_WIDTH + 10, start_y, COLORS["GREEN"])
        y = start_y + 25
        if self.player.weapon:
            w = self.player.weapon[0]
            self.draw_text(f"Wpn: {w.name}", self.width - PANEL_WIDTH + 10, y, COLORS["PURPLE"])
        else:
            self.draw_text("Wpn: Fists", self.width - PANEL_WIDTH + 10, y, COLORS["GREY"])
        y += 20
        self.draw_text(f"Armor Pcs: {len(self.player.armor)}", self.width - PANEL_WIDTH + 10, y, COLORS["PURPLE"])

    def draw_messages(self, start_y):
        y = start_y
        for msg, color in self.messages[-8:]: 
            self.draw_text(msg, self.width - PANEL_WIDTH + 10, y, color)
            y += 20

    def add_message(self, text, color=COLORS["WHITE"]):
        self.messages.append((text, color))
        if len(self.messages) > 15:
            self.messages.pop(0)

    def find_coins(self):
        for item in self.player.items:
            if isinstance(item, Coins):
                return item
        return None

    def get_mouse_direction(self):
        mx, my = pygame.mouse.get_pos()
        cx, cy = self.hex_center
        if mx < (self.width - PANEL_WIDTH): return 5 
        dx = mx - cx
        dy = my - cy
        angle = math.atan2(dy, dx)
        if angle < 0: angle += 2 * math.pi
        sector = (2 * math.pi) / 5
        adjusted_angle = angle + (math.pi / 2) + (sector / 2)
        if adjusted_angle < 0: adjusted_angle += 2 * math.pi
        if adjusted_angle > 2 * math.pi: adjusted_angle -= 2 * math.pi
        index = int(adjusted_angle / sector)
        return index % 5