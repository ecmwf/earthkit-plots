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

import numpy as np
import matplotlib.patches

import itertools


def bandplot(ax, x, y, colors=None, *args, **kwargs):
    if isinstance(colors, str) or colors is None:
        colors = [colors]

    c = itertools.cycle(colors)
    for i in range(y.shape[0] - 1):
        ax.fill_between(x, y[i], y[i + 1], *args, color=next(c), **kwargs)



def boxplot(ax, x, y, width=None, colors=None, whiskers=True, capfrac=0.618, **kwargs):
    # Autoscale with based on data if not explicitly set
    width = width if width is not None else np.min(np.diff(x))*0.5

    if isinstance(colors, str) or colors is None:
        colors = [colors]

    ny = y.shape[0]

    def add_rect(*args, **kwargs):
        options = {"edgecolor": "black"}
        options.update(kwargs)
        ax.add_patch(matplotlib.patches.Rectangle(*args, **options))

    # Widths for the boxes. Plot whiskers (and other lines) as 0-width
    # or height rectangles to maintain zorder as plotting order.
    whisker_width = 0. if whiskers else 0.382
    widths = width * np.linspace(whisker_width, 1., ny // 2)
    widths = np.concat([widths, widths[-2+(ny%2)::-1]])

    cap_width = width * capfrac

    for j, xc in enumerate(x):
        color = itertools.cycle(colors)
        for yt, yb, width in zip(y[:-1,j], y[1:,j], widths):
            add_rect((xc - 0.5*width, yb), width, yt - yb, facecolor=next(color), **kwargs)

        if ny == 1:
            raise NotImplementedError
        # Draw caps at the end of whiskers
        elif whiskers:
            add_rect((xc - 0.5*cap_width, y[0,j]), cap_width, 0, **kwargs)
            add_rect((xc - 0.5*cap_width, y[-1,j]), cap_width, 0, **kwargs)

    ax.autoscale_view()
