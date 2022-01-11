"""This module holds different plotting functions that are compatible kivy."""
from __future__ import annotations

from kivymd_extensions.akivymd.uix.charts import AKPieChart
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt


def plot_pie_chart(data: dict[str, float]) -> AKPieChart:
    """This function takes in a data dict name->quantity and returns a AKPieChart"""
    sum_values = sum(data.values())
    data = {k: (v / sum_values) * 100 for k, v in data.items()}
    sum_values = sum(data.values())
    leftover = 100 - sum_values
    data[list(data.keys())[-1]] += leftover
    print(data)

    chart = AKPieChart(
        items=[data],
    )
    return chart


def plot_graph(data: dict[str, float],
               x_label: str = None, y_label: str = 'Y',
               ) -> FigureCanvasKivyAgg:
    """Plot a graph of dates to values.
    e.g. plot_graph(data = {'2022-01-11': 100,
                            '2022-01-10': 100,
                            '2022-01-09': 300}, y_label='Calories')"""

    plt.rcParams.update({
        "figure.facecolor": (1.0, 0.0, 0.0, 0.0),  # red   with alpha = 30%
        "axes.facecolor": (0.0, 1.0, 0.0, 0.0),  # green with alpha = 0%
        "savefig.facecolor": (0.0, 0.0, 1.0, 0.2),  # blue  with alpha = 20%
        "figure.autolayout": True
    })
    data = {'-'.join(k.split('-')[1:]): v for k, v in data.items()}  # removing year
    plt.plot(*zip(*data.items()), label=y_label)
    plt.legend()

    if x_label:
        plt.xlabel(x_label)

    ax = plt.gca()
    ax.grid(True)
    ax.yaxis.tick_right()
    ax.xaxis.tick_top()
    ax.tick_params(axis='x', colors='green')
    ax.tick_params(axis='y', colors='green')

    plt.tight_layout()
    canvas = FigureCanvasKivyAgg(plt.gcf())
    plt.close()  # clearing memory of plt
    return canvas

