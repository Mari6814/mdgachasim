import math
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import seaborn as sb
from matplotlib import ticker


def plot(
    data: Dict[Optional[str], List[int]],
    title: str = "Title",
    dpi: int = 300,
    ticks: List[float] = None,
    save_figure: Optional[Path] = None,
    show_hist: bool = False,
):
    """Plotting utility.

    Args:
        data (Dict[Optional[str], List[int]]): Data to plot.
            First is the series name, second are the samples (gem cost).
        title (str, optional): Figure title. Defaults to "Title".
        dpi (int, optional): Figure dpi. Defaults to 300.
        ticks (List[float], optional): X-Axis ticks. Defaults to None.
        save_figure (Optional[Path], optional): Location to save figure to. Defaults to None.
        show_hist (bool, optional): Optionall show the plot at the end. Defaults to False.
    """
    plt.style.use("dark_background")
    plt.figure(title, dpi=dpi)
    ax = sb.histplot(
        data,
        stat="density",
        alpha=0.5,
        kde=True,
        edgecolor="k",
        linewidth=0,
        cumulative=True,
        discrete=True,
        common_bins=False,
        common_norm=False,
        legend=True,
    )
    ax.xaxis.grid(visible=True, which="minor", alpha=0.15, linestyle="-.")
    ax.xaxis.grid(visible=True, which="major", alpha=0.8)
    ax.yaxis.grid(visible=True, which="major", alpha=0.3)
    ax.xaxis.set_major_formatter(plt.FormatStrFormatter("%dk"))
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1))
    ax.set_yticks([0.25, 0.50, 0.75, 1.0])
    if ticks:
        ax.set_xticks(ticks)
        ax.set_xticks(list(range(0, math.ceil(max(ticks)))), minor=True)
    plt.ylabel("Probability of obtaining all")
    plt.xlabel("Gems spent")
    avg: float = 0
    for series in data.values():
        avg = sum(series) / len(series)
        break
    plt.title(f"{title} (Ø{avg*1000:.0f} gems)")
    if save_figure:
        path = Path(save_figure)
        path.parent.mkdir(exist_ok=True)
        plt.savefig(str(path), transparent=True)
    if show_hist:
        plt.show()
