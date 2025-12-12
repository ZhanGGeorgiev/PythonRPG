import random
import pygame
from settings import COLORS, HIT_CHANCE, DIRECTION_CHANGE_CHANCE, HIT_DELAY_MS, GLOBAL_COOLDOWN_MS
from items import Sword, Helmet, BreastPlate, Leggings

class Fight:
    """Manages combat logic between player and entities."""
    def __init__(self, map_obj, ui_panel, *party):
        self.map = map_obj
        self.ui_panel = ui_panel 
        self.party = list(party)
        self.directions = {} # Entity -> Int (0-4)
        self.set_directions()
        self.next_allowed_enemy_attack = 0

    def add_party(self, entity):
        if entity not in self.party:
            self.party.append(entity)
            self.directions[entity] = random.randint(0, 4)
            entity.fight = self
    
    def remove_entity(self, entity):
        if entity in self.party:
            self.party.remove(entity)
            if entity in self.directions:
                del self.directions[entity]
            
            # Reset state
            entity.in_fight = False
            entity.target = None
            entity.fight = None

        self.check_active()

    def update_distances(self, player):
        """Removes entities that wander too far during combat."""
        for entity in self.party[:]: 
            if entity == player: continue
            
            if entity.map != player.map:
                self.remove_entity(entity)
                continue

            dist_x = abs(entity.x - player.x)
            dist_y = abs(entity.y - player.y)
            if dist_x > 10 or dist_y > 10:
                self.remove_entity(entity)

    def set_directions(self):
        for entity in self.party:
            if hasattr(entity, 'is_player') and entity.is_player:
                self.directions[entity] = 0
            else:
                self.directions[entity] = random.randint(0, 4)

    def update_player_direction(self, direction_index: int, player):
        if direction_index != 5: 
            self.directions[player] = direction_index

    def player_try_hit(self, player, current_time: int):
        if not player.target: 
            self.ui_panel.add_message("No target!", COLORS["GREY"])
            return
        
        dist_x = abs(player.x - player.target.x)
        dist_y = abs(player.y - player.target.y)
        if dist_x > 1 or dist_y > 1:
            self.ui_panel.add_message("Target too far!", COLORS["GREY"])
            return

        if player.can_hit:
            player.last_hit_time = current_time
            self.map.events.append(
                Hit(self, player, player.target, HIT_DELAY_MS, current_time, self.ui_panel)
            )
            self.ui_panel.add_message("You swing...", COLORS["WHITE"])

    def npc_ai_logic(self, current_time: int):
        for entity in self.party:
            if hasattr(entity, 'is_player') and entity.is_player:
                continue
            
            # Random Direction Change
            if entity.can_change_direction(current_time):
                if random.randint(0, 50) < DIRECTION_CHANGE_CHANCE: 
                    entity.last_direction_change = current_time
                    self.directions[entity] = random.randint(0, 4)
            
            # Attack Logic
            if current_time > self.next_allowed_enemy_attack:
                if entity.can_hit:
                    if random.randint(0, 50) < HIT_CHANCE: 
                        target = entity.target
                        if target:
                            dist_x = abs(entity.x - target.x)
                            dist_y = abs(entity.y - target.y)
                            if dist_x <= 1 and dist_y <= 1:
                                entity.last_hit_time = current_time
                                self.map.events.append(
                                    Hit(self, entity, target, HIT_DELAY_MS, current_time, self.ui_panel)
                                )
                                self.next_allowed_enemy_attack = current_time + GLOBAL_COOLDOWN_MS
                                break 

    def check_active(self):
        if len(self.party) <= 1:
            for entity in self.party:
                entity.in_fight = False
                entity.target = None
                entity.fight = None
            self.party.clear()

    def get_arrow_colors(self, player):
        colors = [COLORS["WHITE"]] * 5
        
        for entity, direction in self.directions.items():
            if direction >= 5: continue
            if entity != player:
                if entity == player.target:
                    colors[direction] = COLORS["BRIGHT_RED"]
                else:
                    colors[direction] = COLORS["RED"]
        
        if player in self.directions:
            p_dir = self.directions[player]
            if p_dir < 5:
                if colors[p_dir] == COLORS["RED"] or colors[p_dir] == COLORS["BRIGHT_RED"]:
                    colors[p_dir] = COLORS["PURPLE"] # Blocked
                else:
                    colors[p_dir] = COLORS["BLUE"] # Clear
        return colors

class Hit:
    """Represents a pending attack event."""
    def __init__(self, fight, attacker, defender, delay, created_time, ui_panel):
        self.fight = fight
        self.attacker = attacker
        self.defender = defender
        self.delay = delay
        self.created_time = created_time
        self.ui_panel = ui_panel

    def process(self, current_time: int) -> bool:
        """Returns True if the hit is finished and should be removed."""
        if self.created_time + self.delay < current_time:
            self.resolve_damage()
            return True
        return False

    def resolve_damage(self):
        if not self.attacker or not self.defender: return
        if self.attacker not in self.fight.directions or self.defender not in self.fight.directions: return

        att_dir = self.fight.directions.get(self.attacker, 0)
        def_dir = self.fight.directions.get(self.defender, 0)

        if att_dir == def_dir:
            self.ui_panel.add_message(f"{self.defender.symbol} BLOCKED {self.attacker.symbol}!", COLORS["PURPLE"])
            return

        damage = self.attacker.strength
        weapon = self.get_equipped_item(self.attacker, Sword)
        if weapon: damage += weapon.damage

        # Armor Logic
        armor = None
        if att_dir == 0: armor = self.get_equipped_item(self.defender, Helmet)
        elif att_dir in [1, 4]: armor = self.get_equipped_item(self.defender, BreastPlate)
        elif att_dir in [2, 3]: armor = self.get_equipped_item(self.defender, Leggings)

        if armor: damage -= armor.protection

        damage = max(0, damage)
        
        if damage > 0:
            self.defender.get_damage(damage, attacker=self.attacker)
            self.ui_panel.add_message(f"{self.attacker.symbol} hit {self.defender.symbol} for {damage}", COLORS["RED"])
        else:
            self.ui_panel.add_message(f"{self.attacker.symbol} hit armor (0 dmg)", COLORS["GREY"])

    def get_equipped_item(self, entity, item_type):
        source = entity.weapon if item_type == Sword else entity.armor
        for item in source:
            if isinstance(item, item_type):
                return item
        return None