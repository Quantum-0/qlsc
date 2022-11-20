import datetime
import socket
from dataclasses import dataclass
from enum import IntEnum
from typing import NewType, List, Optional

QLPVer = NewType('QLPVer', int)

class QLPPacketType(IntEnum):
    DISCOVERY = 1
    BROADCAST = 2
    CONTROL = 3


class QLPDiscoveryPacket:
    ANYBODY_HERE = b'ABH'
    I_AM_HERE = b'IAH'


@dataclass
class QLSCDevice:
    ip: str
    name: str

@dataclass
class QLPPacket:
    data: bytes
    packet_type: QLPPacketType
    proto_version: QLPVer = QLPVer(1)
    source: Optional[str] = None

    @property
    def crc(self):
        return calc_crc(b'QLP' + self.proto_version.to_bytes(1, 'big') + self.packet_type.value.to_bytes(1, 'big') + self.data)

    def serialize(self):
        data = b'QLP' + self.proto_version.to_bytes(1, 'big') + self.packet_type.value.to_bytes(1, 'big') + self.data
        data += calc_crc(data).to_bytes(1, 'big')
        return data

    @classmethod
    def parse(cls, data: bytes, source: Optional[str] = None):
        print(data)
        if data[:3] != b'QLP':
            raise ValueError('No header', data)
        print('>>', data)
        proto_version = QLPVer(int(data[3]))
        print('>>>', data)
        packet_type = QLPPacketType(int(data[4]))
        # content = data[5:-1]
        content = data[5:]
        # crc = data[-1]
        packet = QLPPacket(content, packet_type, proto_version, source)
        print(packet)
        # if packet.crc != crc:
        #     raise ValueError('Crc mismatch', data)
        return packet

# low level

__QLP_PORT__ = 52075


def calc_crc(data: bytes) -> int:
    crc = 0x75
    for b in data:
        crc ^= b
    return crc


# def send_raw(data: bytes, add_crc: bool):
#     if add_crc:
#         data += calc_crc(data).to_bytes(1, 'big')
#     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
#         sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#         sock.sendto(data, ("255.255.255.255", __QLP_PORT__))


# def send_packet(data: bytes, packet_type: QLPPacketType, proto_ver: QLPVer = QLPVer(1)):
#     packet = b'QLP' + proto_ver.to_bytes(1, 'big') + packet_type.value.to_bytes(1, 'big') + data
#     send_raw(packet, add_crc=True)


def send_packet(packet: QLPPacket) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet.serialize(), ("255.255.255.255", __QLP_PORT__))


def send_anybody_here():
    # send_packet(QLPDiscoveryPacket.ANYBODY_HERE, packet_type=QLPPacketType.DISCOVERY)
    send_packet(QLPPacket(QLPDiscoveryPacket.ANYBODY_HERE, QLPPacketType.DISCOVERY))


def listen(time: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(("", __QLP_PORT__))
    sock.settimeout(0.2)
    now = datetime.datetime.now()
    responses = []
    while (datetime.datetime.now() - now).total_seconds() < time:
        try:
            data, addr = sock.recvfrom(1024)
        except socket.timeout:
            continue
        else:
            print(f'[{addr}]: {data}')
            responses.append((addr[0], data))
    dto_responses = []
    for resp in responses:
        try:
            packet = QLPPacket.parse(resp[1], source=resp[0])
            print(packet)
            dto_responses.append(packet)
        except:
            pass


    #responses = [QLPPacket.parse(data, source=ip) for (ip, data) in responses]
    return dto_responses


def discover_all_devices() -> List[QLSCDevice]:
    send_anybody_here()
    responses = listen(3)
    print(responses)
    return [QLSCDevice(resp.source, '') for resp in responses if resp.data == QLPDiscoveryPacket.I_AM_HERE]
