from math import hypot

class Vector2:
    def __init__(self, x=0, y=0):
        self.x = float(x)
        self.y = float(y)

    def add(self, v):
        return Vector2(self.x + v.x, self.y + v.y)

    def sub(self, v):
        return Vector2(self.x - v.x, self.y - v.y)

    def mul(self, s):
        return Vector2(self.x * s, self.y * s)

    def length(self):
        return hypot(self.x, self.y)

    def normalized(self):
        l = self.length()
        if l == 0:
            return Vector2()
        return Vector2(self.x / l, self.y / l)

    def limit(self, max_len):
        l = self.length()
        if l == 0 or l <= max_len:
            return Vector2(self.x, self.y)
        return self.normalized().mul(max_len)
