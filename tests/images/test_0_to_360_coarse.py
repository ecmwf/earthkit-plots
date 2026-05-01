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


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_0_360_grid_cells():
    ds = ekd.from_source("sample", "lsp_step_range.grib2").to_fieldlist()

    chart = ekp.Map()

    chart.grid_cells(ds)
    chart.coastlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_0_360_grid_cells_robinson():
    ds = ekd.from_source("sample", "lsp_step_range.grib2").to_fieldlist()

    chart = ekp.Map(crs="Robinson")

    chart.grid_cells(ds)
    chart.coastlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_0_360_point_cloud():
    ds = ekd.from_source("sample", "lsp_step_range.grib2").to_fieldlist()

    chart = ekp.Map()

    chart.point_cloud(ds)
    chart.coastlines()
    return chart.fig
