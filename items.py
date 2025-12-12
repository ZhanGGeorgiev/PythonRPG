from typing import Optional
from settings import COLORS

class Item:
    """Base class for all collectable items."""
    def __init__(self, name: str, damage: int, protection: int, price: int, symbol: str, equipped: bool = False):
        self.name = name
        self.damage = damage
        self.protection = protection
        self.price = price
        self.symbol = symbol
        self.equipped = equipped
        self.color = COLORS["WHITE"]
        
        if self.equipped:
            self.color = COLORS["PURPLE"]

    def __str__(self):
        return self.symbol

class Potion(Item):
    def __init__(self, name: str, protection: int = 0, price: int = 10, equipped: bool = False):
        super().__init__(name, 0, 0, price, '6', equipped)

class Equipment(Item):
    """Base class for wearable items."""
    def __init__(self, name: str, protection: int, price: int, symbol: str, equipped: bool):
        super().__init__(name, 0, protection, price, symbol, equipped)

class Helmet(Equipment):
    def __init__(self, name: str, protection: int, price: int, equipped: bool):
        super().__init__(name, protection, price, 'H', equipped)

class BreastPlate(Equipment):
    def __init__(self, name: str, protection: int, price: int, equipped: bool):
        super().__init__(name, protection, price, 'B', equipped)

class Leggings(Equipment):
    def __init__(self, name: str, protection: int, price: int, equipped: bool):
        super().__init__(name, protection, price, 'L', equipped)

class Sword(Item):
    def __init__(self, name: str, damage: int, price: int, equipped: bool):
        super().__init__(name, damage, 0, price, 'S', equipped)

class Coins(Item):
    def __init__(self, name: str, price: int):
        super().__init__(name, 0, 0, price, 'c', False)
        self.color = COLORS["GOLD"]