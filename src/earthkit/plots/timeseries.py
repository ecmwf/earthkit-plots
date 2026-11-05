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
Shortcuts for time series plots.

Examples
--------
>>> import earthkit.plots as ekp
>>> ekp.timeseries.line(data, x="valid_time", groupby="step")
>>> ekp.timeseries.multiboxplot(data, units="celsius")
"""

from earthkit.plots.quickplot import timeseries as _timeseries

__all__ = [
    "line",
    "scatter",
    "bar",
    "fill_between",
    "multiboxplot",
    "stripes",
]


def line(*args, **kwargs):
    """
    Plot one or more time series as lines.

    Equivalent to the ``timeseries`` quickplot function with
    ``plot="line"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.timeseries`.
    """
    return _timeseries(*args, plot="line", **kwargs)


def scatter(*args, **kwargs):
    """
    Plot time series data as scatter points.

    Equivalent to the ``timeseries`` quickplot function with
    ``plot="scatter"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.timeseries`.
    """
    return _timeseries(*args, plot="scatter", **kwargs)


def bar(*args, **kwargs):
    """
    Plot time series data as bars.

    Equivalent to the ``timeseries`` quickplot function with
    ``plot="bar"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.timeseries`.
    """
    return _timeseries(*args, plot="bar", **kwargs)


def fill_between(*args, **kwargs):
    """
    Fill the area between two time series curves.

    Equivalent to the ``timeseries`` quickplot function with
    ``plot="fill_between"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.timeseries`.
    """
    return _timeseries(*args, plot="fill_between", **kwargs)


def multiboxplot(*args, **kwargs):
    """
    Plot an ensemble spread as a multiboxplot (letter-value plot).

    Equivalent to the ``timeseries`` quickplot function with
    ``plot="multiboxplot"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.timeseries`.
    """
    return _timeseries(*args, plot="multiboxplot", **kwargs)


def stripes(*args, **kwargs):
    """
    Plot climate stripes.

    Draws one vertical colored bar per data point, colored by value
    through the given (or auto-detected) style.

    Equivalent to the ``timeseries`` quickplot function with
    ``plot="stripes"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.timeseries`.
    """
    return _timeseries(*args, plot="stripes", **kwargs)
