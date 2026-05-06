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
import earthkit.data as ekd
import pytest

import earthkit.plots as ekp
from earthkit.plots import schema


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_healpix_contourf_with_grid_points():
    data = ekd.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = ekp.Map(domain=["France", "Spain"])
    chart.contourf(
        data,
        levels=np.arange(0, 20, 0.5),
        colors="Spectral_r",
        units="celsius",
    )
    chart.grid_points(data)
    chart.title()
    chart.legend()
    chart.coastlines()
    chart.borders()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_healpix_grid_cells_with_grid_points():
    data = ekd.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = ekp.Map(domain=["France", "Spain"])
    chart.grid_cells(
        data,
        levels=np.arange(0, 20, 0.5),
        colors="Spectral_r",
        units="celsius",
    )
    chart.grid_points(data)
    chart.title()
    chart.legend()
    chart.coastlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_healpix_point_cloud():
    data = ekd.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = ekp.Map(domain=["France", "Spain"])
    chart.point_cloud(
        data,
        levels=np.arange(0, 20, 0.5),
        colors="Spectral_r",
        units="celsius",
    )
    chart.title()
    chart.legend()
    chart.coastlines()
    return chart.fig
