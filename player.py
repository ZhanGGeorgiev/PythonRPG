import pygame
from entities import LivingEntity
from items import Sword, Helmet, BreastPlate, Leggings, Potion, Coins

class Player(LivingEntity):
    def __init__(self, x, y, map_obj):
        super().__init__(x, y, '@', map_obj, 30, 5)
        
        self.is_player = True 
        self.vision = 20
        self.hit_cooldown = 200 
        
        self.base_strength = 5
        self.base_defense = 0 
        
        self.hotbar = [None] * 5 

    def add_item(self, new_item):
        if isinstance(new_item, Coins):
            for item in self.items:
                if isinstance(item, Coins):
                    item.price += new_item.price
                    return 
        self.items.append(new_item)

    def trigger_hotbar(self, slot_index):
        if 0 <= slot_index < 5:
            item = self.hotbar[slot_index]
            
            # Validation: Do we actually still have this item?
            if item and item in self.items:
                self.equip_item(item)
            elif item:
                # Item no longer in inventory (dropped/sold), clear slot
                self.hotbar[slot_index] = None
                print("Hotbar slot cleared (item missing)")

    def equip_item(self, item):
        if isinstance(item, Sword):
            for w in self.weapon:
                w.equipped = False
            self.weapon = [item]
            item.equipped = True
            print(f"Equipped {item.name}")

        elif isinstance(item, (Helmet, BreastPlate, Leggings)):
            for a in self.armor[:]:
                if type(a) == type(item):
                    a.equipped = False
                    self.armor.remove(a)
            
            self.armor.append(item)
            item.equipped = True
            print(f"Equipped {item.name}")
        
        elif isinstance(item, Potion):
            self.health = min(30, self.health + 10) 
            self.items.remove(item)
            # Potions are consumed, so remove from hotbar if present
            if item in self.hotbar:
                idx = self.hotbar.index(item)
                self.hotbar[idx] = None
            print("Used Potion")
            
        self.recalculate_stats()

    def recalculate_stats(self):
        self.strength = self.base_strength
        for w in self.weapon:
            if w.equipped:
                self.strength += w.damage

    def get_out_of_fight(self):
        if self.fight:
            self.in_fight = False
            self.fight.remove_entity(self)
            self.fight.check_active() 
            self.fight = None