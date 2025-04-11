# Copyright 2024-, European Centre for Medium Range Weather Forecasts.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools

import matplotlib.patches
import numpy as np
import pandas as pd


def bandplot(ax, x, y, colors=None, *args, **kwargs):
    if isinstance(colors, str) or colors is None:
        colors = [colors]

    c = itertools.cycle(colors)
    for i in range(y.shape[0] - 1):
        ax.fill_between(x, y[i], y[i + 1], *args, color=next(c), **kwargs)


def boxplot(ax, x, y, width=None, colors=None, whiskers=True, capfrac=0.618, **kwargs):
    """Box-and-whisker plot with multiple boxes for more value intervals

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes object to plot into.
    x : array_like
        Positions of the boxes.
    y : array_like
        Values to dimension the boxes. A box-and-whisker representation is
        drawn based on the intervals defined by each column of values. The
        number of columns must match the number of x positions provided.
        Values in the column must be sorted.
    width : number
        Width of the widest box.
    colors : None | str | array_like
        Colors to fill the boxes with (in order of the y values provided).
        The sequence of colors is repeated if the number of colors provided
        is smaller than the number of boxes drawn. When drawing with whiskers,
        colors must still be provided for the associated value intervals.
    whiskers : bool
        Whether to draw the last box as a whisker.
    capfrac : number
        Width of the caps on the whiskers as a fraction of the width.
    kwargs
        Passed to `matplotlib.patches.Rectangle`.
    """
    # Autoscale with based on data if not explicitly set
    width = width if width is not None else np.min(np.diff(x)) * 0.5

    # if the width is np.timedelta-like, cast it to pandas.Timedelta in order
    # to avoid integer division issue like np.timedelta64(1, 'D') * 0.5 == np.timedelta64(0, 'D')
    # TODO: should we add pandas explicitly to the package dependencies (even though it is already a dependency via earthkit-data)?
    if np.array(width).dtype.kind == "m":
        width = pd.Timedelta(width)

    if isinstance(colors, str) or colors is None:
        colors = [colors]

    ny = y.shape[0]

    def add_rect(*args, **kwargs):
        options = {"edgecolor": "black"}
        options.update(kwargs)
        ax.add_patch(matplotlib.patches.Rectangle(*args, **options))

    # Before plotting anything on the axes ax, setup units of the x-axis
    # (inspired by seaborn boxenplot routine, where this line does the trick:
    # https://github.com/mwaskom/seaborn/blob/86b5481ca47cb46d3b3e079a5ed9b9fb46e315ef/seaborn/_base.py#L1135)
    ax.xaxis.update_units(x)

    # Widths for the boxes. Plot whiskers (and other lines) as 0-width
    # or height rectangles to maintain zorder as plotting order.
    whisker_width = 0.0 if whiskers else 0.382
    widths = width * np.linspace(whisker_width, 1.0, ny // 2)
    widths = np.concat([widths, widths[-2 + (ny % 2) :: -1]])

    cap_width = width * capfrac

    # Draw a box-and-whisker for each column
    for j, xc in enumerate(x):
        color = itertools.cycle(colors)
        # A box for each interval defined by the column
        for yt, yb, width in zip(y[:-1, j], y[1:, j], widths):
            add_rect(
                (xc - 0.5 * width, yb), width, yt - yb, facecolor=next(color), **kwargs
            )

        if ny == 1:
            raise NotImplementedError
        # Draw caps at the end of whiskers
        elif whiskers and capfrac > 0:
            add_rect((xc - 0.5 * cap_width, y[0, j]), cap_width, 0, **kwargs)
            add_rect((xc - 0.5 * cap_width, y[-1, j]), cap_width, 0, **kwargs)

    ax.autoscale_view()
