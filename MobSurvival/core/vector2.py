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

    def div(self, s):
        if s == 0:
            return Vector2(self.x, self.y)
        return Vector2(self.x / s, self.y / s)

    def length(self):
        return hypot(self.x, self.y)

    def length_sq(self):
        return self.x * self.x + self.y * self.y

    def normalized(self):
        l = self.length()
        if l == 0:
            return Vector2()
        return Vector2(self.x / l, self.y / l)

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def perp(self):
        return Vector2(-self.y, self.x)

    def limit(self, max_len):
        l = self.length()
        if l == 0 or l <= max_len:
            return Vector2(self.x, self.y)
        return self.normalized().mul(max_len)
