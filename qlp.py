import datetime
import socket
from dataclasses import dataclass
from enum import IntEnum
from struct import pack
from typing import NewType, Optional, Set, Union

__QLP_PORT__ = 52075
__PROTO_HEADER__ = b'QLP'
ProtoVer = NewType('ProtoVer', int)


class PacketType(IntEnum):
    NONE = 0
    DISCOVERY = 1
    BROADCAST = 2
    CONTROL = 3


class Color:
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


class QLPDiscoveryPacket:
    ANYBODY_HERE = b'ABH'
    I_AM_HERE = b'IAH'


class CommandID(IntEnum):
    LENGTH = 0x01
    FILL = 0x54
    REBOOT = 0x74

    @property
    def as_byte(self) -> bytes:
        return self.value.to_bytes(1, 'big')

    def __add__(self, other) -> bytes:
        assert isinstance(other, bytes)
        return self.as_byte + other

    def __radd__(self, other) -> bytes:
        assert isinstance(other, bytes)
        return other + self.as_byte

@dataclass
class QLSCDevice:
    ip: str
    device_chip_id: str
    device_uuid: str
    name: str

    def __hash__(self):
        return hash(self.device_chip_id)

    def __eq__(self, other):
        return self.device_chip_id == other.device_chip_id and self.device_uuid == other.device_chip_id

    def send_command(self, command_id: CommandID, data: bytes = b''):
        dev_id = pack('<L', int(self.device_chip_id, 16))
        packet = QLPPacket(dev_id + command_id.to_bytes(1, 'big') + data, PacketType.CONTROL)
        send_packet(packet)
        pass

    def set_length(self, n: int):
        self.send_command(CommandID.LENGTH, n.to_bytes(1, 'little', signed=False))

    def fill(self, r: int, g: int, b: int):
        self.send_command(CommandID.FILL, r.to_bytes(1, 'big')+g.to_bytes(1, 'big')+b.to_bytes(1, 'big'))

    def reboot(self):
        self.send_command(CommandID.REBOOT)

@dataclass
class QLPPacket:
    data: bytes
    packet_type: PacketType
    proto_version: ProtoVer = ProtoVer(1)
    # device_id: Optional[int] = None
    # broadcast_group: Optional[int] = None
    source: Optional[str] = None

    @property
    def crc(self) -> int:
        crc = 0x75
        for b in self.serialize(with_crc=False):
            crc ^= b
        return crc

    def serialize(self, *, with_crc: bool = True) -> bytes:
        return (
            __PROTO_HEADER__
            + self.proto_version.to_bytes(1, 'big')
            + self.packet_type.value.to_bytes(1, 'big')
            + self.data
            + (self.crc.to_bytes(1, 'big') if with_crc else b'')
        )

    @classmethod
    def parse(cls, data: bytes, source: Optional[str] = None):
        print('Parsing data', data)
        if data[:3] != __PROTO_HEADER__:
            raise ValueError('No header', data)
        proto_version = ProtoVer(int(data[3]))
        packet_type = PacketType(int(data[4]))
        content = data[5:-1]
        crc = data[-1]
        packet = QLPPacket(content, packet_type, proto_version, source)
        if packet.crc != crc:
            raise ValueError('Crc mismatch', data)
        return packet


def send_packet(packet: Union[QLPPacket, bytes]) -> None:
    print('Sending packet', packet, packet.serialize().hex())
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet.serialize() if isinstance(packet, QLPPacket) else packet, ('255.255.255.255', __QLP_PORT__))


def send_anybody_here():
    send_packet(QLPPacket(QLPDiscoveryPacket.ANYBODY_HERE, PacketType.DISCOVERY))


def listen(time: int):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        sock.bind(('', __QLP_PORT__))
        sock.settimeout(0.2)
        now = datetime.datetime.now()
        while (datetime.datetime.now() - now).total_seconds() < time:
            try:
                data, addr = sock.recvfrom(1024)
                packet = QLPPacket.parse(data, source=addr[0])
                print('Receiving packet', packet)
                yield packet
            except (ValueError, socket.timeout):
                continue
        return


def discover_all_devices(timeout: int = 3) -> Set[QLSCDevice]:
    send_anybody_here()
    return {
        QLSCDevice(resp.source, resp.data[4:12].decode(), resp.data[13:21].decode(), resp.data[22:].decode())
        for resp in listen(timeout)
        if resp.data[:3] == QLPDiscoveryPacket.I_AM_HERE
    }


def test():
    my_controller = list(discover_all_devices(timeout=2))[0]
    my_controller.set_length(30)
    my_controller.fill(3, 1, 4)
