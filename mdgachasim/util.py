import difflib
from typing import Dict, List

from .card import Card
from .data import db


def string_to_decklist(string: str, full_match: bool = False):
    """Convenience method combinding `string_to_namelist` and `names_to_decklist`.

    Args:
        string (str): Decklist as single string.
        full_match (bool, optional): Full match only. Defaults to False.

    Returns:
        Tuple[List[Card], Dict[str, str]]:
            Tuple of the deck list and any used translatons.
    """
    return names_to_decklist(string_to_namelist(string), full_match)


def string_to_namelist(string: str):
    """Extracts a decklist from a given string.
    The string has to be in the following format:
    Each card consists of an optional number between 1 and 3, followed by the cards name.
    E.g.:
    "1 Accesscode Talker"
    is the same as
    "Accesscode Talker"

    Additonally, multiple cards can be specified per line if separated by a ";".

    E.g.:
    Accesscode talker;1 Salamangreat gazell; 3 Gamaciel, the sea turtle
    3 salamangreat spinny; 1 salamangreat circle
    """
    names: List[str] = []
    for line in map(str.strip, string.split("\n")):
        if not line:
            continue
        subline = map(str.strip, line.split(";")) if ";" in line else [line]
        names.extend(subline)
    return names


def names_to_decklist(cardnames: List[str], full_match: bool = False):
    """
    Args:
        cardnames (str): List of cardnames
        full_match (bool): If True, disables the closest string matcher. Defaults to False.

    Raises:
        ValueError: Raised if the no close matches to an extracted card candidate are found.
        ValueError: Raised if two or more possible matches for the extracted card candidate ar found.

    Returns:
        List[Card]: The extracted decklist as first in the tuple.
        Dict[str, str]: The dictionary used to translate fuzzy matches.
    """
    goals: List[Card] = []
    translations: Dict[str, str] = dict()
    available = {card.name.lower(): card for card in db.cards.values()}
    for goal_name in cardnames:
        if not goal_name:
            continue
        count = 1
        if goal_name[0] in "123":
            count = int(goal_name[0])
            goal_name = goal_name[1:].strip()
        card = available.get(goal_name.lower(), None)
        if card is not None:
            for _ in range(count):
                goals.append(card)
            continue
        matches = difflib.get_close_matches(goal_name.lower(), available)
        if not matches:
            raise ValueError(f'Unable to find card "{goal_name}"')
        if len(matches) > 1:
            raise ValueError(
                f'Multiple close matches for "{goal_name}":\n'
                + "\n".join(f" - {match}" for match in matches)
            )
        trans = available[matches[0]]
        if full_match and goal_name.lower() != trans.name.lower():
            raise ValueError(
                f'Unable to fully match "{goal_name}" (best match: "{trans.name}")'
            )
        translations[goal_name] = trans.name
        for _ in range(count):
            goals.append(trans)
    return goals, translations
