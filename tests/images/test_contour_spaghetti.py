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

# Same data as the contour-spaghetti tutorial example
_LEVELS = [12500]


def _z_en():
    ds_en = ekd.from_source("sample", "ens_storm_st_jude.grib")
    return ds_en.to_fieldlist().sel({"parameter.variable": "z", "vertical.level": 850, "time.step": 78})


def _spaghetti_chart(data, highlight):
    chart = ekp.Map(figsize=(7, 7))
    chart.spaghetti(data, levels=_LEVELS, highlight=highlight, label="Ensemble members")
    chart.land()
    chart.coastlines()
    chart.borders()
    chart.gridlines()
    chart.title("{variable_name} {level} hPa")
    chart.legend()
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_spaghetti_fieldlist():
    return _spaghetti_chart(_z_en(), highlight={"metadata.dataType": "cf"})


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_spaghetti_xarray_dataset():
    # Regression test for #260: an xarray ensemble must plot one line per member
    return _spaghetti_chart(_z_en().to_xarray(), highlight={"member": "0"})


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_spaghetti_xarray_dataarray():
    return _spaghetti_chart(_z_en().to_xarray()["z"], highlight={"member": "0"})
