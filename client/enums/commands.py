from utils.byte_serializable import OneByteSerializableEnum


class CommandID(OneByteSerializableEnum):
    LENGTH = 0x01
    SET_MODE = 0x31
    SET_PIXEL = 0x51
    SET_LINE = 0x52
    SET_GRADIENT = 0x53
    FILL = 0x54
    SET_LINE_IMAGE = 0x55
    SET_ALL_PIXELS = 0x56
    REBOOT = 0x74
