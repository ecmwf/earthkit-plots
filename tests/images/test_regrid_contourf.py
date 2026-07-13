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
from earthkit.plots.resample import Regrid


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
def test_regrid_contourf_lambert_azimuthal():
    # Regression test for the vertical-streak artifact produced when a bare
    # Regrid() (no trailing pixel-sampler) feeds contourf on a non-cylindrical
    # projection.  The Europe domain uses Lambert Azimuthal Equal Area; with
    # transform_first=True cartopy pre-projects the dense 0.5° lat/lon mesh
    # and triangulates it in projected space, collapsing it into vertical
    # slivers.  The schema default transform_first="auto" must resolve to
    # False for curved target projections so this renders correctly.
    data = ekd.from_source("sample", "healpix-h128-nested-2t.grib")

    chart = ekp.Map(domain="Europe")

    chart.contourf(
        data,
        resample=Regrid(resolution=0.5),
        style=ekp.styles.Style(
            levels=range(240, 310, 5),
            colors="Spectral_r",
        ),
    )

    chart.coastlines()
    chart.gridlines()
    chart.legend()

    return chart.fig
