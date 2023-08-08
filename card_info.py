from typing import NamedTuple
from enum import Enum


class FoilType(Enum):
    NONE = 1
    TRADITIONAL = 2
    SURGE = 3


class CardInfo(NamedTuple):
    card_name: str
    set_id: str
    collector_number: str
    language: str
    foil_type: FoilType
