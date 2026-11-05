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
Shortcuts for geographic / map plots.

Examples
--------
>>> import earthkit.plots as ekp
>>> ekp.geo.contourf(data, domain="Europe")
>>> ekp.geo.plot(data, groupby="step", columns=4)
>>> ekp.geo.spaghetti(data, levels=5400, domain="Europe")
"""

from earthkit.plots.quickplot import (
    barbs,
    choropleth,
    contour,
    contourf,
    grid_cells,
    grid_points,
    pcolormesh,
    plot,
    point_cloud,
    quickplot,
    quiver,
    rgb_composite,
    spaghetti,
    streamplot,
)

__all__ = [
    "plot",
    "contourf",
    "contour",
    "pcolormesh",
    "grid_cells",
    "grid_points",
    "point_cloud",
    "rgb_composite",
    "choropleth",
    "spaghetti",
    "quiver",
    "streamplot",
    "barbs",
    "quickplot",
]
