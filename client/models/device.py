from enums.commands import CommandID
from models.color import Color
from models.device_base import QLSCDeviceBase


class QLSCDevice(QLSCDeviceBase):
    """Device's business logic inherited from internal logic"""

    @property
    def length(self):
        return self._length

    async def set_length(self, length: int):
        await self.send_command(CommandID.LENGTH, length.to_bytes(1, 'little', signed=False))
        self._length = length  # noqa # TODO: Или дождаться ответа а потом обновить?

    async def set_pixel_color(self, index: int, color: Color):
        # TODO: Test for that
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
