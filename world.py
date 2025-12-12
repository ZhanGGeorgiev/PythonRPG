import random
from typing import List, Optional, Tuple
from settings import COLORS, MAP_WIDTH, MAP_HEIGHT

class Block:
    def __init__(self, symbol: str, priority: int = 9, passable: bool = True, color: tuple = COLORS["WHITE"]):
        self.symbol = symbol
        self.priority = priority
        self.passable = passable
        self.color = color

    def __str__(self):
        return self.symbol

class Plain(Block):
    def __init__(self): super().__init__('.', color=COLORS["GREEN"])

class Wall(Block):
    def __init__(self): super().__init__('#', 1, False, color=COLORS["GREY"])

class Door(Block):
    def __init__(self): super().__init__('[', 2, True, color=COLORS["BROWN"])

class Tree(Block):
    def __init__(self, cord): super().__init__('o', 1, False, color=COLORS["TREE_GREEN"])

class ForestBlock(Block):
    def __init__(self, cord): super().__init__('F', 2, True, color=COLORS["FOREST_GREEN"])

class ForestDirt(Block):
    def __init__(self): super().__init__(' ', 5, True)

class Village(Block):
    def __init__(self, cord, houses):
        super().__init__('V', 1, True, color=COLORS["BROWN"])
        self.cord = cord
        self.houses = houses

class Chest(Block):
    def __init__(self, cord):
        super().__init__('C', 2, True, color=COLORS["GOLD"])
        self.cord = cord
        self.items = []

class ItemsPile(Block):
    def __init__(self, cord):
        super().__init__('P', 2, True, color=COLORS["GOLD"])
        self.cord = cord
        self.items = []

def cord_to_x_y(width: int, cord: int) -> Tuple[int, int]:
    return (cord % width, (cord - cord % width) // width)

class Map:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.entities = []
        self.events = []
        self.map_list = []
        self._init_grid()

    def _init_grid(self):
        for _ in range(self.width * self.height):
            self.map_list.append([Plain()])

    def add_object(self, obj, x: int = None, y: int = None):
        if x is not None and y is not None:
            cord = x + y * self.width
        elif hasattr(obj, 'cord'):
            cord = obj.cord
        else:
            return

        block_stack = self.map_list[cord]
        # Insert based on priority
        index = len(block_stack)
        for i, existing_obj in enumerate(block_stack):
            if existing_obj.priority < obj.priority:
                index = i
                break
        block_stack.insert(index, obj)

    def add_entity(self, entity, x: int, y: int):
        self.add_object(entity, x=x, y=y)
        self.entities.append(entity)

    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
        
        cord = self.width * entity.y + entity.x
        if entity in self.map_list[cord]:
            self.map_list[cord].remove(entity)

    def remove_object_at(self, x: int, y: int, cls_type):
        obj = self.get_object_at(x, y, cls_type)
        if obj:
            self.map_list[x + y * self.width].remove(obj)

    def get_object_at(self, x: int, y: int, cls_type):
        if not self.check_cords(x, y): return None
        for obj in self.map_list[x + y * self.width]:
            if isinstance(obj, cls_type):
                return obj
        return None

    def is_passable(self, x: int, y: int) -> bool:
        if not self.check_cords(x, y): return False
        for block in self.map_list[x + y * self.width]:
            if hasattr(block, "passable") and not block.passable:
                return False
        return True

    def check_cords(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

class WorldMap(Map):
    def generate(self):
        # Generate Forests
        for _ in range(15):
            start_cord = random.randint(0, self.width * self.height - 1)
            ForestGenerator.grow(self, start_cord, 10)
        # Generate Villages
        for _ in range(5):
            cord = random.randint(0, self.width * self.height - 1)
            self.add_object(Village(cord, random.randint(2, 4)), x=None, y=None) # Village has cord inside

class Location(Map):
    def __init__(self, biome_blocks):
        super().__init__(50, 30)
        self.biome_blocks = biome_blocks
        self.priority = 10
        self.symbol = "L"
        self.passable = True
        self.generate()

    def generate(self):
        from entities import Goblin, Ghost 
        
        generated_biome = False
        for biome in self.biome_blocks:
            if isinstance(biome, Village):
                self.generate_village(biome)
                generated_biome = True
                break
            elif isinstance(biome, (ForestBlock, ForestDirt)):
                self.generate_forest()
                generated_biome = True
                break
        
        if not generated_biome:
            self.generate_forest()

        # Add Monsters
        for _ in range(random.randint(3, 8)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.is_passable(x, y) and (x > 5 or y > 5):
                monster = random.choice([Goblin, Ghost])(x, y, self)
                self.add_entity(monster, x, y)

    def generate_village(self, village_biome):
        from entities import Human
        from items import Potion, Sword
        
        for _ in range(village_biome.houses):
            w = random.randint(3, 6)
            h = random.randint(3, 6)
            x = random.randint(1, self.width - w - 2)
            y = random.randint(1, self.height - h - 2)
            
            for i in range(x, x + w + 1):
                self.add_object(Wall(), x=i, y=y)
                self.add_object(Wall(), x=i, y=y + h)
            for j in range(y, y + h + 1):
                self.add_object(Wall(), x=x, y=j)
                self.add_object(Wall(), x=x + w, y=j)

            door_x, door_y = x + w // 2, y + h
            self.remove_object_at(door_x, door_y, Wall)
            self.add_object(Door(), x=door_x, y=door_y)

            cx, cy = x + w // 2, y + h // 2
            self.add_entity(Human(cx, cy, self), cx, cy)
            
            chest = Chest(0)
            chest.items.append(Potion('Health Potion', 0, 50, False)) # Example item
            self.add_object(chest, x=x+1, y=y+1)

    def generate_forest(self):
        for cord in range(self.width * self.height):
            x, y = cord_to_x_y(self.width, cord)
            if x < 3 and y < 3: continue
            
            if random.random() > 0.85:
                self.add_object(Tree(cord), x=x, y=y)

class ForestGenerator:
    @staticmethod
    def grow(map_obj, start_cord, decay):
        if decay >= 100: return
        x, y = cord_to_x_y(map_obj.width, start_cord)
        if not map_obj.check_cords(x, y): return
        
        if not map_obj.get_object_at(x, y, ForestBlock):
            map_obj.add_object(ForestBlock(start_cord), x=x, y=y)
            decay_step = 15
            
            neighbors = [1, -1, map_obj.width, -map_obj.width]
            for offset in neighbors:
                if random.randint(0, 100) > decay:
                    ForestGenerator.grow(map_obj, start_cord + offset, decay + decay_step)