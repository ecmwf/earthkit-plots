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
import pytest

import earthkit.plots as ekp
from earthkit.plots import schema

_RNG = np.random.default_rng(42)
_DATA = _RNG.random((15, 30))
_Y = np.linspace(-90, 90, 15)
_X = np.linspace(-180, 180, 30)


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_numpy_grid_cells():
    chart = ekp.Map()
    chart.grid_cells(_DATA, x=_X, y=_Y)
    chart.coastlines(color="white")
    chart.gridlines()
    chart.legend(label="")
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_numpy_contourf():
    chart = ekp.Map()
    chart.contourf(_DATA, x=_X, y=_Y)
    chart.coastlines(color="white")
    chart.gridlines()
    chart.legend(label="")
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_numpy_point_cloud():
    chart = ekp.Map()
    chart.point_cloud(_DATA, x=_X, y=_Y)
    chart.coastlines()
    chart.gridlines()
    chart.legend(label="")
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_numpy_grid_cells_robinson():
    chart = ekp.Map(crs="Robinson")
    chart.grid_cells(_DATA, x=_X, y=_Y)
    chart.coastlines(color="white")
    chart.gridlines()
    chart.legend(label="")
    return chart.fig
