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

from earthkit.plots.geo import bounds


def test_BoundingBox():
    bbox = bounds.BoundingBox(-180, 180, -90, 90, crs=ccrs.PlateCarree())
    assert bbox.x_min == -180
    assert bbox.x_max == 180
    assert bbox.y_min == -90
    assert bbox.y_max == 90
    assert bbox.crs == ccrs.PlateCarree()


def test_BoundingBox_Lambert():
    bbox = bounds.BoundingBox(-2e6, 3e6, 3e6, 7e6, crs=ccrs.LambertAzimuthalEqualArea())
    assert bbox.x_min == -2e6
    assert bbox.x_max == 3e6
    assert bbox.y_min == 3e6
    assert bbox.y_max == 7e6
    assert bbox.crs == ccrs.LambertAzimuthalEqualArea()


def test_BoundingBox_iter():
    bbox = bounds.BoundingBox(-180, 180, -90, 90)
    assert list(bbox) == [-180, 180, -90, 90]


def test_BoundingBox_nsew():
    bbox = bounds.BoundingBox(-180, 180, -90, 90)
    assert bbox.west == -180
    assert bbox.east == 180
    assert bbox.south == -90
    assert bbox.north == 90


def test_BoundingBox_to_cartopy_bounds():
    bbox = bounds.BoundingBox(-25, 40, -10, 35)
    assert bbox.to_cartopy_bounds() == (-25, 40, -10, 35)


def test_BoundingBox_to_bbox():
    bbox = bounds.BoundingBox(-25, 40, 34, 72)
    new_bbox = bbox.to_bbox(ccrs.LambertAzimuthalEqualArea())
    assert new_bbox.x_min == pytest.approx(-2390669)
    assert new_bbox.x_max == pytest.approx(3763307)
    assert new_bbox.y_min == pytest.approx(3715828)
    assert new_bbox.y_max == pytest.approx(7690470)
    assert new_bbox.crs == ccrs.LambertAzimuthalEqualArea()


def test_BoundingBox_to_optimised_bbox_global():
    bbox = bounds.BoundingBox(-180, 180, -90, 90, crs=ccrs.PlateCarree())
    optimised_bbox = bbox.to_optimised_bbox()
    assert optimised_bbox.x_min == -180
    assert optimised_bbox.x_max == 180
    assert optimised_bbox.y_min == -90
    assert optimised_bbox.y_max == 90
    assert optimised_bbox.crs == ccrs.PlateCarree()


def test_BoundingBox_to_optimised_bbox_0_360():
    bbox = bounds.BoundingBox(0, 360, -90, 90, crs=ccrs.PlateCarree())
    optimised_bbox = bbox.to_optimised_bbox()
    assert optimised_bbox.x_min == pytest.approx(-180)
    assert optimised_bbox.x_max == pytest.approx(180)
    assert optimised_bbox.y_min == pytest.approx(-90)
    assert optimised_bbox.y_max == pytest.approx(90)
    assert optimised_bbox.crs == ccrs.PlateCarree(central_longitude=180)


def test_BoundingBox_to_optimised_bbox_europe():
    bbox = bounds.BoundingBox(-25, 40, 34, 72)
    optimised_bbox = bbox.to_optimised_bbox()

    assert optimised_bbox.x_min == pytest.approx(-2968299)
    assert optimised_bbox.x_max == pytest.approx(2968299)
    assert optimised_bbox.y_min == pytest.approx(-2126073)
    assert optimised_bbox.y_max == pytest.approx(2386970)

    assert optimised_bbox.crs == ccrs.AlbersEqualArea(
        central_latitude=53,
        central_longitude=7.5,
        standard_parallels=(40.08, 65.92),
    )


def test_BoundingBox_to_latlon_bbox():
    bbox = bounds.BoundingBox(-2e6, 3e6, 3e6, 7e6, crs=ccrs.LambertAzimuthalEqualArea())
    new_bbox = bbox.to_latlon_bbox()
    assert new_bbox.x_min == pytest.approx(-36.64, 1e-2)
    assert new_bbox.x_max == pytest.approx(52.96, 1e-2)
    assert new_bbox.y_min == pytest.approx(26.49, 1e-2)
    assert new_bbox.y_max == pytest.approx(66.68, 1e-2)
    assert new_bbox.crs == ccrs.PlateCarree()


def test_BoundingBox_from_bbox_0_360():
    bbox = bounds.BoundingBox.from_bbox((0, 360, -90, 90))
    assert bbox.x_min == pytest.approx(-180)
    assert bbox.x_max == pytest.approx(180)
    assert bbox.y_min == pytest.approx(-90)
    assert bbox.y_max == pytest.approx(90)
    assert bbox.crs == ccrs.PlateCarree(central_longitude=180)


def test_BoundingBox_contains_point():
    bbox = bounds.BoundingBox(-10, 10, -10, 10)
    assert bbox.contains_point((0, 0))
    assert bbox.contains_point((-10, 10))
    assert not bbox.contains_point((-11, 10))
    assert not bbox.contains_point((-10, 11))


def test_BoundingBox_addition():
    bbox_1 = bounds.BoundingBox(-10, 10, -10, 10)
    bbox_2 = bounds.BoundingBox(0, 11, -12, 12)
    assert list(bbox_1 + bbox_2) == [-10, 11, -12, 12]
