import pygame
from settings import COLORS, PANEL_WIDTH
from combat import Fight
# --- FIX: Import from world, not blocks ---
from world import ItemsPile, Chest
# ------------------------------------------

class GameState:
    def __init__(self, game):
        self.game = game
    def handle_input(self, events): pass
    def update(self): pass
    def draw(self): pass

class LootState(GameState):
    def __init__(self, game, container):
        super().__init__(game)
        self.container = container 
        self.hovered_item = None

    def handle_input(self, events):
        self.hovered_item = None 
        mx, my = pygame.mouse.get_pos()

        if hasattr(self.game.ui, 'pile_rects'):
            for rect, item, idx in self.game.ui.pile_rects:
                if rect.collidepoint(mx, my): self.hovered_item = item
        
        if hasattr(self.game.ui, 'player_rects'):
            for rect, item, idx in self.game.ui.player_rects:
                if rect.collidepoint(mx, my): self.hovered_item = item

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_t, pygame.K_e, pygame.K_ESCAPE]:
                    self.close_loot()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # LEFT CLICK: Take
                if event.button == 1: 
                    if hasattr(self.game.ui, 'pile_rects'):
                        for rect, item, index in self.game.ui.pile_rects:
                            if rect.collidepoint(mx, my):
                                self.game.player.add_item(item)
                                self.container.items.remove(item)
                                return 

                # RIGHT CLICK: Drop into Container
                if event.button == 3:
                    if hasattr(self.game.ui, 'player_rects'):
                        for rect, item, index in self.game.ui.player_rects:
                            if rect.collidepoint(mx, my):
                                if item.equipped:
                                    self.game.ui.add_message("Unequip first!")
                                    return
                                self.container.items.append(item)
                                self.game.player.items.remove(item)
                                return

    def close_loot(self):
        if isinstance(self.container, ItemsPile) and not self.container.items:
            self.game.current_map.remove_object_at(self.game.player.x, self.game.player.y, ItemsPile)
        self.game.change_state(RoamingState(self.game))

    def update(self): pass

    def draw(self):
        self.game.draw_world_only()
        name = "CHEST" if isinstance(self.container, Chest) else "LOOT PILE"
        self.game.ui.draw_loot_interface(self.container, name)
        if self.hovered_item:
            self.game.ui.draw_tooltip(self.hovered_item, pygame.mouse.get_pos())

class InventoryState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.hovered_item = None

    def handle_input(self, events):
        self.hovered_item = None
        mx, my = pygame.mouse.get_pos()
        
        if hasattr(self.game.ui, 'player_rects'):
            for rect, item, idx in self.game.ui.player_rects:
                if rect.collidepoint(mx, my): self.hovered_item = item

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_i, pygame.K_ESCAPE]:
                    self.game.change_state(RoamingState(self.game))
                
                if self.hovered_item:
                    slot = -1
                    if event.key == pygame.K_1: slot = 0
                    elif event.key == pygame.K_2: slot = 1
                    elif event.key == pygame.K_3: slot = 2
                    elif event.key == pygame.K_4: slot = 3
                    elif event.key == pygame.K_5: slot = 4
                    
                    if slot != -1:
                        self.game.player.hotbar[slot] = self.hovered_item
                        self.game.ui.add_message(f"Added to Hotbar {slot+1}", COLORS["GREEN"])
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if hasattr(self.game.ui, 'player_rects'):
                    for rect, item, index in self.game.ui.player_rects:
                        if rect.collidepoint(mx, my):
                            if event.button == 1:
                                self.game.player.equip_item(item)
                            elif event.button == 3:
                                self.drop_item(item)

    def drop_item(self, item):
        if item.equipped:
            self.game.ui.add_message("Cannot drop equipped item!")
            return
        
        pile = self.game.current_map.get_object_at(self.game.player.x, self.game.player.y, ItemsPile)
        if not pile:
            pile = ItemsPile(self.game.player.cord)
            self.game.current_map.add_object(pile, x=self.game.player.x, y=self.game.player.y)
        
        pile.items.append(item)
        self.game.player.items.remove(item)
        self.game.ui.add_message(f"Dropped {item.name}")

    def update(self): pass

    def draw(self):
        self.game.draw_world_only()
        self.game.ui.draw_equip_menu()
        if self.hovered_item:
            self.game.ui.draw_tooltip(self.hovered_item, pygame.mouse.get_pos())

class RoamingState(GameState):
    def handle_input(self, events):
        keys = pygame.key.get_pressed()
        move_delay = 100 
        
        if self.game.current_time - self.game.last_move > move_delay:
            dx, dy = 0, 0
            if keys[pygame.K_w]: dy = -1
            elif keys[pygame.K_s]: dy = 1
            elif keys[pygame.K_a]: dx = -1
            elif keys[pygame.K_d]: dx = 1
            
            if dx != 0 or dy != 0:
                self.game.try_move(dx, dy)
                self.game.last_move = self.game.current_time

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e: self.game.interact_environment()
                if event.key == pygame.K_t: self.game.interact_loot()
                if event.key == pygame.K_i: self.game.change_state(InventoryState(self.game))
                
                if event.key == pygame.K_1: self.game.player.trigger_hotbar(0)
                if event.key == pygame.K_2: self.game.player.trigger_hotbar(1)
                if event.key == pygame.K_3: self.game.player.trigger_hotbar(2)
                if event.key == pygame.K_4: self.game.player.trigger_hotbar(3)
                if event.key == pygame.K_5: self.game.player.trigger_hotbar(4)

                if event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                    self.game.last_move = 0 

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if mx < self.game.screen_width - PANEL_WIDTH:
                        self.game.select_target_at_mouse(mx, my)

    def update(self):
        if self.game.player.in_fight:
            self.game.change_state(CombatState(self.game))
    
    def draw(self):
        self.game.draw_world_only()
        self.game.ui.draw()

class CombatState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.fight = Fight(game.current_map, game.ui, game.player)
        self.game.player.fight = self.fight
        
        # Track enemies found to select best target
        enemies_in_range = []
        
        for entity in game.current_map.entities:
            is_hostile = False
            if hasattr(entity, 'attitude') and entity.attitude == 'aggressive':
                is_hostile = True
            if hasattr(entity, 'target') and entity.target == game.player:
                is_hostile = True
            if hasattr(entity, 'attitude') and entity.attitude == 'passive':
                is_hostile = False
            
            if is_hostile:
                dist_x = abs(entity.x - game.player.x)
                dist_y = abs(entity.y - game.player.y)
                if dist_x <= 10 and dist_y <= 10:
                    self.fight.add_party(entity)
                    enemies_in_range.append(entity)
        
        if enemies_in_range:
            game.ui.add_message(f"Combat started!", COLORS["RED"])
            
            if not game.player.target or game.player.target not in enemies_in_range:
                # Pick nearest
                enemies_in_range.sort(key=lambda e: abs(e.x - game.player.x) + abs(e.y - game.player.y))
                game.player.target = enemies_in_range[0]
                game.ui.add_message(f"Auto-target: {game.player.target.symbol}", COLORS["GREEN"])
        else:
            game.player.in_fight = False
            game.change_state(RoamingState(game))

    def handle_input(self, events):
        direction = self.game.ui.get_mouse_direction()
        if direction != 5:
            self.fight.update_player_direction(direction, self.game.player)

        keys = pygame.key.get_pressed()
        move_delay = 100 
        if self.game.current_time - self.game.last_move > move_delay:
            dx, dy = 0, 0
            if keys[pygame.K_w]: dy = -1
            elif keys[pygame.K_s]: dy = 1
            elif keys[pygame.K_a]: dx = -1
            elif keys[pygame.K_d]: dx = 1
            if dx != 0 or dy != 0:
                self.game.try_move(dx, dy)
                self.game.last_move = self.game.current_time

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if mx < self.game.screen_width - PANEL_WIDTH:
                        self.game.select_target_at_mouse(mx, my)
                    else:
                        self.fight.player_try_hit(self.game.player, self.game.current_time)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e: self.game.interact_environment()
                
                if event.key == pygame.K_1: self.game.player.trigger_hotbar(0)
                if event.key == pygame.K_2: self.game.player.trigger_hotbar(1)
                if event.key == pygame.K_3: self.game.player.trigger_hotbar(2)
                if event.key == pygame.K_4: self.game.player.trigger_hotbar(3)
                if event.key == pygame.K_5: self.game.player.trigger_hotbar(4)

    def update(self):
        self.fight.update_distances(self.game.player)
        self.fight.npc_ai_logic(self.game.current_time)
        for event in self.game.current_map.events[:]:
            if event.process(self.game.current_time):
                self.game.current_map.events.remove(event)

        if len(self.fight.party) <= 1:
            self.game.player.in_fight = False
            self.game.player.fight = None
            self.game.change_state(RoamingState(self.game))
            self.game.ui.add_message("Combat Ended", COLORS["GREEN"])
            
    def draw(self):
        self.game.draw_world_only()
        self.game.ui.draw(self.fight)