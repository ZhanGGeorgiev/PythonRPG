import pygame
import random
from path_find import seek_path
from items import Sword, Helmet, Leggings, BreastPlate, Potion, Coins
from settings import COLORS
# --- FIX: IMPORT FROM WORLD, NOT BLOCKS ---
from world import ItemsPile 
# ------------------------------------------

class LivingEntity:
    """Base class for any moving actor in the game (Player, NPCs)."""
    def __init__(self, x: int, y: int, symbol: str, map_obj, health: int, strength: int):
        self.x = x
        self.y = y
        self.symbol = symbol
        self.map = map_obj
        self.health = health
        self.strength = strength
        self.alive = True
        self.color = COLORS["WHITE"]
        
        self.items = []
        self.weapon = []
        self.armor = []
        
        self.target = None
        self.in_fight = False
        self.fight = None
        self.last_hit_time = 0
        self.hit_cooldown = 1000

        self.priority = 0
        self.passable = False

    def get_damage(self, damage: int, attacker=None):
        self.health -= damage
        
        if attacker and hasattr(self, 'attitude') and self.alive:
            if self.attitude == 'passive':
                self.attitude = 'aggressive'
            self.target = attacker

        if self.health <= 0:
            self.die()

    def die(self):
        self.alive = False
        self.map.remove_entity(self)
        
        if self.fight:
            self.fight.remove_entity(self)
        
        # Drop Loot
        if self.items:
            existing_pile = self.map.get_object_at(self.x, self.y, ItemsPile)
            if existing_pile:
                existing_pile.items.extend(self.items)
            else:
                cord = self.map.width * self.y + self.x
                new_pile = ItemsPile(cord)
                new_pile.items.extend(self.items)
                self.map.add_object(new_pile, x=self.x, y=self.y)
        
        for entity in self.map.entities:
            if hasattr(entity, 'target') and entity.target == self:
                entity.target = None

    @property 
    def cord(self):
        return self.map.width * self.y + self.x

    @property
    def can_hit(self):
        return pygame.time.get_ticks() > self.last_hit_time + self.hit_cooldown
    
    def __str__(self):
        return self.symbol

class Player(LivingEntity):
    def __init__(self, x, y, map_obj):
        super().__init__(x, y, '@', map_obj, health=30, strength=5)
        self.is_player = True 
        self.vision = 20
        self.hit_cooldown = 200 
        self.base_strength = 5
        self.hotbar = [None] * 5 

    def add_item(self, new_item):
        if isinstance(new_item, Coins):
            for item in self.items:
                if isinstance(item, Coins):
                    item.price += new_item.price
                    return 
        self.items.append(new_item)

    def trigger_hotbar(self, slot_index: int):
        if 0 <= slot_index < 5:
            item = self.hotbar[slot_index]
            if item and item in self.items:
                self.equip_item(item)
            elif item:
                self.hotbar[slot_index] = None

    def equip_item(self, item):
        if isinstance(item, Sword):
            for w in self.weapon: w.equipped = False
            self.weapon = [item]
            item.equipped = True
        
        elif isinstance(item, (Helmet, BreastPlate, Leggings)):
            for a in self.armor[:]:
                if type(a) == type(item):
                    a.equipped = False
                    self.armor.remove(a)
            self.armor.append(item)
            item.equipped = True
        
        elif isinstance(item, Potion):
            self.health = min(30, self.health + 10) 
            self.items.remove(item)
            if item in self.hotbar:
                self.hotbar[self.hotbar.index(item)] = None
            
        self.recalculate_stats()

    def recalculate_stats(self):
        self.strength = self.base_strength
        for w in self.weapon:
            if w.equipped:
                self.strength += w.damage

class NPC(LivingEntity):
    def __init__(self, x, y, symbol, attitude, map_obj, vision, strength, health, weapon, armor):
        super().__init__(x, y, symbol, map_obj, health, strength)
        self.attitude = attitude
        self.vision = vision
        self.is_player = False
        
        self.weapon = weapon if weapon else []
        self.armor = armor if armor else []
        self.items.extend(self.weapon)
        self.items.extend(self.armor)

        self.movement_cooldown = 1000
        self.last_moved = 0
        self.path_cooldown = 2000
        self.last_path_calc = 0
        self.path = []
        self.hit_cooldown = 2000 
        self.change_direction_time = 1500
        self.last_direction_change = 0
        
        self.move_ai = MoveAI(self)
        self.behave_ai = BehaveAI(self)

    def update(self, current_time, player):
        self.behave_ai.process(current_time, player)

    def make_step(self, current_time):
        self.last_moved = current_time
        new_x, new_y = self.move_ai.get_next_step(current_time)
        self.map.remove_entity(self)
        self.x, self.y = new_x, new_y
        self.map.add_entity(self, self.x, self.y)

    def start_fight(self, target):
        self.in_fight = True
        self.target = target
        target.in_fight = True

    def can_change_direction(self, current_time):
        return current_time > self.change_direction_time + self.last_direction_change

    @property
    def can_move(self):
        return pygame.time.get_ticks() > self.last_moved + self.movement_cooldown

    def sees_player(self, player):
        dist_x = abs(self.x - player.x)
        dist_y = abs(self.y - player.y)
        return dist_x <= self.vision and dist_y <= self.vision

class BehaveAI:
    def __init__(self, entity):
        self.entity = entity
    
    def process(self, current_time, player):
        dist_x = abs(self.entity.x - player.x)
        dist_y = abs(self.entity.y - player.y)
        is_adjacent = (dist_x <= 1 and dist_y <= 1)
        
        if not is_adjacent and not self.entity.in_fight and self.entity.attitude == 'aggressive':
             if dist_x + dist_y < 4:
                 self.entity.start_fight(player)
        
        if self.entity.can_move:
            should_move = False
            if not self.entity.in_fight:
                should_move = True
            elif self.entity.in_fight and not is_adjacent:
                should_move = True
            
            if should_move:
                self.entity.target = player
                self.entity.make_step(current_time)

class MoveAI:
    def __init__(self, entity):
        self.entity = entity
        
    def get_next_step(self, current_time):
        target = self.entity.target
        if self.entity.attitude == 'aggressive' and target:
            if self.entity.sees_player(target):
                if current_time > self.entity.last_path_calc + self.entity.path_cooldown:
                    self.entity.last_path_calc = current_time
                    self.entity.path = seek_path(self.entity, target.x, target.y)

                if self.entity.path:
                    next_node = self.entity.path.pop(0)
                    if self.entity.map.is_passable(next_node[0], next_node[1]):
                        return next_node
        return self._wander()
        
    def _wander(self):
        dx = random.randint(-1, 1)
        dy = random.randint(-1, 1)
        new_x = self.entity.x + dx
        new_y = self.entity.y + dy
        if self.entity.map.check_cords(new_x, new_y) and self.entity.map.is_passable(new_x, new_y):
            return (new_x, new_y)
        return (self.entity.x, self.entity.y)

class Goblin(NPC):
    def __init__(self, x, y, map_obj):
        gear = []
        if random.random() > 0.5:
            gear.append(Sword('Rusty Sword', 3, 10, False))
        super().__init__(x, y, 'G', 'aggressive', map_obj, 10, 2, 25, gear, [])
        self.color = COLORS["RED"]

class Ghost(NPC):
    def __init__(self, x, y, map_obj):
        super().__init__(x, y, '?', 'aggressive', map_obj, 15, 1, 15, [], [])
        self.color = COLORS["GREY"]

class Human(NPC):
    def __init__(self, x, y, map_obj):
        super().__init__(x, y, 'H', 'passive', map_obj, 5, 1, 10, [], [])
        self.color = COLORS["WHITE"]