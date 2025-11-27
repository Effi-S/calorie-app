"""This module holds plotting functions using matplotlib directly.

Building Notes:
    1) Add matplotlib to requirements in buildozer.spec
        - run pip install matplotlib (checked on version 3.2.2)
        - To buildozer.spec add: requirements = matplotlib==3.2.2
"""

from __future__ import annotations

import os
import io
from typing import Optional

# Set environment variables BEFORE importing matplotlib to prevent font initialization segfaults
os.environ.setdefault('MPLBACKEND', 'Agg')
# Prevent matplotlib from trying to initialize fonts which can cause segfaults
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib-config')

# Set matplotlib backend BEFORE importing pyplot to avoid GUI initialization
# Use Agg backend which doesn't require a display
import matplotlib
matplotlib.use('Agg', force=True)  # Force Agg backend before importing pyplot

# Suppress font cache warnings that can cause issues
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', message='.*findfont.*', category=UserWarning)

# Disable font manager warnings/initialization that can cause segfaults
try:
    # Set font properties before pyplot import to avoid font manager initialization
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'
    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
except Exception:
    pass  # Ignore font setup errors

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# Disable font manager after import to prevent further font operations
try:
    plt.rcParams['font.family'] = 'DejaVu Sans'
except Exception:
    pass


def fig2img(fig: Figure):
    """Convert matplotlib Figure to Kivy Image widget.
    
    This function is kept for backward compatibility. For new code,
    consider using matplotlib Figure objects directly or fig2kivy_image().
    """
    try:
        from kivy.graphics.texture import Texture
        from kivy.uix.image import Image
        import numpy as np
    except ImportError as e:
        raise ImportError("Kivy and numpy are required for fig2img(). Use matplotlib Figure objects directly instead.") from e
    
    fig.canvas.draw()
    width, height = fig.canvas.get_width_height()
    
    # Use buffer_rgba instead of deprecated tostring_rgb
    try:
        # Try the new method first (Matplotlib 3.8+)
        # buffer_rgba() returns a numpy array with shape (height, width, 4)
        buffer_array = fig.canvas.buffer_rgba()
        # Flatten to 1D array for blit_buffer
        if hasattr(buffer_array, 'tobytes'):
            raw_data = buffer_array.tobytes()
        else:
            raw_data = np.ascontiguousarray(buffer_array).tobytes()
        colorfmt = "rgba"
    except AttributeError:
        # Fallback to old method for older matplotlib versions
        raw_data = fig.canvas.tostring_rgb()
        colorfmt = "rgb"

    # Create a Kivy texture and load the raw data
    texture = Texture.create(size=(width, height), colorfmt=colorfmt)
    texture.blit_buffer(raw_data, colorfmt=colorfmt, bufferfmt="ubyte")
    texture.flip_vertical()  # Flip the texture for correct orientation in Kivy

    # Display the texture in a Kivy Image widget
    img = Image(texture=texture)
    return img


def fig2kivy_image(fig: Figure):
    """Convert matplotlib Figure to Kivy Image widget.
    Alias for fig2img() for clarity."""
    return fig2img(fig)


_RC_PARAMS = {  # params for plotting
    "figure.facecolor": (1.0, 0.0, 0.0, 0.0),  # red   with alpha = 30%
    "axes.facecolor": (0.0, 1.0, 0.0, 0.0),  # green with alpha = 0%
    "savefig.facecolor": (0.0, 0.0, 1.0, 0.2),  # blue  with alpha = 20%
    "figure.autolayout": True,
}


def plot_pie_chart(data: dict[str, float]) -> Figure:
    """This function takes in a data dict name->quantity and returns a matplotlib Figure.
    
    Args:
        data: Dictionary mapping names to quantities
    
    Returns:
        matplotlib Figure object
    """

    plt.rcParams.update(_RC_PARAMS)
    fig, ax = plt.subplots(figsize=(24, 12))

    sum_ = sum(data.values())
    if not sum_:
        ax.pie([100], labels=["No Data"])
    else:
        data = {k: (v / sum_) * 100 for k, v in data.items()}  # values to percents

        _g = (f"{k}: {v: .1f}%" for k, v in data.items())
        ax.pie(
            data.values(), autopct=lambda *a, **k: next(_g), textprops={"color": "w"}
        )
        # ax.axis('normal')

    return fig


def plot_graph(
    data: dict[str, float],
    x_label: Optional[str] = None,
    y_label: str = "Y",
) -> Figure:
    """Plot a graph of dates to values.
    e.g. plot_graph(data = {'2022-01-11': 100,
                            '2022-01-10': 100,
                            '2022-01-09': 300}, y_label='Calories')
    
    Args:
        data: Dictionary mapping dates (strings) to values
        x_label: Optional label for x-axis
        y_label: Label for y-axis (default: "Y")
    
    Returns:
        matplotlib Figure object
    """

    plt.rcParams.update(_RC_PARAMS)
    fig, ax = plt.subplots()
    
    data = {"-".join(k.split("-")[1:]): v for k, v in data.items()}  # removing year
    if len(data) == 1:
        ax.bar(*zip(*data.items()), label=y_label)
    else:
        ax.plot(*zip(*data.items()), label=y_label)
    ax.legend()

    if x_label:
        ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    ax.grid(True)
    ax.yaxis.tick_right()
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", colors="green")
    ax.tick_params(axis="y", colors="green")

    plt.tight_layout()
    
    return fig
