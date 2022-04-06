from typing import Dict, List, Optional, Tuple

if __name__ == "__main__":
    import logging
    import statistics
    import sys
    from argparse import ArgumentParser
    from pathlib import Path

    from .data import db
    from .plot import plot
    from .simulator import goal_info, simulation
    from .util import names_to_decklist, string_to_namelist

    # Set up the parser
    parser = ArgumentParser()
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        help="Path to a decklist file. If not set, stdin is used.",
    )
    parser.add_argument(
        "--population-size",
        "-p",
        type=int,
        default=100,
        help="Simulation population size.",
    )
    parser.add_argument(
        "--core-only",
        "-c",
        choices=("no", "ignore", "both"),
        default="both",
        help="""Setting for comparing the cost of the decklist with or without staples.
"no" computes the cost with all cards.
"ignore" removes all cards marked as "staple".
"both" greates a comparison between the two options.""",
    )
    parser.add_argument(
        "--show-hist",
        "-s",
        action="store_true",
        help="Use matplotlib to display a cumulative density histogram of the cost.",
    )
    parser.add_argument(
        "--info",
        "-i",
        action="store_true",
        help="Print decklist information on startup.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Log information about each step in the simulation process.",
    )
    parser.add_argument(
        "--fuzzy-match",
        action="store_true",
        help="Allows the card name parser to fuzzy search cards.",
    )
    parser.add_argument(
        "--save-figure",
        "-S",
        type=Path,
        help="Provides a path to save the image created by using the --show-hist option. Defaults to None.",
        default=None,
    )
    parser.add_argument(
        "--dpi",
        type=int,
        help="DPI of the created histogram figure.",
        default=300,
    )
    parser.add_argument(
        "--title",
        "-t",
        help="Sets a custom title of the saved histogram.",
        default="Cost of obtaining all goals",
    )
    parser.add_argument(
        "--print-stats",
        help="Enables printing of simulation stats for each series.",
        action="store_true",
    )

    # Parser arguments and give mypy enough information about the types
    args = parser.parse_args()
    assert args.file is None or isinstance(args.file, Path)
    assert isinstance(args.population_size, int)
    assert isinstance(args.show_hist, bool)
    assert isinstance(args.info, bool)
    assert isinstance(args.verbose, bool)
    assert isinstance(args.fuzzy_match, bool)
    assert isinstance(args.dpi, int)
    assert args.core_only in ("no", "ignore", "both")
    assert isinstance(args.title, str)
    assert isinstance(args.print_stats, bool)
    assert args.save_figure is None or isinstance(args.save_figure, Path)
    # Some errors
    if args.population_size <= 0:
        print(f"error: Invalid population size {args.population_size}", file=sys.stderr)
        exit(1)
    if args.file and not args.file.is_file():
        print("error: Provided file path is not a file", file=sys.stderr)
        exit(1)
    # Determine the goal decklist from a file
    with args.file.open() if args.file else sys.stdin as fd:
        try:
            goals, trans = names_to_decklist(
                string_to_namelist(fd.read()), full_match=not args.fuzzy_match
            )
        except ValueError as e:
            print(str(e), file=sys.stderr)
            exit(1)
        for goal_name, translation in trans.items():
            if args.fuzzy_match:
                print(f'Found "{goal_name}" -> "{translation}"', file=sys.stderr)
    if not goals:
        print("error: No goals defined.", file=sys.stderr)
        exit(1)
    # Goals have been created, print some info
    if args.info:
        print(goal_info(goals))

    sim_runs: Dict[str, List[Tuple[Optional[str], bool]]] = {
        "no": [(None, False)],
        "ignore": [("Core only", True)],
        "both": [(r"\w staples", False), ("Core only", True)],
    }
    data: Dict[Optional[str], List[int]] = {}
    ticks: List[float] = []
    for name, core_only in sim_runs[args.core_only]:
        # Do the actual sampling of the cost distribution
        log: Optional[logging.Logger] = None
        # Enable verbose simulation output
        if args.verbose:
            logging.basicConfig(level=logging.INFO)
            log = logging.getLogger(name)
        costs = [
            simulation(
                goals.copy(),
                core_only=core_only,
                log=log,
            )[0]
            / 1000
            for i in range(args.population_size)
        ]
        avg = statistics.mean(costs)
        # Accumulate special ticks that are not already recorded
        for new_tick in (avg, max(costs)):
            if all(abs(m - new_tick) > 1 for m in ticks):
                ticks.append(new_tick)
        # Print results
        if args.print_stats:
            std = statistics.stdev(costs)
            print(f"[{name or ''}] The average cost is {avg:.0f}k±{std:.0f}k gems.")
        data[name] = costs
    # Show some histogram?
    if args.show_hist or args.save_figure:
        plot(data, args.title, args.dpi, ticks, args.save_figure, args.show_hist)
