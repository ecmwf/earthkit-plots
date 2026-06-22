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

import earthkit.data as ekd
import pytest

import earthkit.plots as ekp
from earthkit.plots import schema

_DATA_URL = "https://get.ecmwf.int/repository/test-data/earthkit-regrid/test-data/global_0_360/O32.grib"


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_reduced_gg_grid_cells():
    data = ekd.from_source("url", _DATA_URL)
    chart = ekp.Map(domain="Antarctica")
    chart.grid_cells(data, units="celsius", style="auto")
    chart.grid_points(data)
    chart.title()
    chart.legend()
    chart.coastlines()
    chart.gridlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_reduced_gg_interpolated():
    data = ekd.from_source("url", _DATA_URL)
    chart = ekp.Map(domain="Antarctica")
    chart.contourf(data, units="celsius", style="auto")
    chart.grid_points(data)
    chart.title()
    chart.legend()
    chart.coastlines()
    chart.gridlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_reduced_gg_point_cloud():
    data = ekd.from_source("url", _DATA_URL)
    chart = ekp.Map(domain="Antarctica")
    chart.point_cloud(data, units="celsius", style="auto")
    chart.title()
    chart.legend()
    chart.coastlines()
    chart.gridlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_reduced_gg_all_methods_arctic():
    data = ekd.from_source("url", _DATA_URL).to_fieldlist()
    fig = ekp.Figure(rows=2, columns=2, figsize=(8, 8), domain="Arctic")
    for method in ("grid_points", "point_cloud", "grid_cells", "contourf"):
        subplot = fig.add_map()
        getattr(subplot, method)(data, units="celsius", style="auto")
        subplot.title(method)
    fig.legend(location="right")
    fig.coastlines()
    fig.gridlines()
    return fig.fig
