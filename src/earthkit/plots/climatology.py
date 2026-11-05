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
Shortcuts for climatology (annual-cycle) plots.

Examples
--------
>>> import earthkit.plots as ekp
>>> ekp.climatology.line(data)
>>> ekp.climatology.bar(data, color="steelblue")
"""

from earthkit.plots.quickplot import climatology as _climatology

__all__ = [
    "line",
    "scatter",
    "bar",
    "fill_between",
]


def line(*args, **kwargs):
    """
    Plot an annual cycle as lines.

    Equivalent to the ``climatology`` quickplot function with
    ``plot="line"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.climatology`.
    """
    return _climatology(*args, plot="line", **kwargs)


def scatter(*args, **kwargs):
    """
    Plot an annual cycle as scatter points.

    Equivalent to the ``climatology`` quickplot function with
    ``plot="scatter"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.climatology`.
    """
    return _climatology(*args, plot="scatter", **kwargs)


def bar(*args, **kwargs):
    """
    Plot an annual cycle as bars.

    Equivalent to the ``climatology`` quickplot function with
    ``plot="bar"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.climatology`.
    """
    return _climatology(*args, plot="bar", **kwargs)


def fill_between(*args, **kwargs):
    """
    Fill the area between two annual-cycle curves.

    Equivalent to the ``climatology`` quickplot function with
    ``plot="fill_between"``.  Accepts all parameters of
    :func:`earthkit.plots.quickplot.climatology`.
    """
    return _climatology(*args, plot="fill_between", **kwargs)
