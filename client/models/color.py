from typing import Self


class Color:
    """Color structure implementation"""
    def __init__(self, red: int, green: int, blue: int) -> None:
        if not 0 <= red < 256 or not 0 <= green < 256 or not 0 <= blue < 256:
            raise ValueError('Invalid channels values for Color structure')
        self.red = red
        self.green = green
        self.blue = blue

    @property
    def R(self) -> int:  # noqa pylint: disable=invalid-name
        return self.red

    @property
    def G(self) -> int:  # noqa pylint: disable=invalid-name
        return self.green

    @property
    def B(self)-> int:  # noqa pylint: disable=invalid-name
        return self.blue

    @classmethod
    def from_HSV(cls, hue: int, saturation: int, value: int) -> Self:  # pylint: disable=invalid-name
        # TODO
        raise NotImplementedError()

    def __bytes__(self) -> bytes:
        return self.R.to_bytes(1, 'big') + self.G.to_bytes(1, 'big') + self.B.to_bytes(1, 'big')
