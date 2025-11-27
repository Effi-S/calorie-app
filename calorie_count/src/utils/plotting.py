"""This module holds different plotting functions that are compatible kivy.

Building Notes:
    1) Add matplotlib to requirements in buildozer.spec
        - run pip install matplotlib (checked on version 3.2.2)
        - To buildozer.spec add: requirements = matplotlib==3.2.2
    2) Get matplotlib backend package to kmplot folder
            - pip install kivy.garden / sudo apt-get install kivy_garden
            - garden install matplotlib
                (any issues see:  https://www.youtube.com/watch?v=ak6HwZyj1lM&ab_channel=SkSahil)
"""

from __future__ import annotations

# from calorie_count.lib.kmplot.backend_kivyagg import FigureCanvasKivyAgg
import os
# Set environment variables BEFORE importing matplotlib to prevent font initialization segfaults
os.environ.setdefault('MPLBACKEND', 'Agg')
# Prevent matplotlib from trying to initialize fonts which can cause segfaults
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib-config')
# Disable font cache to prevent segfaults
os.environ.setdefault('MPL_FONTCONFIG', '0')

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
# Disable font manager after import to prevent further font operations
try:
    plt.rcParams['font.family'] = 'DejaVu Sans'
except Exception:
    pass

# Import Kivy components - these may cause segfaults in headless environments
# but are required for the plotting functions
try:
    from kivy.graphics.texture import Texture
    from kivy.uix.image import Image
except (ImportError, RuntimeError, SystemError) as e:
    # If Kivy can't be imported or initialized, we can't use these functions
    # This will cause an error if someone tries to use the plotting functions
    # but prevents segfaults during import
    Texture = None
    Image = None


def fig2img(fig):
    fig.canvas.draw()
    width, height = fig.canvas.get_width_height()
    
    # Use buffer_rgba instead of deprecated tostring_rgb
    try:
        # Try the new method first (Matplotlib 3.8+)
        raw_data = fig.canvas.buffer_rgba()
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


_RC_PARAMS = {  # params for plotting
    "figure.facecolor": (1.0, 0.0, 0.0, 0.0),  # red   with alpha = 30%
    "axes.facecolor": (0.0, 1.0, 0.0, 0.0),  # green with alpha = 0%
    "savefig.facecolor": (0.0, 0.0, 1.0, 0.2),  # blue  with alpha = 20%
    "figure.autolayout": True,
}


def plot_pie_chart(data: dict[str, float]):
    """This function takes in a data dict name->quantity and returns a AKPieChart"""

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

    plt.close()  # clearing memory of plt
    return fig2img(fig)


def plot_graph(
    data: dict[str, float],
    x_label: str = None,
    y_label: str = "Y",
):
    """Plot a graph of dates to values.
    e.g. plot_graph(data = {'2022-01-11': 100,
                            '2022-01-10': 100,
                            '2022-01-09': 300}, y_label='Calories')"""

    plt.rcParams.update(_RC_PARAMS)
    data = {"-".join(k.split("-")[1:]): v for k, v in data.items()}  # removing year
    if len(data) == 1:
        plt.bar(*zip(*data.items()), label=y_label)
    else:
        plt.plot(*zip(*data.items()), label=y_label)
    plt.legend()

    if x_label:
        plt.xlabel(x_label)

    ax = plt.gca()
    ax.grid(True)
    ax.yaxis.tick_right()
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", colors="green")
    ax.tick_params(axis="y", colors="green")

    plt.tight_layout()
    canvas = fig2img(plt.gcf())
    plt.close()  # clearing memory of plt
    return canvas
