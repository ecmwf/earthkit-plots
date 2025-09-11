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

import os
import re

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from earthkit.plots.ancillary import find_logo
from earthkit.plots.components.layers import LayerGroup
from earthkit.plots.components.layouts import rows_cols
from earthkit.plots.components.maps import Map
from earthkit.plots.components.subplots import Subplot
from earthkit.plots.metadata import formatters
from earthkit.plots.schemas import schema
from earthkit.plots.utils import string_utils


class Figure:
    """
    The overall canvas onto which subplots are drawn.

    A Figure is a container for one or more Subplots, each of which can contain
    one or more Layers. The Figure is responsible for managing the layout of
    Subplots and Layers, as well as providing methods for adding common
    elements like legends and titles.

    Parameters
    ----------
    rows : int, optional
        The number of rows in the figure.
    columns : int, optional
        The number of columns in the figure.
    size : list, optional
        The size of the figure in inches. This can be a list or tuple of two
        floats representing the width and height of the figure.
    domain : earthkit.geo.Domain, optional
        The domain of the data being plotted. This is used to set the extent
        and projection of the map.
    kwargs : dict, optional
        Additional keyword arguments to pass to matplotlib.gridspec.GridSpec.
    """

    def __init__(
        self, rows=None, columns=None, size=None, domain=None, crs=None, **kwargs
    ):
        self.rows = rows
        self.columns = columns

        self.fig = None
        self.gridspec = None

        self._row = 0
        self._col = 0

        self._figsize = self._parse_size(size)
        self._gridspec_kwargs = kwargs

        self._domain = domain
        self._crs = crs

        self.subplots = []
        self._last_subplot_location = None
        self._isubplot = 0

        self._queue = []
        self._subplot_queue = []

        self.attributions = []
        self.logos = []

        if None not in (self.rows, self.columns):
            self._setup()

    def setup(method):
        """Decorator to set up the figure before calling a method."""

        def wrapper(self, *args, **kwargs):
            self._setup()
            result = method(self, *args, **kwargs)
            return result

        return wrapper

    def _setup(self):
        self.fig = plt.figure(figsize=self._figsize, constrained_layout=True)
        self.gridspec = self.fig.add_gridspec(
            self.rows, self.columns, **self._gridspec_kwargs
        )

    def defer_until_setup(method):
        def wrapper(self, *args, **kwargs):
            if not self.subplots:
                self._queue.append((method, args, kwargs))
            else:
                return method(self, *args, **kwargs)

        return wrapper

    def defer_subplot(method):
        def wrapper(self, *args, **kwargs):
            if self.rows is None or self.columns is None:
                self._subplot_queue.append((method, args, kwargs))
            else:
                return method(self, *args, **kwargs)

        return wrapper

    def __len__(self):
        return len(self.subplots)

    def __getitem__(self, i):
        return self.subplots[i]

    def _parse_size(self, size):
        if size is not None:
            figsize = []
            for length in size:
                if isinstance(length, str):
                    if length.isnumeric():
                        length = float(length)
                    else:
                        match = re.match(r"([0-9]+)([a-z]+)", length, re.I)
                        value, units = match.groups()
                        value = float(value)
                        if units == "px":
                            length = value / schema.figure.dpi
                        elif units == "cm":
                            length = value * 2.54
                figsize.append(length)
        else:
            figsize = size
        return figsize

    def apply_to_subplots(method):
        """Decorator to apply a method to all subplots in the figure."""

        def wrapper(self, *args, **kwargs):
            success = False
            for subplot in self.subplots:
                # try:
                getattr(subplot, method.__name__)(*args, **kwargs)
                success = True
            # except (NotImplementedError, AttributeError):
            #     continue
            if not success:
                raise NotImplementedError(
                    f"No subplots have method '{method.__name__}'"
                )

        return wrapper

    def iterate_subplots(method):
        """Decorator to iterate simultaneously over data and subplots."""

        def wrapper(self, data, *args, **kwargs):
            if not hasattr(data, "__len__"):
                data = [data]
            if not self.subplots:
                self.rows, self.columns = rows_cols(
                    len(data), rows=self.rows, columns=self.columns
                )
                self._setup()
                for _ in range(len(data)):
                    self.add_map()
            for datum, subplot in zip(data, self.subplots):
                getattr(subplot, method.__name__)(datum, *args, **kwargs)

        return wrapper

    def _determine_row_column(self, row, column):
        if row is not None and column is not None:
            pass
        else:
            if self._last_subplot_location is None:
                row, column = (0, -1)
            if row is None:
                row = self._last_subplot_location[0]
            if column is None:
                column = self._last_subplot_location[1]
            if column < self.columns - 1:
                column = column + 1
            else:
                column = 0
                row = row + 1
        self._last_subplot_location = row, column
        return row, column

    def add_subplot(self, row=None, column=None, **kwargs):
        """
        Add a subplot to the figure.

        Parameters
        ----------
        row : int, optional
            The row in which to place the subplot.
        column : int, optional
            The column in which to place the subplot.
        kwargs : dict, optional
            Additional keyword arguments to pass to the Subplot constructor.
        """
        row, column = self._determine_row_column(row, column)
        subplot = Subplot(row=row, column=column, figure=self, **kwargs)
        self.subplots.append(subplot)
        return subplot

    @defer_subplot
    def add_map(self, row=None, column=None, domain=None, crs=None, **kwargs):
        """
        Add a map to the figure.

        Parameters
        ----------
        row : int, optional
            The row in which to place the subplot.
        column : int, optional
            The column in which to place the subplot.
        domain : earthkit.geo.Domain, optional
            The domain of the data being plotted. This is used to set the extent
            and projection of the map.
        kwargs : dict, optional
            Additional keyword arguments to pass to the Map constructor.
        """
        if domain is None:
            domain = self._domain
        if crs is None:
            crs = self._crs
        row, column = self._determine_row_column(row, column)
        subplot = Map(
            row=row, column=column, domain=domain, crs=crs, figure=self, **kwargs
        )
        self.subplots.append(subplot)
        return subplot

    def subplot_titles(self, *args, **kwargs):
        """
        Set the titles of all subplots.

        Parameters
        ----------
        label : str, optional
            The text to use in the title. This text can include format keys
            surrounded by `{}` curly brackets, which will extract metadata from
            your plotted data layers.
        unique : bool, optional
            If True, format keys which are uniform across subplots/layers will
            produce a single result. For example, if all data layers have the
            same `variable_name`, only one variable name will appear in the
            title.
            If False, each format key will evaluate to a list of values found
            across subplots/layers.
        kwargs : dict, optional
            Additional keyword arguments to pass to the matplotlib.pyplot.title
            method.
        """
        return [subplot.title(*args, **kwargs) for subplot in self.subplots]

    def distinct_legend_layers(self, subplots=None):
        """
        Get a list of layers with distinct styles.

        Parameters
        ----------
        subplots : list, optional
            If provided, only these subplots will be considered when identifying
            unique styles.
        """
        if subplots is None:
            subplots = self.subplots

        subplot_layers = [subplot.distinct_legend_layers for subplot in subplots]
        subplot_layers = [item for sublist in subplot_layers for item in sublist]

        groups = []
        for layer in subplot_layers:
            for i in range(len(groups)):
                if groups[i][0].style == layer.style:
                    groups[i].append(layer)
                    break
            else:
                groups.append([layer])

        groups = [LayerGroup(layers) for layers in list(groups)]

        return groups

    @defer_until_setup
    @schema.legend.apply()
    def legend(self, *args, subplots=None, location=None, **kwargs):
        """
        Add legends to the figure.

        Parameters
        ----------
        subplots : list, optional
            If provided, only these subplots will have legends.
        location : str or list, optional
            The location of the legend. If a list, each item is the location
            for the corresponding subplot.
        kwargs : dict, optional
            Additional keyword arguments to pass to the Subplot legend method.
        """
        legends = []

        anchor = None
        non_cbar_layers = []
        for i, layer in enumerate(self.distinct_legend_layers(subplots)):
            if isinstance(location, (list, tuple)):
                loc = location[i]
            else:
                loc = location
            if layer.style is not None:
                legend = layer.style.legend(
                    layer,
                    *args,
                    location=loc,
                    **kwargs,
                )
            if legend.__class__.__name__ != "Colorbar":
                non_cbar_layers.append(layer)
            else:
                anchor = layer.axes[0].get_anchor()
            legends.append(legend)

        if anchor is not None:
            for layer in non_cbar_layers:
                for ax in layer.axes:
                    ax.set_anchor(anchor)

        return legends

    @defer_until_setup
    @apply_to_subplots
    def coastlines(self, *args, **kwargs):
        """
        Add coastlines to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.coastlines`.
        """

    @defer_until_setup
    @apply_to_subplots
    def countries(self, *args, **kwargs):
        """
        Add countries to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.countries`.
        """

    @defer_until_setup
    @apply_to_subplots
    def urban_areas(self, *args, **kwargs):
        """
        Add urban areas to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.urban_areas`.
        """

    @defer_until_setup
    @apply_to_subplots
    def land(self, *args, **kwargs):
        """
        Add land polygons to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.land`.
        """

    @defer_until_setup
    @apply_to_subplots
    def borders(self, *args, **kwargs):
        """
        Add borders to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.borders`.
        """

    @defer_until_setup
    @apply_to_subplots
    def standard_layers(self, *args, **kwargs):
        """
        Add quick layers to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.quick_layers`.
        """

    @defer_until_setup
    @apply_to_subplots
    def administrative_areas(self, *args, **kwargs):
        """
        Add administrative areas to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.administrative_areas`.
        """

    @defer_until_setup
    @apply_to_subplots
    def stock_img(self, *args, **kwargs):
        """
        Add a stock image to every `Map` subplot in the figure.

        Parameters
        ----------
        Accepts the same arguments as `Map.stock_img`.
        """

    @iterate_subplots
    def block(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def gridpoints(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def plot(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def quickplot(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def pcolormesh(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def contourf(self, *args, **kwargs):
        """"""

    @iterate_subplots
    def contour(self, *args, **kwargs):
        """"""

    @defer_until_setup
    def gridlines(self, *args, sharex=True, sharey=True, **kwargs):
        """
        Add gridlines to every `Map` subplot in the figure.

        Parameters
        ----------
        sharex : bool, optional
            If True, only the bottom row of subplots will have x-axis gridlines.
        sharey : bool, optional
            If True, only the leftmost column of subplots will have y-axis
            gridlines.
        kwargs : dict, optional
            Additional keyword arguments to pass to the `Map.gridlines` method.
        """
        draw_labels = kwargs.pop("draw_labels", ["left", "bottom"])
        if draw_labels is True:
            draw_labels = ["left", "right", "bottom", "top"]
        for subplot in self.subplots:
            if draw_labels:
                subplot_draw_labels = [item for item in draw_labels]
                if sharex and all(
                    sp.domain == subplot.domain
                    for sp in [s for s in self.subplots if s.column == subplot.column]
                ):
                    if "top" in draw_labels and subplot.row != 0:
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "top"
                        ]
                    if "bottom" in draw_labels and subplot.row != max(
                        sp.row for sp in self.subplots
                    ):
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "bottom"
                        ]
                if sharey and all(
                    sp.domain == subplot.domain
                    for sp in [s for s in self.subplots if s.row == subplot.row]
                ):
                    if "left" in draw_labels and subplot.column != 0:
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "left"
                        ]
                    if "right" in draw_labels and subplot.column != max(
                        sp.column for sp in self.subplots
                    ):
                        subplot_draw_labels = [
                            loc for loc in subplot_draw_labels if loc != "right"
                        ]
            else:
                subplot_draw_labels = False
            subplot.gridlines(*args, draw_labels=subplot_draw_labels, **kwargs)

    @schema.suptitle.apply()
    def title(self, label=None, unique=True, grouped=True, y=None, **kwargs):
        """
        Add a top-level title to the chart.

        Parameters
        ----------
        label : str, optional
            The text to use in the title. This text can include format keys
            surrounded by `{}` curly brackets, which will extract metadata from
            your plotted data layers.
        unique : bool, optional
            If True, format keys which are uniform across subplots/layers will
            produce a single result. For example, if all data layers have the
            same `variable_name`, only one variable name will appear in the
            title.
            If False, each format key will evaluate to a list of values found
            across subplots/layers.
        grouped : bool, optional
            If True, a single title will be generated to represent all data
            layers, with each format key evaluating to a list where layers
            differ - e.g. `"{variable} at {time}"` might be evaluated to
            `"temperature and wind at 2023-01-01 00:00".
            If False, the title will be duplicated by the number of subplots/
            layers - e.g. `"{variable} at {time}"` might be evaluated to
            `"temperature at 2023-01-01 00:00 and wind at 2023-01-01 00:00".
        kwargs : dict, optional
            Keyword argument to matplotlib.pyplot.suptitle (see
            https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.suptitle.html#matplotlib-pyplot-suptitle
            ).
        """
        if label is None:
            label = self._default_title_template
        label = self.format_string(label, unique, grouped)

        if y is None:
            y = self._get_suptitle_y()

        result = self.fig.suptitle(label, y=y, **kwargs)
        self.draw()
        return result

    def draw(self):
        """
        Draw the figure and all its subplots.
        """
        self.fig.canvas.draw()
        for subplot in self.subplots:
            for layer in subplot.layers:
                layer.reset_facecolors()

    def _get_suptitle_y(self):
        self.draw()
        max_title_top = 0
        renderer = self.fig.canvas.get_renderer()
        inv_transform = self.fig.transFigure.inverted()

        for ax in self.fig.axes:
            # Check if the subplot has a title
            title = ax.get_title()

            if title:  # If there is a title, we need to handle the title object itself
                title_obj = ax.title
                title_bbox = title_obj.get_window_extent(renderer)
                # Convert from display coords to figure-relative coords
                bbox_fig = inv_transform.transform(title_bbox)
                max_title_top = max(max_title_top, bbox_fig[1][1])
            else:  # No title, check for other elements
                if ax.xaxis.label.get_text():
                    title_obj = ax.xaxis.label
                elif ax.yaxis.label.get_text():
                    title_obj = ax.yaxis.label
                else:
                    labels = ax.get_xticklabels()
                    if labels:
                        ticklabel_bbox = labels[0].get_window_extent(renderer)
                        ticklabel_fig_coords = inv_transform.transform(ticklabel_bbox)
                        max_title_top = max(max_title_top, ticklabel_fig_coords[1, 1])

                # If we found a title-like object, handle its bbox
                if "title_obj" in locals():
                    title_bbox = title_obj.get_window_extent(renderer)
                    bbox_fig = inv_transform.transform(title_bbox)
                    max_title_top = max(max_title_top, bbox_fig[1][1])
                    # Clean up any previous title_obj variable that was used
                    del title_obj
                else:
                    # Fallback to checking the axis position
                    max_title_top = max(max_title_top, ax.get_position().ymax)

        # Set the suptitle just above the highest title
        # Adjust the offset as needed
        return max_title_top + 0.05

    def format_string(self, string, unique=True, grouped=True):
        if not grouped:
            results = [
                subplot.format_string(string, unique, grouped)
                for subplot in self.subplots
            ]
            result = string_utils.list_to_human(results)
        else:
            result = formatters.FigureFormatter(self.subplots, unique=unique).format(
                string
            )
        return result

    @property
    def _default_title_template(self):
        return self.subplots[0]._default_title_template

    def _release_queue(self):
        if self._subplot_queue:
            self.rows, self.columns = rows_cols(
                len(self._subplot_queue), rows=self.rows, columns=self.columns
            )
            self._setup()
        for item in self._subplot_queue:
            method, args, kwargs = item
            method(self, *args, **kwargs)
        for queued_method, queued_args, queued_kwargs in self._queue:
            queued_method(self, *queued_args, **queued_kwargs)
        if self.attributions:
            attribution_text = "; ".join(self.attributions)
            x = 0.5 if not self.logos else 0.05
            y = -0.02
            ha = "center" if not self.logos else "left"

            self.fig.text(
                x,
                y,
                attribution_text,
                ha=ha,
                va="top",
                fontsize=9,
                color="gray",
                wrap=True,
            )
        if self.logos:
            # Place each logo horizontally, bottom-right, with some spacing
            logo_width = 0.12  # fraction of figure width
            logo_height = 0.05  # fraction of figure height
            spacing = 0.01  # horizontal spacing
            # Start from right, go left
            for i, image_file in enumerate(reversed(self.logos)):
                if not os.path.exists(image_file):
                    image_file = find_logo(image_file)
                logo = mpimg.imread(image_file)
                left = 1.0 - (i + 1) * logo_width - i * spacing - 0.05
                bottom = -0.05  # 0.01 margin from bottom
                ax_logo = self.fig.add_axes(
                    [left, bottom, logo_width, logo_height], zorder=100
                )
                ax_logo.imshow(logo)
                ax_logo.axis("off")
        return self

    def show(self, *args, **kwargs):
        """Display the figure."""
        self._release_queue()
        return plt.show(*args, **kwargs)

    def save(self, *args, bbox_inches="tight", **kwargs):
        """
        Save the figure to a file.

        Parameters
        ----------
        fname : str or file-like object
            The file to which to save the figure.
        bbox_inches : str, optional
            The bounding box in inches to use when saving the figure.
        kwargs : dict, optional
            Additional keyword arguments to pass to matplotlib.pyplot.savefig.
        """
        self._release_queue()
        return plt.savefig(
            *args,
            bbox_inches=bbox_inches,
            dpi=kwargs.pop("dpi", schema.figure.dpi),
            **kwargs,
        )

    def resize(self):
        self._release_queue()
        return resize_figure_to_fit_axes(self.fig)

    def add_attribution(self, attribution):
        """
        Add an attribution to the figure.

        Parameters
        ----------
        attribution : str
            The attribution text to add to the figure.
        """
        if attribution not in self.attributions:
            self.attributions.append(attribution)

    def add_logo(self, logo):
        """
        Add a logo to the figure.

        Parameters
        ----------
        logo : str
            Either the name of a built-in logo, or a path to the logo image file to add to the figure.
        """
        if logo not in self.logos:
            self.logos.append(logo)


def resize_figure_to_fit_axes(fig):
    """
    Adjust the size of a Matplotlib figure so that it fits its axes perfectly.

    Parameters:
    - fig: A Matplotlib Figure object.
    """
    # Get the current size of the figure and its DPI
    current_size = fig.get_size_inches()

    # Initialize variables to find the min/max extents of all axes
    min_left = 1.0
    max_right = 0.0
    min_bottom = 1.0
    max_top = 0.0

    # Loop through all axes to find the outer bounds
    for ax in fig.axes:
        bbox = ax.get_position()
        min_left = min(min_left, bbox.x0)
        max_right = max(max_right, bbox.x1)
        min_bottom = min(min_bottom, bbox.y0)
        max_top = max(max_top, bbox.y1)

    # Calculate new figure size
    new_width = (max_right - min_left) * current_size[0]
    new_height = (max_top - min_bottom) * current_size[1]

    # Resize figure
    fig.set_size_inches(new_width, new_height)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    return fig
