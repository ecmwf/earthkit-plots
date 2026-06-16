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
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_global_ll():
    data = ekd.from_source("sample", "era5-monthly-mean-2t-199312.grib")
    chart = ekp.Map()
    chart.contourf(data, units="celsius", style="auto")
    chart.title("ERA5 monthly averaged {variable_name} over {domain} - {time:%B %Y}")

    chart.coastlines()
    chart.borders()
    chart.gridlines()

    chart.legend(label="{variable_name} ({units})")

    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_global_ll_robinson():
    data = ekd.from_source("sample", "era5-monthly-mean-2t-199312.grib")
    chart = ekp.Map(crs="Robinson")
    chart.contourf(data, units="celsius", style="auto")
    chart.title("ERA5 monthly averaged {variable_name} over {domain} - {time:%B %Y}")

    chart.coastlines()
    chart.borders()
    chart.gridlines()

    chart.legend(label="{variable_name} ({units})")

    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_global_ll_europe():
    data = ekd.from_source("sample", "era5-monthly-mean-2t-199312.grib")
    chart = ekp.Map(domain="europe")
    chart.contourf(data, units="celsius", style="auto")
    chart.title("ERA5 monthly averaged {variable_name} over {domain} - {time:%B %Y}")

    chart.coastlines()
    chart.borders()
    chart.gridlines()

    chart.legend(label="{variable_name} ({units})")

    return chart.fig
