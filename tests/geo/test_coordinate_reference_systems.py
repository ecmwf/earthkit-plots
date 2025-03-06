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

from earthkit.plots.geo import coordinate_reference_systems


def test_dict_to_crs():
    crs_dict = {"name": "PlateCarree", "central_longitude": 50}
    crs = ccrs.PlateCarree(central_longitude=50)
    assert coordinate_reference_systems.dict_to_crs(crs_dict) == crs


def test_string_to_crs():
    assert coordinate_reference_systems.string_to_crs("Robinson") == ccrs.Robinson()


def test_parse_None():
    assert coordinate_reference_systems.parse_crs(None) is None


def test_parse_string():
    assert coordinate_reference_systems.parse_crs("OSGB") == ccrs.OSGB()


def test_parse_dict():
    crs_dict = {
        "name": "LambertAzimuthalEqualArea",
        "central_latitude": 52,
        "central_longitude": 10,
        "false_easting": 4321000,
        "false_northing": 3210000,
    }
    crs = ccrs.LambertAzimuthalEqualArea(
        central_latitude=52,
        central_longitude=10,
        false_easting=4321000,
        false_northing=3210000,
    )
    assert coordinate_reference_systems.parse_crs(crs_dict) == crs


def test_parse_ccrs():
    assert coordinate_reference_systems.parse_crs(ccrs.OSGB()) == ccrs.OSGB()


def test_is_cylindrical_True():
    crs = ccrs.PlateCarree(central_longitude=90)
    assert coordinate_reference_systems.is_cylindrical(crs)


def test_is_cylindrical_False():
    crs = ccrs.NorthPolarStereo()
    assert not coordinate_reference_systems.is_cylindrical(crs)
