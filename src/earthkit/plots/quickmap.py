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

import warnings

from earthkit.plots.components.figures import Figure
from earthkit.plots.schemas import schema


def _quickmap(function):
    def wrapper(*args, return_subplot=False, domain=None, **kwargs):
        warnings.warn(
            "The quickmap module is deprecated and will be removed in earthkit-plots 0.4. "
            "Please use the quickplot module instead."
        )
        figure = Figure()
        figure.add_map(domain=domain)
        figure._release_queue()
        subplot = figure[0]
        try:
            getattr(subplot, function.__name__)(*args, **kwargs)
        except Exception as e:
            warnings.warn(
                f"Failed to execute {function.__name__} on given data; consider "
                "constructing the plot manually."
            )
            raise e
        for method in (
            schema.quickmap_subplot_workflow + schema.quickmap_figure_workflow
        ):
            try:
                getattr(subplot, method)()
            except Exception:
                warnings.warn(
                    f"Failed to execute {method} on given data; consider "
                    "constructing the plot manually."
                )
        return subplot

    return wrapper


@_quickmap
def quickplot(*args, **kwargs):
    """Quick plot"""


plot = quickplot


@_quickmap
def line(*args, **kwargs):
    """Quick plot"""


@_quickmap
def bar(*args, **kwargs):
    """Quick plot"""


@_quickmap
def scatter(*args, **kwargs):
    """Quick plot"""


@_quickmap
def point_cloud(*args, **kwargs):
    """Quick plot"""


@_quickmap
def block(*args, **kwargs):
    """Quick plot"""


@_quickmap
def contour(*args, **kwargs):
    """Quick plot"""


@_quickmap
def contourf(*args, **kwargs):
    """Quick plot"""


@_quickmap
def quiver(*args, **kwargs):
    """Quick plot"""


@_quickmap
def barbs(*args, **kwargs):
    """Quick plot"""
