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

_PRESSURE = 700

_LEVELS = [1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0, 20.0, 30.0, 50.0, 75.0, 100.0, 200.0]
_LEVELS = [0 - level for level in _LEVELS[::-1]] + _LEVELS

_COLORS = [
    "#00004d", "#000080", "#0000b3", "#0000e6", "#0026ff", "#004dff",
    "#0073ff", "#0099ff", "#00bfff", "#00d9ff", "#33f2ff", "#73ffff",
    "#bfffff", "white", "#ffff00", "#ffea00", "#ffcc00", "#ffb300",
    "#ff9900", "#ff8000", "#ff6600", "#ff4d00", "#ff2600", "#e60000",
    "#b30000", "#800000", "#4d0000",
]


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_vorticity_over_andes():
    vorticity = ekd.from_source("sample", "ecmwf-vorticity.grib").to_fieldlist()

    style = ekp.styles.Contour(
        colors=_COLORS,
        levels=_LEVELS,
        extend="both",
        scale_factor=10**5,
        ticks=_LEVELS,
    )

    chart = ekp.Map(domain=[-80, -60, -30, -10])
    chart.contourf(vorticity.sel({"vertical.level": _PRESSURE}), style=style)
    chart.title("{variable_name} at {level} hPa")
    chart.legend(location="right")
    chart.borders()
    chart.coastlines()
    return chart.fig
