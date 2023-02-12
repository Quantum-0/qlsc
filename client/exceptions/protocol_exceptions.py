from typing import Optional

from enums.common_response_code import CommonResponseCode
from models.device import QLSCDevice
from models.packet import QLPPacket


class QLPError(Exception):
    """Base Quantum0's LED Strip Protocol Exception"""


class QLPResponseWithError(QLPError):
    """Error from QLSCDevice"""
    def __init__(
            self,
            device: QLSCDevice,
            sent_packet: Optional[QLPPacket],
            received_error: CommonResponseCode,
            error_text: Optional[str]
    ) -> None:
        self.device = device
        self.sent_packet = sent_packet
        self.received_error = received_error
        self.error_text = error_text
        if received_error == CommonResponseCode.OTHER_ERROR and error_text is None:
            raise QLPError('Got OTHER_ERROR but there is not description')
        if received_error != CommonResponseCode.OTHER_ERROR and error_text is not None:
            raise QLPError('Description is not available for any error exclude OTHER_ERROR')

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.error_text or self.received_error.name}>'
