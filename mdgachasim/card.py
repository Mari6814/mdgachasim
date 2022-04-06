from dataclasses import dataclass
from enum import Enum


class Rarity(Enum):
    Common = "n"
    Rare = "r"
    Super = "sr"
    Ultra = "ur"


@dataclass(frozen=True, eq=True)
class Card:
    # Card name
    name: str
    # Rarity in game
    rarity: Rarity
    # Amount at which this card is a staple
    staple: bool = False
    # Amount of "gifts" you get
    gift: int = 0
