from utils.byte_serializable import OneByteSerializableEnum


# pylint: disable=too-few-public-methods
class CommandID(OneByteSerializableEnum):
    """Quantum0's LED Strip Controller's Protocol's commands enum"""

    # Category #1: Settings
    LENGTH = 0x01
    MAX_CURRENT = 0x02
    # RESERVED 0x03-0x0F

    # Category #2: Internal Network
    SET_MASTER = 0x11
    GET_MASTER = 0x12
    SYNC_PACKET = 0x13
    MULTICAST_GROUP = 0x14
    RESPONSE_MULTICAST_GROUP = 0x15
    # RESERVED 0x16-0x2F

    # Category #3: High-level control
    SET_MODE = 0x31
    SET_COLOR = 0x32
    SET_SPEED = 0x33
    SET_BRIGHTNESS = 0x34
    SET_SHIFT = 0x35
    SET_SHAPE = 0x36
    SET_PARAM1 = 0x37
    SET_PARAM2 = 0x38
    # RESERVED 0x39-0x4F

    # Category #4: Low-level control
    SET_PIXEL = 0x51
    SET_LINE = 0x52
    SET_GRADIENT = 0x53
    FILL = 0x54
    SET_LINE_IMAGE = 0x55
    SET_ALL_PIXELS = 0x56
    # RESERVED 0x57-0x6F

    # Category #5: Service
    ENCRYPTION = 0x71
    VERSION = 0x72
    RESET_ID = 0x73
    REBOOT = 0x74
    FULL_RESET = 0x75
    # RESERVED 0x76-0x7F

    # Category #6: Time control
    TIME_SERVER = 0x81
    SET_TIME = 0x82
    SET_TIMER = 0x83
    GET_TIMER = 0x84
    # RESERVED 0x85-0x8F

    # Category #7: Response
    COMMON_RESPONSE = 0x90
    # RESERVED FOR MORE CATEGORIES AND COMMANDS 0x91-0xFF
