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
def test_temperature_pressure_USA():
    temperature, pressure = earthkit.data.from_source("sample", "era5-2t-msl-1985122512.grib").to_fieldlist()
    chart = earthkit.plots.Map(domain="USA")
    chart.plot(temperature, units="celsius")
    chart.plot(pressure, units="hPa")

    chart.legend(location="right")

    chart.coastlines()

    chart.title()
    chart.gridlines()

    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_temperature_pressure_NewZealand():
    temperature, pressure = earthkit.data.from_source("sample", "era5-2t-msl-1985122512.grib").to_fieldlist()
    chart = earthkit.plots.Map(domain="New Zealand")
    chart.plot(temperature, units="celsius")
    chart.plot(pressure, units="hPa")

    chart.legend(location="right")

    chart.coastlines()

    chart.title()
    chart.gridlines()

    return chart.fig
