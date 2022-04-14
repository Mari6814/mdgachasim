# Introduction

This is a simulator for sampling the cost distribution of *Yu-Gi-Oh! Master Duel* packs.
It implements all cards, bundles, selection packs, crafting, pity, pack unlocking
and all secret packs, courtesy of [yugipedia](https://yugipedia.com).


# How to use

Download the package and run without installing or install with pip using the github protocol.
This package is not uploaded to pip and you have to install it using `pip install git+https://github.com/Mari6814/mdgachasim.git`.

### Verbalising the problem

In order to run a simulation, you have to verbalise the problem first.  For a
gacha simulator, the problem is a list of cards you still need.  All card
specifications are accessible directly via the singleton instance `db` of type
`Database` in the module `mdgachasim.data`.  The database's singleton has the
member `cards` which is a dictionary, mapping the exact card name to an instance
of `mdgachasim.card.Card`.

```python
# Import the database singleton
from mdgachasim.data import db

# Specify goal decklist
goals = [
    db.cards["Accesscode Talker"],
    db.cards["Salamangreat Almiraj"],
    db.cards["Pot of Desires"],
    db.cards["Pot of Desires"],
    db.cards["Pot of Desires"],
    db.cards["Ash Blossom & Joyous Spring"],
    db.cards["Ash Blossom & Joyous Spring"],
    db.cards["Ash Blossom & Joyous Spring"],
]
```

Since this is very tedious, you can use the utility function `string_to_decklist` in the module `mdgachasim.util`.
Be careful as it tries to repair any writing mistakes. It doesn't only return the decklist, but also a dictionary
of automatically derived card name translations, which is only for your information and can be ignored.

```python
from mdgachasim.util import string_to_decklist

goals, _translations = string_to_deck("""
    Accesscode Talker
    1 salamangreat almiraj
    Pot of Desires; Pot of Desires; Pot of Desires
    3 Ash Blossom & Joyous Spring
""")
```

Instead of writing "Accesscode Talker" for example, only writing "Accesscode" does also suffice
and the correct card will be found automatically.

### Sampling the cost distribution

The `mdgachasim.simulator` module contains the `simulation` function which does the actual sampling.
It takes a list of goals (= cards) as input among many other parameters. But watch out, besides the sampled cost,
the `simulation` function also returns the materials per rarity used to craft the all leftover cards at the end.

```python
from mdgachasim.simulator import simulation

cost, materials, crafted_cards = simlation(goals)

print(cost) # An integer with the amount of gems spent for this single sample
```

### Rebuilding the distribution

Since this is a statistical process, you have to sample the cost distribution many times (around 100 is enough),
in order to be able to reconstruct the distribution. Remember to only select the first value in the returned tuple.
After you have sampled the distribution enough, you can plot a cumulative density histograms like I did in my reddit post,
or simply take averages and whatnot.

```python
# Sample the distribution 100 times
costs = [
    simulation(goals)[0]
    for _ in range(100)
]

# Print the average cost
print("Average cost: ", sum(costs) / len(costs), "gems")

# Show histograms (requires matplotlib installed)
from matplotlib import pyplot

pyplot.hist(costs, density=True, cumulative=True)
pyplot.ylabel('Probability of completing the decklist')
pyplot.xlabel('Gems spent')
pyplot.show()
```

### Sub-goals

One of the most important features of the simulator is the ability to specify sub-goals.
Main goals, as explained in the previous section, are used to determine what specifically to get
and when to terminate the simulation. But this means that only exactly that specified main goal list
is being searched for. Because of that you may have pulled a playset of Forbidden Droplet, but because
you didn't specify it in your main goals, they were dismantled for a copy of Ash Blossom.
To prevent this, you can add `sub_goals` to a call of `simulator`. The sub-goals are like the main
goals just a list of cards. The effects of sub-goals are, that if a non-main-goal card obtained,
instead of dismantling it, it will be added to the fulfilled sub-goals.

```python
main, _ = string_to_decklist("Accesscode Talker")
sub, _ = string_to_decklist("3 Cynet mining")

cost = sum(simulation(main, sub_goals=sub)[0] for _ in range(100)) / 100
```

In this example above, someone tries to compute how much getting an Accesscode from "Soldiers from the Storm"
would cost. As a sub-goal they specified "3x Cynet Mining", preventing the simulation from dismantling the first
three Cynet Minings it obtains, increasing the accuracy of the cost estimation.

### A helper main method.

To make things a little bit easier I have implemented the main method, allowing you to run the command:

```
python -m mdgachasim --file FILE [--population-size POPULATION_SIZE] [--core-only] [--show-hist] [--info] [--verbose] [--full-match-only] [--save-figure SAVE_FIGURE]
```

It takes a file (must use `--file` argument) that contains a decklist as input
and automatically figures out which cards are in there.  The file format is a
semicolon or newline separated list of full card names (case insensitive).  Each
card is optionally preceded by a number between 1 and 3.  You can also just
write the card's name out multiple time instead of adding the number in front.
This is an example decklist file:

```
Accesscode Talker; 2 salamangreat Almiraj
3 GAMACIEL THE SEA TURTLE
Accesscode Talker
```

This file would sample the cost distribution of this list with 2 Accesscode, 2 Almiraj and 3 Gamaciel.

`--population-size` defaults to 100, but you can increase it if you want.  It controls how often the cost distribution of the decklist is sampled.

The `--core-only` flag can be enabled to ignore cards marked as staple.

The `--show-hist` flag can be enabled to display a histogram using matplotlib.

The `--info` flag prints a bunch of meta information about the provided decklist before starting the simulation.
For example, how many rarities, how many cards, from which packs are the cards available... etc.

The `--verbose` option logs all the actions done during the simulation process to stderr.

To disable the automated card name fixing, you can use `--full-match-only`. This is useful to make sure
the simulator actually uses your specified decklist and hasn't secretly replaced one of your specified cards with something
similar because you made a mistake.

If you don't want to show the histogram, but want to save it to a file instead, use the `--save-figure` option followed by a
file path ending in ".png" or ".jpg".
