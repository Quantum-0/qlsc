from utils.byte_serializable import OneByteSerializableEnum


# pylint: disable=too-few-public-methods
class CommonResponseCode(OneByteSerializableEnum):
    """Quantum0's LED Strip Controller's Protocol's common response code enum"""
    OK = 0x00
    VERSION_ERROR = 0x01
    CRC_ERROR = 0x02
    ENCRYPTION_ERROR = 0x03
    LENGTH_ERROR = 0x04
    # RESERVED: 0x05-0xFE
    OTHER_ERROR = 0xFF  # should contain text
