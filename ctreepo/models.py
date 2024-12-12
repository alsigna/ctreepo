from dataclasses import dataclass
from enum import Enum

__all__ = (
    "TaggingRule",
    "Vendor",
)


@dataclass(frozen=True, slots=True)
class TaggingRule:
    # - regex: ^ip vpn-instance (\\S+)$
    #   tags:
    #     - vpn
    #     - vrf
    # - regex: ^interface (\\S+)$
    #   tags:
    #     - interface
    regex: str
    tags: list[str]


class Vendor(str, Enum):
    ARISTA = "arista"
    CISCO = "cisco"
    HUAWEI = "huawei"
