import pygame
import sys
from settings import TILE_SIZE, COLORS, FPS, PANEL_WIDTH
from player import Player
from world import WorldMap, Location, Chest, Village, ForestBlock, Plain, ForestDirt, ItemsPile
from ui import UI
from texts import show_start_screen, show_game_over, show_happy_ending
from gamestates import RoamingState, CombatState, LootState, InventoryState

class SymbolRenderer:
    def __init__(self, font):
        self.font = font
        self.cache = {}

    def get_surface(self, symbol, color):
        key = (symbol, color)
        if key not in self.cache:
            self.cache[key] = self.font.render(symbol, True, color)
        return self.cache[key]

class Game:
    def __init__(self):
        pygame.init()

        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), 
            pygame.FULLSCREEN
        )
  
        pygame.display.set_caption("Retro Python RPG")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.map_font = pygame.font.SysFont('Arial', 20)
        self.renderer = SymbolRenderer(self.map_font)

        self.world_map = WorldMap(52, 33)
        self.world_map.generate()
        
        self.current_map = self.world_map
        self.player = Player(0, 0, self.current_map)
        self.current_map.add_entity(self.player, 0, 0)
        
        self.ui = UI(self.screen, self.player)
        
        self.view_w = (self.screen_width - PANEL_WIDTH) // TILE_SIZE 
        self.view_h = self.screen_height // TILE_SIZE

        self.last_world_pos = (0, 0)
        self.last_move = 0

        self.state = RoamingState(self)

        show_start_screen(self.screen)

    def change_state(self, new_state):
        self.state = new_state

    def run(self):
        while self.running:
            self.current_time = pygame.time.get_ticks()

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                     self.running = False

            self.state.handle_input(events)
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def select_target_at_mouse(self, mx, my):
        cam_x = max(0, min(self.player.x - self.view_w // 2, self.current_map.width - self.view_w))
        cam_y = max(0, min(self.player.y - self.view_h // 2, self.current_map.height - self.view_h))
        
        click_map_x = int((mx - 10) / TILE_SIZE) + cam_x
        click_map_y = int((my - 10) / TILE_SIZE) + cam_y
        
        for entity in self.current_map.entities:
            if entity.x == click_map_x and entity.y == click_map_y:
                if hasattr(entity, 'is_player') and not entity.is_player:
                    self.player.target = entity
                    self.ui.add_message(f"Target: {entity.symbol}", COLORS["GREEN"])
                    return

    def try_move(self, dx, dy):
        target_x = self.player.x + dx
        target_y = self.player.y + dy
        
        if self.current_map.is_passable(target_x, target_y):
            self.current_map.remove_entity(self.player)
            self.player.x = target_x
            self.player.y = target_y
            self.current_map.add_entity(self.player, target_x, target_y)

    def interact_loot(self):
        chest = self.current_map.get_object_at(self.player.x, self.player.y, Chest)
        if chest:
            self.change_state(LootState(self, chest))
            return
        loot_pile = self.current_map.get_object_at(self.player.x, self.player.y, ItemsPile)
        if loot_pile:
            self.change_state(LootState(self, loot_pile))
            return

    def interact_environment(self):
        if not isinstance(self.current_map, Location):
            existing_location = self.current_map.get_object_at(self.player.x, self.player.y, Location)
            if existing_location:
                self.enter_location(existing_location)
                return
                
            terrain_obj = None
            stack = self.current_map.map_list[self.player.cord]
            for obj in reversed(stack):
                if isinstance(obj, (Village, ForestBlock, Plain, ForestDirt)):
                    terrain_obj = obj
                    break
            
            if terrain_obj:
                self.ui.add_message("Entering new area...")
                new_location = Location([terrain_obj])
                self.current_map.add_object(new_location, x=self.player.x, y=self.player.y)
                self.enter_location(new_location)
                return

        if isinstance(self.current_map, Location):
            self.current_map.remove_entity(self.player)
            self.current_map = self.world_map
            self.player.map = self.world_map
            self.player.x, self.player.y = self.last_world_pos
            self.current_map.add_entity(self.player, self.player.x, self.player.y)
            return

    def enter_location(self, location_obj):
        self.last_world_pos = (self.player.x, self.player.y)
        self.current_map.remove_entity(self.player)
        self.current_map = location_obj
        self.player.map = location_obj
        self.player.x, self.player.y = 1, 1
        self.current_map.add_entity(self.player, 1, 1)

    def update(self):
        if not self.player.alive:
            show_game_over(self.screen)
            self.running = False
            return

        for item in self.player.items:
            if hasattr(item, 'price') and item.name == 'coins' and item.price >= 10000:
                show_happy_ending(self.screen)
                self.running = False
                return

        for entity in self.current_map.entities:
            if hasattr(entity, 'update'):
                entity.update(self.current_time, self.player)

        self.state.update()

    def draw_world_only(self):
        self.screen.fill(COLORS["BLACK"])
        
        cam_x = max(0, min(self.player.x - self.view_w // 2, self.current_map.width - self.view_w))
        cam_y = max(0, min(self.player.y - self.view_h // 2, self.current_map.height - self.view_h))
        
        for y in range(cam_y, min(cam_y + self.view_h, self.current_map.height)):
            for x in range(cam_x, min(cam_x + self.view_w, self.current_map.width)):
                
                screen_x = (x - cam_x) * TILE_SIZE + 10
                screen_y = (y - cam_y) * TILE_SIZE + 10
                
                if self.current_map.check_cords(x, y):
                    stack = self.current_map.map_list[x + y * self.current_map.width]
                    if stack:
                        top_obj = stack[-1]
                        if isinstance(top_obj, Location):
                            if len(stack) > 1: top_obj = stack[-2]
                            else: continue

                        color = getattr(top_obj, 'color', COLORS["WHITE"])
                        if str(top_obj) == '@': color = COLORS["WHITE"]
                        elif str(top_obj) == 'G': color = COLORS["RED"]
                        
                        if hasattr(self.player, 'target') and top_obj == self.player.target:
                            pygame.draw.rect(self.screen, (50, 0, 0), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

                        text = self.renderer.get_surface(str(top_obj), color)
                        self.screen.blit(text, (screen_x, screen_y))

    def draw(self):
        self.state.draw()
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()