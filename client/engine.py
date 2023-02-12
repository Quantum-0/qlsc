import asyncio
import logging
import socket
from typing import Set, Union

import enums.discovery_packet_body as dpb
from enums.packet_type import PacketType
from exceptions.protocol_exceptions import QLPError
from models.device import QLSCDevice
from models.packet import QLPPacket
from utils.singleton import Singleton

logger = logging.getLogger('Engine')

class QLPEngine(metaclass=Singleton):
    """Engine for Quantum0's LED Strip Protocol, allows to interact with devices"""
    __QLP_PORT__ = 52075

    # TODO: Add something kinda request_response list
    #  Цель:
    #   - функция отправки команды девайсу должна дождаться ответа или упасть с таймаут еррором
    #   - несколько таймаут ерроров - удаляем девайс из списка
    #   - если девайсу была отправлена команда - лочить выполнение следующей отправки пока предыдущая не будет завершена
    #     dict[device_id, lock] ?
    #   - НЕ лочить параллельную отправку двум или более девайсам
    #   - добавить в протокол байт - счетчик команды

    def __init__(self):
        self._listening: bool = False
        self._stop_listen: bool = False
        # self._received_packets_queue: Queue[QLPPacket] = Queue()
        self._devices: Set[QLSCDevice] = set()
        self._tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__just_send_packet = None
        logger.debug('Engine was created')

    def start(self):
        if self._listening:
            raise QLPError('QLP Listener is already started')
        self._listening = True
        asyncio.create_task(self.__listening_loop())
        logger.info('Engine was started')

    def stop(self):
        if not self._listening:
            raise QLPError('QLP Listener is already stopped')
        if self._stop_listen:
            raise QLPError('QLP Listener is already stopping')
        self._stop_listen = True
        logger.info('Request to stop')

    async def __listening_loop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', self.__QLP_PORT__))
            sock.settimeout(0.2)
            while not self._stop_listen:
                try:
                    data, addr = sock.recvfrom(1024)
                    if data == self.__just_send_packet:
                        continue
                    packet = QLPPacket.parse(data, source=addr[0])
                    logger.info('<<<< RX: {}'.format(data.hex(' ').upper()))
                    logger.debug('Receiving packet: {}'.format(packet))
                    self.__handle_packet(packet)
                except (ValueError, socket.timeout):
                    continue
                finally:
                    await asyncio.sleep(0.1)
        self._stop_listen = False
        self._listening = False
        logger.info('Engine was stopped')

    def __handle_packet(self, packet: QLPPacket):
        if packet.data[:3] == dpb.I_AM_HERE:
            new_dev = QLSCDevice(
                    ip=packet.source,
                    device_chip_id=packet.data[4:12].decode(),
                    device_uuid=packet.data[13:21].decode(),
                    name=packet.data[22:].decode(),
                    _engine=self,
                )
            self._devices.add(new_dev)

    async def _send_packet(self, packet: Union[QLPPacket, bytes]) -> None:
        serialized_packet = packet.serialize() if isinstance(packet, QLPPacket) else packet
        logger.info('>>>> TX: {}'.format(serialized_packet.hex(' ').upper()))
        logger.debug('Sending packet: {}'.format(str(packet)))
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(serialized_packet, ('255.255.255.255', self.__QLP_PORT__))
            self.__just_send_packet = serialized_packet

    async def discover_all_devices(self, timeout: float = 1.5) -> Set[QLSCDevice]:
        logger.debug('Search for devices...')
        await self._send_packet(QLPPacket(dpb.ANYBODY_HERE, PacketType.DISCOVERY))
        await asyncio.sleep(timeout)
        return self._devices
