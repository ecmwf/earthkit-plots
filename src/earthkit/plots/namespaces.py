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

"""
Namespace objects for the earthkit-plots shortcut API.

These are exposed at the top level of ``earthkit.plots`` as ``ekp.geo``,
``ekp.timeseries``, and ``ekp.climatology``.  Each namespace groups the
shortcut functions that belong to a particular chart type.

Examples
--------
>>> import earthkit.plots as ekp

Geographic / map plots:

>>> ekp.geo.contourf(data, domain="Europe")
>>> ekp.geo.plot(data, groupby="step", columns=4)
>>> ekp.geo.spaghetti(data, levels=5400, domain="Europe")

Time series plots:

>>> ekp.timeseries.line(data, x="valid_time", groupby="step")
>>> ekp.timeseries.multiboxplot(data, units="celsius")

Climatology (annual-cycle) plots:

>>> ekp.climatology.line(data)
>>> ekp.climatology.bar(data, color="steelblue")
"""

from earthkit.plots import quickplot as _qp


class _GeoNamespace:
    """Shortcuts for geographic / map plots."""

    def plot(self, *args, **kwargs):
        """
        Plot geospatial data as one or more map panels.

        See :func:`earthkit.plots.quickplot.plot` for full documentation.
        """
        return _qp.plot(*args, **kwargs)

    def contourf(self, *args, **kwargs):
        """
        Plot filled contours on a map.

        See :func:`earthkit.plots.quickplot.contourf` for full documentation.
        """
        return _qp.contourf(*args, **kwargs)

    def contour(self, *args, **kwargs):
        """
        Plot contour lines on a map.

        See :func:`earthkit.plots.quickplot.contour` for full documentation.
        """
        return _qp.contour(*args, **kwargs)

    def pcolormesh(self, *args, **kwargs):
        """
        Plot a pseudocolor mesh on a map.

        See :func:`earthkit.plots.quickplot.pcolormesh` for full documentation.
        """
        return _qp.pcolormesh(*args, **kwargs)

    def grid_cells(self, *args, **kwargs):
        """
        Plot data as grid cells on a map.

        See :func:`earthkit.plots.quickplot.grid_cells` for full documentation.
        """
        return _qp.grid_cells(*args, **kwargs)

    def grid_points(self, *args, **kwargs):
        """
        Plot grid point centroids as scatter points on a map.

        See :func:`earthkit.plots.quickplot.grid_points` for full documentation.
        """
        return _qp.grid_points(*args, **kwargs)

    def point_cloud(self, *args, **kwargs):
        """
        Plot data values as a coloured point cloud on a map.

        See :func:`earthkit.plots.quickplot.point_cloud` for full documentation.
        """
        return _qp.point_cloud(*args, **kwargs)

    def rgb_composite(self, *args, **kwargs):
        """
        Plot an RGB composite image on a map.

        See :func:`earthkit.plots.quickplot.rgb_composite` for full documentation.
        """
        return _qp.rgb_composite(*args, **kwargs)

    def choropleth(self, *args, **kwargs):
        """
        Create a choropleth map from a GeoDataFrame.

        See :func:`earthkit.plots.quickplot.choropleth` for full documentation.
        """
        return _qp.choropleth(*args, **kwargs)

    def spaghetti(self, *args, **kwargs):
        """
        Plot spaghetti contours for ensemble data on a single map.

        See :func:`earthkit.plots.quickplot.spaghetti` for full documentation.
        """
        return _qp.spaghetti(*args, **kwargs)


class _TimeSeriesNamespace:
    """Shortcuts for time series plots."""

    def line(self, *args, **kwargs):
        """
        Plot one or more time series as lines.

        Equivalent to the ``timeseries`` quickplot function with
        ``plot="line"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.timeseries`.
        """
        return _qp.timeseries(*args, plot="line", **kwargs)

    def scatter(self, *args, **kwargs):
        """
        Plot time series data as scatter points.

        Equivalent to the ``timeseries`` quickplot function with
        ``plot="scatter"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.timeseries`.
        """
        return _qp.timeseries(*args, plot="scatter", **kwargs)

    def bar(self, *args, **kwargs):
        """
        Plot time series data as bars.

        Equivalent to the ``timeseries`` quickplot function with
        ``plot="bar"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.timeseries`.
        """
        return _qp.timeseries(*args, plot="bar", **kwargs)

    def fill_between(self, *args, **kwargs):
        """
        Fill the area between two time series curves.

        Equivalent to the ``timeseries`` quickplot function with
        ``plot="fill_between"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.timeseries`.
        """
        return _qp.timeseries(*args, plot="fill_between", **kwargs)

    def multiboxplot(self, *args, **kwargs):
        """
        Plot an ensemble spread as a multiboxplot (letter-value plot).

        Equivalent to the ``timeseries`` quickplot function with
        ``plot="multiboxplot"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.timeseries`.
        """
        return _qp.timeseries(*args, plot="multiboxplot", **kwargs)


class _ClimatologyNamespace:
    """Shortcuts for climatology (annual-cycle) plots."""

    def line(self, *args, **kwargs):
        """
        Plot an annual cycle as lines.

        Equivalent to the ``climatology`` quickplot function with
        ``plot="line"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.climatology`.
        """
        return _qp.climatology(*args, plot="line", **kwargs)

    def scatter(self, *args, **kwargs):
        """
        Plot an annual cycle as scatter points.

        Equivalent to the ``climatology`` quickplot function with
        ``plot="scatter"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.climatology`.
        """
        return _qp.climatology(*args, plot="scatter", **kwargs)

    def bar(self, *args, **kwargs):
        """
        Plot an annual cycle as bars.

        Equivalent to the ``climatology`` quickplot function with
        ``plot="bar"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.climatology`.
        """
        return _qp.climatology(*args, plot="bar", **kwargs)

    def fill_between(self, *args, **kwargs):
        """
        Fill the area between two annual-cycle curves.

        Equivalent to the ``climatology`` quickplot function with
        ``plot="fill_between"``.  Accepts all parameters of
        :func:`earthkit.plots.quickplot.climatology`.
        """
        return _qp.climatology(*args, plot="fill_between", **kwargs)


geo = _GeoNamespace()
timeseries = _TimeSeriesNamespace()
climatology = _ClimatologyNamespace()
