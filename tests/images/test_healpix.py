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

import earthkit.data
import pytest

import earthkit.plots
from earthkit.plots import schema


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_healpix_interpolated():
    data = earthkit.data.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = earthkit.plots.Map()
    chart.quickplot(data, units="celsius")

    chart.legend()
    chart.coastlines()
    chart.title()
    chart.gridlines()

    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_healpix_pixels():
    data = earthkit.data.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = earthkit.plots.Map(domain=["France", "Spain"])
    chart.grid_cells(data, units="celsius")

    chart.legend()

    chart.coastlines()

    chart.title()
    chart.gridlines()

    return chart.fig
