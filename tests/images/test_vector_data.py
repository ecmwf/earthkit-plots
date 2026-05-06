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
def test_quiver():
    data = ekd.from_source("sample", "storm_ophelia_wind_850.grib")
    chart = ekp.Map(domain=[-20, 5, 40, 60])
    chart.quiver(data)
    chart.coastlines()
    chart.land()
    chart.gridlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_barbs():
    data = ekd.from_source("sample", "storm_ophelia_wind_850.grib")
    chart = ekp.Map(domain=[-20, 5, 40, 60])
    chart.barbs(data)
    chart.coastlines()
    chart.land()
    chart.gridlines()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_quiver_with_style():
    data = ekd.from_source("sample", "storm_ophelia_wind_850.grib")
    chart = ekp.Map(domain=[-20, 5, 40, 60])
    style = ekp.styles.Style(
        colors="plasma_r",
        levels=range(0, 22, 2),
        units="m s-1",
    )
    chart.quiver(data, style=style)
    chart.legend(label="wind speed ({units})", location="right")
    chart.land()
    chart.coastlines()
    chart.gridlines()
    chart.title("Storm Ophelia - {level} hPa wind speed and direction\n{time:%H:%M UTC on %-d %B %Y}")
    return chart.fig
