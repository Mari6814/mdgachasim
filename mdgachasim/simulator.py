import logging as _logging
from typing import Dict, List, Optional, Set

from .bundle import Bundle
from .card import Card, Rarity
from .data import db
from .pack import Pack


def goal_info(goals: List[Card]):
    """Prints some info about the given decklist.

    Args:
        goals (List[Card]): Some decklist.

    Returns:
        str: A printable string with information about the decklist. Just print
            it out.
    """
    sources: List[Pack] = [
        source
        for card in goals
        for source in db.packs.values()
        if source != db.master_pack and card in source
    ]
    s = "Number per rarity:\n"
    for rarity in Rarity:
        count = sum(card.rarity == rarity for card in goals)
        s += f"{count} {rarity.name}(s)\n"
    s += f"{len(goals)} total\n"
    s += "\nPacks used:\n"
    source_names = [source.name for source in sources]
    for source in set(source_names):
        s += f" - {source} ({source_names.count(source)} card(s))\n"
    craftable_only = [
        card for card in goals if not any(card in source for source in sources)
    ]
    craftable_only_rarities = {
        r: len([card for card in craftable_only if card.rarity == r]) for r in Rarity
    }
    normals = craftable_only_rarities[Rarity.Common]
    rares = craftable_only_rarities[Rarity.Rare]
    supers = craftable_only_rarities[Rarity.Super]
    urs = craftable_only_rarities[Rarity.Ultra]
    s += f"\n{len(craftable_only)} Master Pack only card(s): {normals} (N), {rares} (R), {supers} (SR), {urs} (UR)"
    n = 0
    r = 0
    sr = 0
    ur = 0
    for card in goals:
        if card.staple and card.rarity == Rarity.Common:
            n += 1
        if card.staple and card.rarity == Rarity.Rare:
            r += 1
        if card.staple and card.rarity == Rarity.Super:
            sr += 1
        if card.staple and card.rarity == Rarity.Ultra:
            ur += 1

    s += f"\n{n+r+sr+ur} staples: {n} (N), {r} (R), {sr} (SR), {ur} (UR)"
    return s


def _find_goal_sources(goals: List[Card], packs_unlocked: Set[Pack]):
    """Find the list of sources all the goals can be obtained from.
    Also respect only selection packs that are still available.

    Args:
        goals (Set[Card]): List of goals.
        packs_unlocked (Set[Pack]): Available packs.

    Returns:
        Dict[Pack, List[Card]]: List of goals that can be obtained from each source
    """
    sources: Dict[Pack, List[Card]] = {}
    for goal in goals:
        # legacy and unobtainable cards don't have any sources
        for source in db.sources.get(goal, ()):
            # Add secret packs to the set of sources for this card.
            # But filter out all normal packs that are not pre-unlocked,
            # because normal packs cannot be unlocked by crafting.
            if not source.is_normal_pack or source in packs_unlocked:
                sources.setdefault(source, []).append(goal)
    return sources


def _remove_card_from_goals(
    card: Card,
    goals: List[Card],
    per_source: Dict[Pack, List[Card]] = None,
    *,
    log: Optional[_logging.Logger] = None,
    is_sub_goal: bool = False,
):
    """Removes a card from the list of main or sub goals given in `goals`.
    Then checks and removes the card from the per source sorted dictionary `per_source`.
    `per_source` should always contain the same cards as  `goals`, but sorted by the pack they are available in.

    Args:
        card (Card): Card to remove.
        goals (List[Card]): List of goals from which the card should be removed.
        per_source (Dict[Pack, List[Card]], optional): Dictionary of sources with their goals from which the card should be removed.
        log (Optional[Logger]): Logger for logging which goal was obtained. Defaults to None.
        is_sub_goal (bool, optional): Extra bit of info for logging which goal type was obtained. Defaults to False.
    """
    if card not in goals:
        return False
    goals.remove(card)
    if log:
        if is_sub_goal:
            log.info('Obtained sub goal "%s"', card.name)
        else:
            log.info('Obtained main goal "%s"', card.name)
    if per_source:
        do_cleanup = False
        for source, cards in per_source.items():
            if card in cards:
                cards.remove(card)
                if not cards:
                    do_cleanup = True
        if do_cleanup:
            for source, cards in list(per_source.items()):
                if not cards:
                    del per_source[source]
    return True


def simulation(
    goals: List[Card],
    sub_goals: List[Card] = None,
    materials: Dict[Rarity, int] = None,
    packs_unlocked: Set[Pack] = None,
    bundles: Set[Bundle] = None,
    core_only: bool = False,
    rarity_weight: Dict[Rarity, float] = None,
    gifts: List[Card] = None,
    staples: Set[Card] = None,
    log: Optional[_logging.Logger] = None,
    no_crafting: bool = False,
):
    """This is the basic simulation function.
    It samples the deck cost distribution of the given decklist exactly once.
    ```

    Args:
        goals (List[Card]): A list of cards that has to be obtained before the simulation ends.
        sub_goals (List[Card], optional): A list of sub-goals that if obtained,
            should not be dusted for materials. Defaults to None.
        materials (Dict[Rarity, int], optional): Initial number of materials
            owned. Defaults to None.
        core_only (bool, optional): Enables removing cards marked as 'staple'
            prior to doing anything else. Defaults to False.
        packs_unlocked (Set[Pack], optional): The set of packs currently unlocked, including selection packs. Defaults to None.
        bundles (Set[Bundle], optional): List of available bundles. Defaults to None.
        rarity_weight (Dict[Rarity, float], optional): "A weighting given to
            each rarity that is required for comparing which available source has
            the most "value". 10 packs are then bought from the source with the most
            value. Defaults to None.
        gifts (List[Card], optional): Forces a list of gifted cards. If None,
            then all known gifts are considered as received. Defaults to None.
        staples (List[Card], optional): Custom set of what card is considered a staple. Defaults to None.
        log (Logger, optional): An instance of a logging.Logger that can be used to log every action the simulation takes.
        no_crafting (boolean, optional): Disables crafting for testing purposes. Defaults to False.

    Returns:
        Tuple[int, Dict[Rarity, int], List[Card]]: Tuple containing the sampled decklist
            cost and the materials used to craft the remaining cards. The remaining cards
            are the third entry in the tuple.
    """
    rarity_weight = rarity_weight or {}
    materials = (materials or {}).copy()
    packs_unlocked = (packs_unlocked or set()).copy()
    for r in Rarity:
        materials.setdefault(r, 0)
    goals = goals.copy()
    # Remove all gifts from the goal pool according
    # to the correct number of cards gifted
    for goal in set(goals):
        gift_count = min(
            goals.count(goal), goal.gift if gifts is None else gifts.count(goal)
        )
        for _ in range(gift_count):
            goals.remove(goal)
        if gift_count and log:
            log.info(
                'Removed %i "%s" from goals as it was a gift.', gift_count, goal.name
            )
    # Remove staple cards up to the number the player can be expected
    # to own them/can be expected to find replacements
    if core_only:
        for goal in set(goals):
            if (staples is None and goal.staple) or (
                staples is not None and goal in staples
            ):
                while goal in goals:
                    goals.remove(goal)
            if log:
                log.info('Removed staple "%s" from goal list.', goal.name)
    # The number of goals available for each source
    # The `cards_per_source` will be used to quantify which pack should be opened.
    cards_per_source: Dict[Pack, List[Card]] = _find_goal_sources(goals, packs_unlocked)
    if log:
        for source, cards in filter(lambda x: x[-1], cards_per_source.items()):
            log.info('"%s" contains %i goals', source.name, len(cards))
    # Initialize per pack pity
    per_pack_pity: Dict[Pack, int] = {}
    # List of sub goals
    sub_goals = (sub_goals or []).copy()

    # Before pulling, figure out which bundles need to be bought
    must_buy_bundles: List[Bundle] = []
    if bundles:
        for g in goals:
            for bundle in bundles:
                if g in bundle.featured_cards and bundle not in must_buy_bundles:
                    must_buy_bundles.append(bundle)
                    if log:
                        log.info(
                            'Planning to buy the bundle "%s" for a copy of "%s"',
                            bundle.name,
                            g.name,
                        )

    # Gem cost in total
    cost = 0

    def expected_return(source_pack: Pack):
        assert rarity_weight is not None
        rarity_prob = {
            Rarity.Ultra: 0.025,
            Rarity.Super: 0.075,
            # Rares and normals are not worth going into a box for:
            # So I lower their value by default
            # Completely removing doesn't work because then N/R only decks
            # have no defined heuristic
            Rarity.Rare: 0.35 / 100,
            Rarity.Common: 0.55 / 1000,
        }
        # Sum the probabilities that you pull each card from the source_pack
        return sum(
            rarity_prob[card.rarity]
            * rarity_weight.get(card.rarity, 1)
            # Divide by the number of cards in the pack of that rarity.
            # In case there are no cards of that rarity (because of missing info in the dataset),
            # assume there are at least 4 cards of that rarity.
            / source_pack.totals.get(card.rarity, 4)
            for card in cards_per_source[source_pack]
        )

    for _ in range(50):
        if must_buy_bundles:
            # Always exhaust the available bundles first
            bundle = must_buy_bundles.pop()
            # The bundle card may have been obtained randomly:
            # skip the bundle if so
            if not any(featured in goals for featured in bundle.featured_cards):
                if log:
                    log.info(
                        'Skipping bundle "%s" as the featured card has already been obtained.',
                        bundle.name,
                    )
                continue
            for featured in bundle.featured_cards:
                # Remove featured cards primarily from main goals
                if not _remove_card_from_goals(
                    featured, goals, cards_per_source, log=log
                ):
                    # Since in future bundles may contain more than one featured card,
                    # we have to also remove any other cards from sub goals if possible.
                    if not _remove_card_from_goals(
                        featured, sub_goals, None, log=log, is_sub_goal=True
                    ):
                        # else dismantle
                        materials[featured.rarity] += 10
            source = bundle.featured_pack
            cost += bundle.cost
            if log:
                log.info('Purchased bundle "%s" for %i gems', bundle.name, bundle.cost)
        elif not cards_per_source:
            # If all cards from sets are picked, go into master pack
            # and try to randomly obtain an unobtainable card
            # while also accumulating materials for crafting.
            source = db.master_pack
            cost += 1000
            if log:
                log.info('Pulling from "%s" for %i gems', source.name, 1000)
        else:
            # Get most valuable set
            if log:
                for source in cards_per_source:
                    log.info("Expected return for %s: %f", source.name, expected_return(source))
            source = max(cards_per_source, key=expected_return)
            # Before pulling, handle unlocking and crafting here
            if not source.is_normal_pack and source not in packs_unlocked:
                # Priority: Craft super before ultra
                for rarity in [Rarity.Super, Rarity.Ultra]:
                    for craft in cards_per_source[source]:
                        if craft.rarity != rarity:
                            continue
                        _remove_card_from_goals(craft, goals, cards_per_source, log=log)
                        materials[rarity] -= 30
                        if log:
                            log.info(
                                'Crafting "%s" (%s) to unlock "%s": %i (-%i) %s materials',
                                craft.name,
                                rarity.value,
                                source.name,
                                materials[rarity],
                                30,
                                rarity.value,
                            )
                        # Break if crafted
                        break
                    else:
                        # Go to next rarity if not yet crafted
                        continue
                    # Break if crafted
                    break
                else:
                    # If neither a super nor ultra from the pack are needed, craft a random one.
                    # A random one is not recorded, so we just remove the materials.
                    # 20 because we can dismantle it, ignore finish here for simplicity.
                    materials[Rarity.Super] -= 20
                    if log:
                        mats = materials[Rarity.Super]
                        log.info(
                            'No SR/UR from "%s" required: Crafting any super to unlock: %i (-%i) SR materials',
                            source.name,
                            mats,
                            -20,
                        )
                packs_unlocked.add(source)
                # If successfully crafted, continue the whole loop and do not buy the pack
                continue

            cost += 1000
            if log:
                log.info('Pulling from "%s" for %i gems', source.name, 1000)
        pull = source.pull_ten(per_pack_pity.get(source, 0), db.master_pack)
        per_pack_pity[source] = pull.pity
        if log:
            log.info('Now at %i pity for pack "%s"', pull.pity, source.name)
        for card, finish in zip(pull.cards, pull.finishes):
            # Add unlocked packs
            if card.rarity in (Rarity.Super, Rarity.Ultra):
                # Different unlock behaviour depending on if logs are enabled or not
                if log:
                    # if loggin is enabled, log only newly unlocked packs
                    for newly_unlocked in db.sources.get(card, set()):
                        if (
                            newly_unlocked not in packs_unlocked
                            and newly_unlocked in cards_per_source
                        ):
                            packs_unlocked.add(newly_unlocked)
                            log.info(
                                'Unlocked "%s" because "%s" was obtained.',
                                newly_unlocked.name,
                                card.name,
                            )
                else:
                    # without logging, simply update the unlocked packs set
                    packs_unlocked.update(db.sources.get(card, set()))
            # Remove card from main goals
            if not _remove_card_from_goals(card, goals, cards_per_source, log=log):
                # If not a main goal, attempt to remove from sub goals
                if not _remove_card_from_goals(
                    card, sub_goals, None, log=log, is_sub_goal=True
                ):
                    # If neither a main nor sub goal, dismantle the card
                    # and add the finish value to the pull's materials
                    pull.materials[card.rarity] += finish
        # Add the pulled materials of unimplemented cards
        for r, v in pull.materials.items():
            materials[r] += v
            if log and v > 0:
                log.info("%i (+%i) %s materials", materials[r], v, r.name)
        # At the end of each pull,
        # test if we have enough materials to craft the remaining cards.
        remaining_materials = materials.copy()
        for unobtained_card in goals:
            remaining_materials[unobtained_card.rarity] -= 30
        # Left over cards can be crafted if all mats >= 0: Done
        if all(mats >= 0 for mats in remaining_materials.values()):
            if no_crafting and goals:
                continue
            if log:
                log.info("Crafting all unobtained cards.")
            break
    if log:
        log.info("Deck obtained after spending %i gems", cost)
    return cost, materials, goals
