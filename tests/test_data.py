
from mdgachasim.card import Rarity
from mdgachasim.data import db


def test_master_pack():
    assert db.master_pack.name == "Master Pack"
    assert db.master_pack.is_normal_pack
    cardlist = {card.name: card for card in db.master_pack.cardlist}
    assert 'Blue-Eyes White Dragon' not in cardlist
    assert cardlist['Dark Magician'].rarity == Rarity.Ultra
    assert cardlist['Destiny HERO - Destroyer Phoenix Enforcer' ].rarity == Rarity.Ultra
    assert 'Barrier Statue of the Stormwinds' not in cardlist
    assert cardlist['Tri-Brigade Revolt'].rarity == Rarity.Common


def test_packs():
    cardlists = {
        name: {
            card.name: card
            for card in pack.cardlist
        }
        for name, pack in db.packs.items()
    }

    assert 'Fusion Potential' in db.packs
    assert 'A Song of Zephyr and Petals' in db.packs
    assert 'Warriors of Legend' in db.packs
    assert 'Ruler\'s Mask' in db.packs
    assert 'Master Pack' not in db.packs
    assert 'Destiny HERO - Destroyer Phoenix Enforcer' in cardlists['Refined Blade']
    assert 'Rikka Petal' in cardlists['Blooming in Adversity']


def test_totals():
    assert db.packs['Refined Blade'].totals[Rarity.Ultra] == 10
    assert db.packs['Refined Blade'].totals[Rarity.Super] == 15
    assert db.packs['Refined Blade'].totals[Rarity.Rare] == 20
    assert db.packs['Refined Blade'].totals[Rarity.Common] == 35
    assert db.packs['Fusion Potential'].totals[Rarity.Ultra] == 10
    assert db.packs['Fusion Potential'].totals[Rarity.Super] == 15
    assert db.packs['Fusion Potential'].totals[Rarity.Rare] == 20
    assert db.packs['Fusion Potential'].totals[Rarity.Common] == 35
    assert db.packs["Ruler's Mask"].totals[Rarity.Ultra] == 10
    assert db.packs["Ruler's Mask"].totals[Rarity.Super] == 15
    assert db.packs["Ruler's Mask"].totals[Rarity.Rare] == 20
    assert db.packs["Ruler's Mask"].totals[Rarity.Common] == 35
    assert db.packs["Deceitful Wings of Darkness"].totals[Rarity.Ultra] == 4
    assert db.packs["Deceitful Wings of Darkness"].totals[Rarity.Super] == 8
    assert db.packs["Deceitful Wings of Darkness"].totals[Rarity.Rare] == 10
    assert db.packs["Deceitful Wings of Darkness"].totals[Rarity.Common] == 12
