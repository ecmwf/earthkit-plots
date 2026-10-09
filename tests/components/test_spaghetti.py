# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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
import matplotlib
import numpy as np
import pytest
import xarray as xr

import earthkit.plots as ekp
from earthkit.plots.components.maps import Map

matplotlib.use("Agg")

N_MEMBERS = 5
LEVEL = 273.15


@pytest.fixture
def ensemble_da():
    """
    An ensemble DataArray with dims (number, latitude, longitude).
    """
    lat, lon = np.linspace(80, 20, 13), np.linspace(-40, 40, 17)
    values = 270 + np.random.default_rng(0).normal(0, 3, (N_MEMBERS, 13, 17))
    return xr.DataArray(
        values,
        dims=["number", "latitude", "longitude"],
        coords={"number": range(N_MEMBERS), "latitude": lat, "longitude": lon},
        name="2t",
        attrs={"units": "K"},
    )


@pytest.fixture
def ensemble_fl(ensemble_da):
    return ekd.from_object(ensemble_da).to_fieldlist()


def test_map_spaghetti_dataarray_plots_each_member(ensemble_da):
    """
    Regression test for #260: an ensemble DataArray must produce one
    contour layer per member, not a single layer for the whole array.
    """
    chart = Map()
    chart.spaghetti(ensemble_da, levels=LEVEL)

    assert len(chart.layers) == N_MEMBERS


def test_map_spaghetti_fieldlist_plots_each_member(ensemble_fl):
    chart = Map()
    chart.spaghetti(ensemble_fl, levels=LEVEL)

    assert len(chart.layers) == N_MEMBERS


def test_map_spaghetti_list_of_dataarrays(ensemble_da):
    members = [ensemble_da.isel(number=i) for i in range(N_MEMBERS)]
    chart = Map()
    chart.spaghetti(members, levels=LEVEL)

    assert len(chart.layers) == N_MEMBERS


def test_map_spaghetti_dataarray_highlight(ensemble_da):
    """Highlighting selects via xarray's own ``sel`` and adds one extra layer."""
    chart = Map()
    chart.spaghetti(ensemble_da, levels=LEVEL, highlight={"number": 0})

    assert len(chart.layers) == N_MEMBERS + 1


def test_map_spaghetti_fieldlist_highlight(ensemble_fl):
    chart = Map()
    chart.spaghetti(ensemble_fl, levels=LEVEL, highlight={"ensemble.member": 0})

    assert len(chart.layers) == N_MEMBERS + 1


def test_map_spaghetti_highlight_no_match_adds_no_layer(ensemble_da):
    chart = Map()
    chart.spaghetti(ensemble_da, levels=LEVEL, highlight={"number": []})

    assert len(chart.layers) == N_MEMBERS


def test_quickplot_spaghetti_dataarray(ensemble_da):
    chart = ekp.geo.spaghetti(ensemble_da, levels=LEVEL)

    assert len(chart.layers) == N_MEMBERS


def test_quickplot_spaghetti_fieldlist(ensemble_fl):
    chart = ekp.geo.spaghetti(ensemble_fl, levels=LEVEL)

    assert len(chart.layers) == N_MEMBERS


def test_quickplot_spaghetti_dataarray_highlight(ensemble_da):
    chart = ekp.geo.spaghetti(ensemble_da, levels=LEVEL, highlight={"number": 0})

    assert len(chart.layers) == N_MEMBERS + 1


def test_quickplot_spaghetti_multiple_inputs(ensemble_da, ensemble_fl):
    """Several positional inputs are concatenated into one set of members."""
    chart = ekp.geo.spaghetti(ensemble_da, ensemble_fl, levels=LEVEL)

    assert len(chart.layers) == 2 * N_MEMBERS
