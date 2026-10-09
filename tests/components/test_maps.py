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

import matplotlib
import numpy as np
import pytest
from matplotlib.colorbar import Colorbar

from earthkit.plots.components.maps import Map

matplotlib.use("Agg")


@pytest.fixture
def squares_gdf():
    """A small GeoDataFrame of three unit squares with a numeric column."""
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import box

    return gpd.GeoDataFrame(
        {"value": [1.0, 2.0, 3.0]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)],
        crs="EPSG:4326",
    )


def test_choropleth_legend_adds_colorbar(squares_gdf):
    """Map.legend() must produce a colorbar for a choropleth layer.

    Regression test: choropleth mappables (cartopy FeatureArtist) are coloured
    via explicit facecolors and never have an array set, so a ``get_array()``
    based check wrongly skipped them and no legend was drawn.
    """
    chart = Map(domain=[-1, 4, -1, 2])
    layer = chart.choropleth(squares_gdf, z="value")
    n_axes_before = len(chart.fig.axes)

    chart.legend()

    assert isinstance(layer.legend, Colorbar)
    assert len(chart.fig.axes) == n_axes_before + 1


def test_uncoloured_quiver_legend_adds_no_colorbar():
    """An uncoloured quiver layer has a cmap but no data range, so no colorbar."""
    x = np.linspace(-10, 10, 5)
    y = np.linspace(-10, 10, 5)
    xx, yy = np.meshgrid(x, y)
    u = np.ones_like(xx)
    v = np.ones_like(yy)

    chart = Map(domain=[-10, 10, -10, 10])
    chart.quiver(x=xx, y=yy, u=u, v=v)
    n_axes_before = len(chart.fig.axes)

    chart.legend()

    assert len(chart.fig.axes) == n_axes_before
