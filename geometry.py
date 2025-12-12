import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_cords(self):
        return (self.x, self.y)

class Triangle:
    def __init__(self, point1, point2, point3):
        self.point1 = point1
        self.point2 = point2
        self.point3 = point3
        self.area = 0
        self.calculate_area()

    def calculate_area(self):
        """Calculates area using the coordinate geometry formula."""
        x1, y1 = self.point1.get_cords()
        x2, y2 = self.point2.get_cords()
        x3, y3 = self.point3.get_cords()
        
        self.area = abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2

def get_sin(angle):
    return math.sin(angle)

def get_cos(angle):
    return math.cos(angle)