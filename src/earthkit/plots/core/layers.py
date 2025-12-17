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

from earthkit.plots import metadata
from earthkit.plots.metadata.formatters import LayerFormatter
from earthkit.plots.sources.core import DimensionSet
from earthkit.plots.utils import string_utils


class Layer:
    """
    A single plot Layer on a Subplot.

    Parameters
    ----------
    dimension_set : earthkit.plots.sources.core.DimensionSet
        The dimension set containing x, y, and optionally z data for plotting.
    mappable : matplotlib object
        The object that is plotted on the axes.
    subplot : earthkit.plots.components.subplots.Subplot
        The subplot on which this layer is plotted.
    style : earthkit.plots.styles.Style, optional
        The style to be applied to this layer.
    primary_axis : str, optional
        Which axis ('x', 'y', or 'z') contains the primary data for unit conversion.
    axis_units : dict, optional
        Dictionary mapping axis names to their units for display purposes.
    """

    def __init__(
        self, dimension_set, mappable, subplot, style=None, primary_axis=None, axis_units=None
    ):
        if not isinstance(dimension_set, DimensionSet):
            raise TypeError(
                f"dimension_set must be a DimensionSet, got {type(dimension_set)}"
            )
        self.dimension_set = dimension_set
        self.mappable = mappable
        self.subplot = subplot
        self.style = style
        self.primary_axis = primary_axis
        self.axis_units = axis_units or {}
        self._magnitude = None

        if hasattr(mappable, "get_facecolor"):
            self._facecolors = mappable.get_facecolor()
        else:
            self._facecolors = None

    def reset_facecolors(self):
        """
        Reset the facecolors of the mappable object.
        """
        if self._facecolors is not None:
            self.mappable.set_facecolor(self._facecolors)

    @property
    def magnitude(self):
        """
        Calculate magnitude for vector data.

        Note: This is a placeholder for future vector data support.
        Currently raises an error as vector data handling needs to be implemented.
        """
        raise NotImplementedError(
            "Vector data (magnitude calculation) is not yet supported with DimensionSet. "
            "This will be added in a future update."
        )

    @property
    def fig(self):
        """The matplotlib figure on which this layer is plotted."""
        return self.subplot.fig

    @property
    def ax(self):
        """The matplotlib axes on which this layer is plotted."""
        return self.subplot.ax

    @property
    def axes(self):
        """All matplotlib axes over which this layer is plotted."""
        return [self.ax]

    def legend(self, *args, **kwargs):
        """
        Generate a legend for this specific layer.
        """
        if self.style is not None:
            return self.style.legend(self, *args, **kwargs)

    def format_string(self, string, **kwargs):
        """
        Format a string with the layer's metadata.

        Parameters
        ----------
        string : str
            The string to be formatted. Can contain placeholders for the layer's metadata in the form of `{key}`.
        """
        return LayerFormatter(self, **kwargs).format(string)

    @property
    def _default_title_template(self):
        """
        Get the default title template based on data type (analysis vs forecast).

        Returns
        -------
        str
            The appropriate title template string.
        """
        # Check if this is analysis data (type="an") or forecast
        data_type = self.dimension_set.metadata("type")
        if data_type is None or "an" in data_type:
            template = metadata.labels.DEFAULT_ANALYSIS_TITLE
        else:
            template = metadata.labels.DEFAULT_FORECAST_TITLE
        return template


class LayerGroup:
    """
    A group of related layers.

    Parameters
    ----------
    layers : list of earthkit.maps.charts.layers.Layer objects
        A list of grouped layers.
    """

    def __init__(self, layers):
        self.layers = layers

    @property
    def subplots(self):
        """The subplots on which this layer group is plotted."""
        return [layer.subplot for layer in self.layers]

    @property
    def fig(self):
        """The matplotlib figure on which this layer group is plotted."""
        return self.subplots[0].fig

    @property
    def axes(self):
        """All matplotlib axes over which this layer group is plotted."""
        return [subplot.ax for subplot in self.subplots]

    @property
    def style(self):
        """The style to be applied to this layer group."""
        return self.layers[0].style

    def legend(self, *args, **kwargs):
        """
        Add a legend for this layer group.

        Parameters
        ----------
        *args : list
            Arguments to be passed to the style.legend method.
        **kwargs : dict
            Keyword arguments to be passed to the style.legend method.
        """
        if self.style is not None:
            return self.style.legend(
                self.fig,
                self,
                *args,
                ax=self.axes,
                **kwargs,
            )

    @property
    def mappable(self):
        """The object that is plotted on the axes."""
        return self.layers[0].mappable

    def format_string(self, string, unique=True, **kwargs):
        """
        Format a string with the layer group's metadata.

        Parameters
        ----------
        string : str
            The string to be formatted. Can contain placeholders for the layer
            group's metadata in the form of `{key}`.
        unique : bool, optional
            Whether to return only unique values for each placeholder. If False,
            all values will be returned.
        """
        results = [layer.format_string(string, **kwargs) for layer in self.layers]

        if unique:
            results = list(dict.fromkeys(results))

        result = string_utils.list_to_human(results)
        return result
