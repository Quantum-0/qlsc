import datetime
import socket
from dataclasses import dataclass
from enum import IntEnum
from typing import NewType, Optional, Set, Union

__QLP_PORT__ = 52075
__PROTO_HEADER__ = b'QLP'
ProtoVer = NewType('ProtoVer', int)


class PacketType(IntEnum):
    NONE = 0
    DISCOVERY = 1
    BROADCAST = 2
    CONTROL = 3


class QLPDiscoveryPacket:
    ANYBODY_HERE = b'ABH'
    I_AM_HERE = b'IAH'


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

    def send_command(self, some_args):
        # generate packet with received=device_id
        pass


@dataclass
class QLPPacket:
    data: bytes
    packet_type: PacketType
    proto_version: ProtoVer = ProtoVer(1)
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
        # content = data[5:-1]
        # crc = data[-1]
        content = data[5:]
        packet = QLPPacket(content, packet_type, proto_version, source)
        # if packet.crc != crc:
        # raise ValueError('Crc mismatch', data)
        return packet


def send_packet(packet: Union[QLPPacket, bytes]) -> None:
    print('Sending packet', packet)
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
