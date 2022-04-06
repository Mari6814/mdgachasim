from typing import List

from .card import Card
from .pack import Pack


class Bundle:
    def __init__(
        self,
        name: str,
        cost: int,
        featured_pack: Pack,
        featured_cards: List[Card],
    ):
        self.name = name
        self.cost = cost
        self.featured_pack = featured_pack
        self.featured_cards = featured_cards

    def __repr__(self):
        return f'[Bundle "{self.name}"]'
