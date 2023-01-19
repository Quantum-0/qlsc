class Color:
    """Color structure implementation"""
    def __init__(self, r: int, g: int, b: int):
        assert 0 <= r < 256
        assert 0 <= g < 256
        assert 0 <= b < 256
        self.r = r
        self.g = g
        self.b = b

    @property
    def R(self):
        return self.r

    @property
    def G(self):
        return self.g

    @property
    def B(self):
        return self.b

    def __bytes__(self):
        return self.R.to_bytes(1, 'big') + self.G.to_bytes(1, 'big') + self.B.to_bytes(1, 'big')
