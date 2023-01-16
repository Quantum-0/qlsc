import asyncio
import socket
from asyncio import Queue
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
    SET_MODE = 0x31
    SET_PIXEL = 0x51
    SET_LINE = 0x52
    SET_GRADIENT = 0x53
    FILL = 0x54
    SET_LINE_IMAGE = 0x55
    SET_ALL_PIXELS = 0x56
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

    @property
    def length(self):
        return 42 # for test

    def __hash__(self):
        return hash(self.device_chip_id)

    def __eq__(self, other):
        return self.device_chip_id == other.device_chip_id and self.device_uuid == other.device_chip_id

    async def send_command(self, command_id: CommandID, data: bytes = b''):
        dev_id = pack('<L', int(self.device_chip_id, 16))
        packet = QLPPacket(dev_id + command_id + data, PacketType.CONTROL)
        await QLPEngine()._send_packet(packet)

    async def set_length(self, n: int):
        await self.send_command(CommandID.LENGTH, n.to_bytes(1, 'little', signed=False))

    async def set_pixel_color(self, index: int, color: Color):
        if not (0 <= index < self.length):
            raise IndexError()
        await self.send_command(CommandID.SET_PIXEL, index.to_bytes(2, 'little', signed=False) + bytes(color))

    async def set_line_color(self, start: int, end: int, color: Color):
        if not (0 <= start < end < self.length):
            raise IndexError()
        await self.send_command(CommandID.SET_LINE, start.to_bytes(2, 'little', signed=False) + end.to_bytes(2, 'little', signed=False) + bytes(color))

    async def fill(self, color: Color):
        await self.send_command(CommandID.FILL, bytes(color))

    async def reboot(self):
        await self.send_command(CommandID.REBOOT)


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


class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs) -> 'Singleton':
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class QLPError(Exception):
    pass


class QLPEngine(metaclass=Singleton):
    def __init__(self):
        self._listening: bool = False
        self._stop_listen: bool = False
        # self._received_packets_queue: Queue[QLPPacket] = Queue()
        self._devices: Set[QLSCDevice] = set()
        self._tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def start(self):
        if self._listening:
            raise QLPError('QLP Listener is already started')
        self._listening = True
        asyncio.create_task(self.__listening_loop())

    def stop(self):
        if not self._listening:
            raise QLPError('QLP Listener is already stopped')
        if self._stop_listen:
            raise QLPError('QLP Listener is already stopping')
        self._stop_listen = True

    async def __listening_loop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', __QLP_PORT__))
            sock.settimeout(0.2)
            while not self._stop_listen:
                try:
                    data, addr = sock.recvfrom(1024)
                    packet = QLPPacket.parse(data, source=addr[0])
                    print('Receiving packet', packet)
                    self.__handle_packet(packet)
                except (ValueError, socket.timeout):
                    continue
                finally:
                    await asyncio.sleep(0.1)
        self._stop_listen = False
        self._listening = False

    def __handle_packet(self, packet: QLPPacket):
        if packet.data[:3] == QLPDiscoveryPacket.I_AM_HERE:
            self._devices.add(
                QLSCDevice(
                    ip=packet.source,
                    device_chip_id=packet.data[4:12].decode(),
                    device_uuid=packet.data[13:21].decode(),
                    name=packet.data[22:].decode()
                )
            )

    async def _send_packet(self, packet: Union[QLPPacket, bytes]) -> None:
        serialized_packet = packet.serialize() if isinstance(packet, QLPPacket) else packet
        print('Sending packet', packet, serialized_packet.hex())
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(serialized_packet, ('255.255.255.255', __QLP_PORT__))

    async def discover_all_devices(self, timeout: float = 1.5) -> Set[QLSCDevice]:
        await self._send_packet(QLPPacket(QLPDiscoveryPacket.ANYBODY_HERE, PacketType.DISCOVERY))
        await asyncio.sleep(timeout)
        return self._devices


async def main():
    eng = QLPEngine()
    eng.start()
    # eng.start()
    await asyncio.sleep(1)
    devs = await eng.discover_all_devices()
    print(devs)
    d = list(devs)[0]
    await d.set_length(30)
    await asyncio.sleep(1)
    # await d.fill(Color(3, 1, 4))
    await asyncio.sleep(1)
    await d.set_pixel_color(5,Color(5,0,5))
    # await d.set_line_color(2,3,Color(5,5,5))
    # for i in range(500):
        # await d.set_pixel_color(i % 30, Color(i%5,i%6,i%7))
        # await asyncio.sleep(0.1)
        # await d.set_pixel_color(i % 30, Color(0,0,0))
        # await asyncio.sleep(0.02)
    await asyncio.sleep(5)
    await d.reboot()
    eng.stop()
    # eng.stop()


if __name__ == '__main__':
    asyncio.run(main())


# TODO:
#  - this will be protocol implementation
#  - make control panel - web ui, working with that protocol
