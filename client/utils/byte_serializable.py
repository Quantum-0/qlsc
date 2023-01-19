import abc
from enum import IntEnum


class ByteSerializable():
    @abc.abstractmethod
    def __bytes__(self) -> bytes:
        raise NotImplementedError('Must be implemented for that class')

    def __add__(self, other) -> bytes:
        if isinstance(other, bytes):
            return bytes(self) + other
        if isinstance(other, ByteSerializable):
            return bytes(self) + bytes(other)
        raise ValueError(f'Object {other} is not {self.__class__.__name__}')

    def __radd__(self, other) -> bytes:
        if isinstance(other, bytes):
            return other + bytes(self)
        if isinstance(other, ByteSerializable):
            return bytes(other) + bytes(self)
        raise ValueError(f'Object {other} is not {self.__class__.__name__}')


class OneByteSerializableEnum(ByteSerializable, IntEnum):
    def __bytes__(self) -> bytes:
        return self.value.to_bytes(1, 'big')
