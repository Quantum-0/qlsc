import dataclasses
import ipaddress
from typing import Self

from pydantic import BaseModel


class Device(BaseModel):
    ip: ipaddress.IPv4Address
    title: str


    @classmethod
    def from_dc(cls, device_dc: dataclasses.dataclass) -> Self:
        return cls(dataclasses.asdict(device_dc))
