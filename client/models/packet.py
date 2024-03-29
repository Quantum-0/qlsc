import logging
from dataclasses import dataclass, field
from typing import NewType, Optional, ClassVar

# from enums.commands import CommandID
from enums.packet_type import PacketType
# from exceptions.protocol_exceptions import QLPError

__PROTO_HEADER__ = b'QLP'
ProtoVer = NewType('ProtoVer', int)

logger = logging.getLogger('Packet')


@dataclass
class QLPPacket:
    """Wrapper for raw bytes packet allowing to write or read serialized data from it and also checking crc"""
    data: bytes
    packet_type: PacketType
    proto_version: ProtoVer = field(default=ProtoVer(1), repr=False)
    source: Optional[str] = None
    packet_counter: ClassVar[int] = 0
    packet_id: Optional[int] = field(default=None, repr=False)

    device_id: Optional[str] = None
    # broadcast_group: Optional[int] = None

    def __post_init__(self):
        self.packet_id = self.packet_id or self.__class__.packet_counter
        self.__class__.packet_counter += 1
        # TODO: check command here

    # TODO:
    # @property
    # def command_id(self):
    #     if self.packet_type in (PacketType.CONTROL, PacketType.BROADCAST):
    #         return CommandID(self.data[...])
    #     raise QLPError()

    @property
    def crc(self) -> int:
        crc = 0x75
        for byte in self.serialize(with_crc=False):
            crc ^= byte
        return crc

    def serialize(self, *, with_crc: bool = True) -> bytes:
        return (
            __PROTO_HEADER__
            + self.proto_version.to_bytes(1, 'big')
            + self.packet_type.value.to_bytes(1, 'big')
            # TODO: NOT IMPLEMENTED ON FIRMWARE YET:
            #  + (self.packet_counter.to_bytes(1, 'big') if self.packet_type == PacketType.CONTROL else b'')
            #  + b''  # TODO: Receiver???
            + self.data
            + (self.crc.to_bytes(1, 'big') if with_crc else b'')
        )

    @classmethod
    def parse(cls, data: bytes, source: Optional[str] = None):
        if data[:3] != __PROTO_HEADER__:
            raise ValueError('No header', data)
        proto_version = ProtoVer(int(data[3]))
        packet_type = PacketType(int(data[4]))
        packet_id = int(data[5]) if packet_type == PacketType.CONTROL else None
        content = data[5:-1] if packet_type != PacketType.CONTROL else data[6:-1]
        crc = data[-1]
        packet = QLPPacket(content, packet_type, proto_version, source, packet_id=packet_id)
        if packet.crc != crc:
            raise ValueError('Crc mismatch', data)
        return packet
