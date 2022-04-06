from typing import Iterable

from mdgachasim import card
from mdgachasim.data import db
from mdgachasim.simulator import goal_info, simulation
from mdgachasim.util import names_to_decklist, string_to_namelist


def string_to_decklist(string: str):
    return names_to_decklist(string_to_namelist(string))


def _get_sources(cardlist: Iterable[card.Card]):
    return set(
        source
        for card in cardlist
        for source in db.packs.values()
        if card in source.cardlist
    )


def test_goal_info():
    decklist = [
        db.cards["Ash Blossom & Joyous Spring"],
        db.cards["Link Spider"],
        db.cards["Accesscode Talker"],
    ]
    info = goal_info(decklist)
    print(info)


def test_normal_pack():
    for i in range(10):
        pull = db.packs["Stalwart Force"].pull_ten(i, db.master_pack)
        for c in pull.cards:
            # Normal packs must have all of their cards come from
            # that pack
            assert db.packs["Stalwart Force"] in _get_sources([c])


def test_secret_pack():
    for i in range(10):
        result = db.packs["Moonlit Avian Dance"].pull_ten(i, db.master_pack)
        sources = _get_sources(result.cards)
        # Remove Stalwart because some lyrilusc cards are obtainable there
        if db.packs["Stalwart Force"] in sources:
            sources.remove(db.packs["Stalwart Force"])
        # 4 Guaranteed from this pack
        assert db.packs["Moonlit Avian Dance"] in sources
        # The first four are not from Moonlit, and may come from any pack
        # This test may fail some times, because not all cards are implemented
        # Which will result in material generation instead of adding a source
        assert len(sources) > 1


def test_bundles():
    (ash, solemn, lightning), _ = string_to_decklist(
        "Ash Blossom & Joyous Spring; Solemn judgment; Lightning Storm"
    )
    for featured in [ash, solemn, lightning]:
        cost0, *_ = simulation([featured])
        assert cost0 >= 1000
        bundles = [b for b in db.bundles if featured in b.featured_cards]
        assert len(bundles) == 1
        cost, *_ = simulation([featured], bundles=bundles)
        assert cost == 750
    cost, *_ = simulation(
        [ash, solemn, lightning],
        bundles=db.bundles,
        no_crafting=True,
    )
    assert cost == 750 * 3
    cost, *_ = simulation(
        [ash, lightning, solemn, solemn], bundles=db.bundles, no_crafting=True
    )
    assert cost > 750 * 3


def test_core_only():
    for flag in (True, False):
        cost, *_ = simulation(
            string_to_decklist(
                """
            3 Twin Twisters
            Pot of Prosperity
            Pot of Desires
            Pot of Extravagance """
            )[0],
            core_only=flag,
        )
        if flag:
            assert cost <= 1000
        else:
            assert cost > 1000


def test_get_gift():
    cost, *_ = simulation(
        string_to_decklist(
            """
            Link Spider
            Raigeki
            Monster Reborn
            """
        )[0],
    )
    assert cost <= 1000
    cost, *_ = simulation(
        string_to_decklist(
            """
            3 Link Spider
            3 Raigeki
            3 Monster Reborn
            """
        )[0],
    )
    assert cost > 1000


zoo_tribrigade, _ = string_to_decklist(
    """
2 D.D. Crow
3 Tri-Brigade Nervall
3 Maxx "C"
3 Tri-Brigade Kitt
3 Tri-Brigade Kerass
3 Ash Blossom & Joyous Spring
3 Tri-Brigade Fraktall
Zoodiac Thoroughblade
Zoodiac Whiptail
Zoodiac Ramram
2 Nibiru, the Primal Being
3 Pot of Desires
3 Fire Formation - Tenki
2 Called by the Grave
3 Forbidden Droplet
2 Infinite impermanence
3 Tri-Brigade Revolt
Zoodiac Chakanine
Zoodiac Boarbow
Zoodiac Drident
Zoodiac Tigermortar
Divine Arsenal AA-Zeus - Sky Thunder
Salamangreat Almiraj
Ancient Warriors Oath - Double Dragon Lords
Tri-Brigade Bearbrumm the Rampant Rampager
Tri-Brigade Ferrijit the Barren Blossom
Hraesvelgr, the Desperate Doom Eagle
Tri-Brigade Rugal the Silver Sheller
Accesscode Talker
Apollousa, bow of the goddess
2 tri-brigade shuraig the ominous omen
"""
)


def test_simulation():
    cost, mat, goals = simulation(zoo_tribrigade)
    for r, m in mat.items():
        assert m > 0, "Some materials of each rarity should stay unused"
    assert len(goals) > 0, "Not using crafting is very rare"
    assert len(goals) < len(zoo_tribrigade), "Exclusively using crafting is also rare"
    assert cost > 0, "Some gems should have been spent"
