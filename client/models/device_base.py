from __future__ import annotations

import logging
from struct import pack
from typing import TYPE_CHECKING

from pydantic import Field, BaseModel

if TYPE_CHECKING:
    from engine import QLPEngine

# pylint: disable=wrong-import-position

from enums.commands import CommandID
from enums.packet_type import PacketType
from models.packet import QLPPacket

logger = logging.getLogger('Device')


class QLSCDeviceBase(BaseModel):
    """QLSC Device base class, containing internal logic"""
    ip: str  # pylint: disable=invalid-name # TODO: type = ipaddress.IPv4Address
    device_chip_id: str
    device_uuid: str
    name: str
    engine: QLPEngine = Field(exclude=True, default=None)
    length: int = Field(default=0)

    def __hash__(self):
        return hash(self.device_chip_id)

    def __eq__(self, other):
        return self.device_chip_id == other.device_chip_id \
            and self.device_uuid == other.device_chip_id

    def set_engine(self, engine: QLPEngine):
        if self.engine:
            raise RuntimeError()
        logger.warning('USING METHOD FOR EMULATING DEVICES')
        self.engine = engine

    async def send_command(self, command_id: CommandID, data: bytes = b''):
        dev_id = pack('<L', int(self.device_chip_id, 16))
        packet = QLPPacket(dev_id + command_id + data, PacketType.CONTROL, device_id=self.device_uuid)
        await self.engine._send_packet(packet)  # noqa # pylint: disable=protected-access
        # TODO: self.engine.wait_response???
