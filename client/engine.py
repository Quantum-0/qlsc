import asyncio
import datetime
import logging
import socket
from collections import defaultdict
from typing import Optional, Set

import enums.discovery_packet_body as dpb
from enums.packet_type import PacketType
from exceptions.protocol_exceptions import QLPError
from models.device import QLSCDevice
from models.packet import QLPPacket
from utils.esp_touch import init as esp_touch_init, sendData as esp_touch_send_data
from utils.singleton import Singleton

logger = logging.getLogger('Engine')


class QLPEngine(metaclass=Singleton):
    """Engine for Quantum0's LED Strip Protocol, allows to interact with devices"""
    __QLP_PORT__ = 52075
    __RECV_TIMEOUT = 1.5

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
        # Sent packets, waiting for confirmation: dev_uuid:timestamp+command_counter
        self.__packets: dict[str, tuple[datetime.datetime, int]] = {}
        self.__locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        logger.debug('Engine was created')

    def __getitem__(self, device_uuid: str) -> Optional[QLSCDevice]:
        for device in self._devices:
            if device.device_uuid == device_uuid:
                return device
        logger.info('Device with uuid="%s" was not found', device_uuid)
        return None

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
                    logger.info('<<<< RX: %s', data.hex(' ').upper())
                    logger.debug('Receiving packet: %s', packet)
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
                engine=self,
            )
            self._devices.add(new_dev)
        if packet.device_id is not None:
            if packet.device_id not in self.__packets:
                raise NotImplementedError('WTF happen???')
            packet_counter = self.__packets[packet.device_id][1]
            if packet.packet_counter == packet_counter:
                self.__locks[packet.device_id].release()
                logger.debug(
                    'Response from device_id="%s" for command_counter=%s was received, lock was released',
                    packet.device_id,
                    str(packet_counter),
                )
                del self.__packets[packet.device_id]
            else:
                logger.debug(
                    'Command counter is incorrect. Wait for %s, received %s. '
                    'Probably that was response to another client',
                    packet_counter,
                    packet.packet_counter,
                )

    async def _send_packet(self, packet: QLPPacket) -> None:
        if packet.device_id is not None:
            lock = self.__locks[packet.device_id]
            if lock.locked():
                if (datetime.datetime.now() - self.__packets[packet.device_id][0]).total_seconds() < self.__RECV_TIMEOUT:
                    logger.info('Sending of packet paused: waiting for response for previous command')
                    while lock.locked() and (datetime.datetime.now() - self.__packets[packet.device_id][0]).total_seconds() < self.__RECV_TIMEOUT:
                        await asyncio.sleep(0.01)
                if (datetime.datetime.now() - self.__packets[packet.device_id][0]).total_seconds() > self.__RECV_TIMEOUT:
                    logger.debug('Lock was released because no response from device')
                    lock.release()
        else:
            logger.debug('Packet has no device_id so no awaiting')

        # if packet.device_id in self.__packets or (datetime.datetime.now() - self.__packets[packet.device_id][0]).total_seconds() < self.__RECV_TIMEOUT:
        #     logger.info('Sending of packet paused: waiting for response for previous command')
        #     while packet.device_id in self.__packets:
        #         await asyncio.sleep(0.01)

        serialized_packet = packet.serialize() if isinstance(packet, QLPPacket) else packet
        logger.info('>>>> TX: %s', serialized_packet.hex(' ').upper())
        logger.debug('Sending packet: %s', packet)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(serialized_packet, ('255.255.255.255', self.__QLP_PORT__))
            self.__just_send_packet = serialized_packet
            self.__packets[packet.device_id] = (datetime.datetime.now(), packet.packet_counter)
            await self.__locks[packet.device_id].acquire()
            # raise NotImplementedError('Тут записывает пакет в список ожидания ответа')

    async def discover_all_devices(self, timeout: float = __RECV_TIMEOUT) -> Set[QLSCDevice]:
        logger.debug('Search for devices...')
        await self._send_packet(QLPPacket(dpb.ANYBODY_HERE, PacketType.DISCOVERY))
        await asyncio.sleep(timeout)
        return self._devices

    @staticmethod
    def connect_new_devices(ssid: str, password: str):
        esp_touch_init(ssid, password, 'T', '255.255.255.255', None)
        esp_touch_send_data()
