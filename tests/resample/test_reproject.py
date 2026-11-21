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

import cartopy.crs as ccrs
import numpy as np
import pytest

from earthkit.plots.resample.reproject import reproject_to_grid


def _target_bbox(crs):
    x, y = crs.transform_points(ccrs.PlateCarree(), np.array([-20.0, 30.0]), np.array([35.0, 70.0]))[:, :2].T
    return x.min(), x.max(), y.min(), y.max()


@pytest.mark.parametrize("value", [100.0, -2.5])
def test_reproject_to_grid_constant_field_stays_constant(value):
    lon = np.arange(-30.0, 40.01, 1.0)
    lat = np.arange(30.0, 75.01, 1.0)
    z = np.full((lat.size, lon.size), value)
    crs = ccrs.LambertConformal(10, 50)

    _, _, z_tgt = reproject_to_grid(lon, lat, z, ccrs.PlateCarree(), _target_bbox(crs), crs, nx=400, ny=400)

    valid = z_tgt[~np.isnan(z_tgt)]
    assert valid.size > 0
    assert np.all(valid == value)
