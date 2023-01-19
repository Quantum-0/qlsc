from utils.byte_serializable import OneByteSerializableEnum


class PacketType(OneByteSerializableEnum):
    """Quantum0's LED Strip Protocol's Type"""
    NONE = 0
    DISCOVERY = 1
    BROADCAST = 2
    CONTROL = 3
