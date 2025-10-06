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
import pytest

from earthkit.plots.geo import optimisers


def test_CRSOptimiser_area_global():
    optimiser = optimisers.CRSOptimiser([-180, 180, -90, 90])
    assert optimiser.area == 64800


def test_CRSOptimiser_area_equatorial():
    optimiser = optimisers.CRSOptimiser([-40, 10, -20, 30])
    assert optimiser.area == 2500


def test_CRSOptimiser_area_northern_hemisphere():
    optimiser = optimisers.CRSOptimiser([-20, 20, 30, 70])
    assert optimiser.area == 1600


def test_CRSOptimiser_area_zero():
    optimiser = optimisers.CRSOptimiser([50, 50, -90, 90])
    assert optimiser.area == 0


def test_CRSOptimiser_area_wrap_north_pole():
    optimiser = optimisers.CRSOptimiser([-20, 30, 85, 85])
    assert optimiser.area == 500


def test_CRSOptimiser_area_wrap_south_pole():
    optimiser = optimisers.CRSOptimiser([-20, 30, -80, -80])
    assert optimiser.area == 1000


def test_CRSOptimiser_ratio_globe():
    optimiser = optimisers.CRSOptimiser([-180, 180, -90, 90])
    assert optimiser.ratio == 2


def test_CRSOptimiser_ratio_equal():
    optimiser = optimisers.CRSOptimiser([-90, 90, -90, 90])
    assert optimiser.ratio == 1


def test_CRSOptimiser_ratio_wrap_pole():
    optimiser = optimisers.CRSOptimiser([-20, 20, 80, 80])
    assert optimiser.ratio == 2


def test_CRSOptimiser_standard_parallels_europe():
    optimiser = optimisers.CRSOptimiser([-20, 40, 32, 72])
    assert optimiser.standard_parallels == (38.4, 65.6)


def test_CRSOptimiser_standard_parallels_australia():
    optimiser = optimisers.CRSOptimiser([113, 153, -45, -10])
    assert optimiser.standard_parallels == pytest.approx((-39.4, -15.6))


def test_CRSOptimiser_min_lon():
    optimiser = optimisers.CRSOptimiser([-20, 40, 30, 70])
    assert optimiser.min_lon == -20


def test_CRSOptimiser_max_lon():
    optimiser = optimisers.CRSOptimiser([-20, 40, 30, 70])
    assert optimiser.max_lon == 40


def test_CRSOptimiser_max_lon_wrapped():
    optimiser = optimisers.CRSOptimiser([-20, -40, 30, 70])
    assert optimiser.max_lon == 320


def test_CRSOptimiser_min_lat():
    optimiser = optimisers.CRSOptimiser([-20, 40, 30, 70])
    assert optimiser.min_lat == 30


def test_CRSOptimiser_max_lat():
    optimiser = optimisers.CRSOptimiser([-20, 40, 30, 70])
    assert optimiser.max_lat == 70


def test_CRSOptimiser_central_lat():
    optimiser = optimisers.CRSOptimiser([-20, 40, 30, 70])
    assert optimiser.central_lat == 50


def test_CRSOptimiser_central_lon():
    optimiser = optimisers.CRSOptimiser([-20, 40, 30, 70])
    assert optimiser.central_lon == 10


def test_CRSOptimiser_is_landscape():
    optimiser = optimisers.CRSOptimiser([-20, 40, 30, 40])
    assert optimiser.is_landscape()
    assert not optimiser.is_portrait()
    assert not optimiser.is_square()


def test_CRSOptimiser_is_landscape_near_square_threshold():
    optimiser = optimisers.CRSOptimiser([-20, 40, 0, 49.5])
    assert optimiser.is_landscape()
    assert not optimiser.is_portrait()
    assert not optimiser.is_square()


def test_CRSOptimiser_is_square_at_landscape_threshold():
    optimiser = optimisers.CRSOptimiser([-20, 40, 0, 50])
    assert optimiser.is_square()
    assert not optimiser.is_landscape()
    assert not optimiser.is_portrait()


def test_CRSOptimiser_is_square():
    optimiser = optimisers.CRSOptimiser([-20, 40, 0, 60])
    assert optimiser.is_square()
    assert not optimiser.is_landscape()
    assert not optimiser.is_portrait()


def test_CRSOptimiser_is_square_at_portrait_threshold():
    optimiser = optimisers.CRSOptimiser([-20, 40, 0, 75])
    assert optimiser.is_square()
    assert not optimiser.is_landscape()
    assert not optimiser.is_portrait()


def test_CRSOptimiser_is_portrait_near_square_threshold():
    optimiser = optimisers.CRSOptimiser([-20, 40, 0, 75.5])
    assert optimiser.is_portrait()
    assert not optimiser.is_landscape()
    assert not optimiser.is_square()


def test_CRSOptimiser_is_portrait():
    optimiser = optimisers.CRSOptimiser([-20, 40, 10, 90])
    assert optimiser.is_portrait()
    assert not optimiser.is_landscape()
    assert not optimiser.is_square()


def test_CRSOptimiser_is_global_global():
    optimiser = optimisers.CRSOptimiser([-180, 180, -90, 90])
    assert optimiser.is_global()


def test_CRSOptimiser_is_global_very_large():
    optimiser = optimisers.CRSOptimiser([-120, 120, -90, 90])
    assert optimiser.is_global()


def test_CRSOptimiser_is_large_global_threshold():
    optimiser = optimisers.CRSOptimiser([-108, 108, -90, 90])
    assert optimiser.is_large()


def test_CRSOptimiser_is_large():
    optimiser = optimisers.CRSOptimiser([-100, 100, -80, 70])
    assert optimiser.is_large()


def test_CRSOptimiser_is_large_near_small_threshold():
    optimiser = optimisers.CRSOptimiser([0, 72.5, -90, 90])
    assert optimiser.is_large()


def test_CRSOptimiser_is_small_at_large_threshold():
    optimiser = optimisers.CRSOptimiser([0, 72, -90, 90])
    assert optimiser.is_small()


def test_CRSOptimiser_is_small():
    optimiser = optimisers.CRSOptimiser([-5, 10, -10, 5])
    assert optimiser.is_small()


def test_CRSOptimiser_is_polar():
    optimiser = optimisers.CRSOptimiser([-180, 180, 85, 85])
    assert optimiser.is_polar()


def test_CRSOptimiser_is_polar_near_threshold():
    optimiser = optimisers.CRSOptimiser([-180, 180, 61, 90])
    assert optimiser.is_polar()


def test_CRSOptimiser_is_not_polar_at_threshold():
    optimiser = optimisers.CRSOptimiser([-180, 180, 60, 90])
    assert not optimiser.is_polar()


def test_CRSOptimiser_is_equatorial():
    optimiser = optimisers.CRSOptimiser([-30, 70, -20, 30])
    assert optimiser.is_equatorial()


def test_CRSOptimiser_is_equatorial_near_threshold():
    optimiser = optimisers.CRSOptimiser([-30, 70, 0, 49])
    assert optimiser.is_equatorial()


def test_CRSOptimiser_is_not_equatorial_at_threshold():
    optimiser = optimisers.CRSOptimiser([-30, 70, 0, 50])
    assert not optimiser.is_equatorial()


def test_CRSOptimiser_crs_global():
    optimiser = optimisers.CRSOptimiser([-180, 180, -90, 90])
    assert optimiser.crs == ccrs.PlateCarree()
