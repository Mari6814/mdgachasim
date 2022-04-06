from pathlib import Path
from typing import Dict, List, Set

from pydantic import BaseModel

from .bundle import Bundle
from .card import Card, Rarity
from .pack import Pack

PRIVATE_DATABASE_PATH = Path(__file__).parent / "data" / "database_priv.json"
PUBLIC_DATABASE_PATH = Path(__file__).parent / "data" / "database_pub.json"


class BundleModel(BaseModel):
    title: str
    pack: str
    cards: List[str]
    price: int


class DatabaseModel(BaseModel):
    bundles: List[BundleModel]
    gifts: Dict[str, int]
    packs: Dict[str, Set[str]]
    rarities: Dict[str, Rarity]
    staples: Set[str]
    selection_packs: Set[str]
    master_pack: Set[str]

    class Config:
        use_enum_values = True


class Database:
    @staticmethod
    def from_file(path: Path):
        return Database(DatabaseModel.parse_file(path))

    def __init__(self, model: DatabaseModel):
        self.cards = {
            name: Card(
                name, Rarity(rarity), name in model.staples, model.gifts.get(name, 0)
            )
            for name, rarity in model.rarities.items()
        }
        self.master_pack = Pack(
            "Master Pack",
            set(self.cards[card] for card in model.master_pack),
            is_normal_pack=True,
        )
        self.packs = {
            name: Pack(
                name,
                set(self.cards[card] for card in cards_in_pack),
                name in model.selection_packs,
            )
            for name, cards_in_pack in model.packs.items()
        }
        self.sources: Dict[Card, Set[Pack]] = {
            card: set() for card in self.cards.values()
        }
        for pack in self.packs.values():
            for card in pack:
                self.sources[card].add(pack)
        self.bundles = {
            Bundle(
                bundle.title,
                bundle.price,
                self.master_pack
                if bundle.pack == self.master_pack.name
                else self.packs[bundle.pack],
                featured_cards=[self.cards[card] for card in bundle.cards],
            )
            for bundle in model.bundles
        }


db = Database.from_file(PRIVATE_DATABASE_PATH)
