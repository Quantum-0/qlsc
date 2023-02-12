from __future__ import annotations

from typing import TYPE_CHECKING

import pydantic
from pydantic import Field

if TYPE_CHECKING:
    from engine import QLPEngine

# pylint: disable=wrong-import-position

from struct import pack

from enums.commands import CommandID
from enums.packet_type import PacketType
from models.packet import QLPPacket


class QLSCDeviceBase(pydantic.BaseModel):
    ip: str  # pylint: disable=invalid-name # TODO: type = ipaddress.IPv4Address
    device_chip_id: str
    device_uuid: str
    name: str
    _engine: QLPEngine = Field(exclude=True)
    _length: int = Field(default=0)

    def __hash__(self):
        return hash(self.device_chip_id)

    def __eq__(self, other):
        return self.device_chip_id == other.device_chip_id \
            and self.device_uuid == other.device_chip_id

    async def send_command(self, command_id: CommandID, data: bytes = b''):
        dev_id = pack('<L', int(self.device_chip_id, 16))
        packet = QLPPacket(dev_id + command_id + data, PacketType.CONTROL)
        await self._engine._send_packet(packet)  # noqa # pylint: disable=protected-access
