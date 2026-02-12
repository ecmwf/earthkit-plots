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

import math

import cartopy.crs as ccrs
from shapely.geometry import LineString, Point, Polygon

from earthkit.plots.geo import geometry


def test_reproject_geometries_point():

    geom = Point(10.0, 45.0)

    result = geometry.reproject_geometries(
        geometries=[geom],
        src_crs=ccrs.PlateCarree(),
        target_crs=ccrs.LambertAzimuthalEqualArea(),
    )

    assert len(result) == 1
    assert isinstance(result[0], Point)

    # Coordinates should not be identical after reprojection
    x0, y0 = geom.coords[0]
    x1, y1 = result[0].coords[0]

    assert not math.isclose(x0, x1)
    assert not math.isclose(y0, y1)


def test_reproject_geometries_linestring():
    geom = LineString(
        [
            (10.0, 40.0),
            (12.0, 42.0),
            (14.0, 44.0),
        ]
    )

    result = geometry.reproject_geometries(
        geometries=[geom],
        src_crs=ccrs.PlateCarree(),
        target_crs=ccrs.LambertAzimuthalEqualArea(),
    )

    assert len(result) == 1
    reprojected = result[0]

    assert isinstance(reprojected, LineString)
    assert not reprojected.is_empty

    original_coords = list(geom.coords)
    new_coords = list(reprojected.coords)

    assert len(original_coords) == len(new_coords)

    # At least one vertex must move
    assert any(
        not math.isclose(ox, nx) or not math.isclose(oy, ny)
        for (ox, oy), (nx, ny) in zip(original_coords, new_coords)
    )


def test_reproject_geometries_polygon():
    geom = Polygon(
        [
            (10.0, 44.0),
            (12.0, 44.0),
            (12.0, 46.0),
            (10.0, 46.0),
            (10.0, 44.0),
        ]
    )

    result = geometry.reproject_geometries(
        geometries=[geom],
        src_crs=ccrs.PlateCarree(),
        target_crs=ccrs.LambertAzimuthalEqualArea(),
    )

    assert len(result) == 1
    reprojected = result[0]

    assert isinstance(reprojected, Polygon)
    assert not reprojected.is_empty
    assert reprojected.is_valid

    original_coords = list(geom.exterior.coords)
    new_coords = list(reprojected.exterior.coords)

    assert len(original_coords) == len(new_coords)

    # At least one exterior vertex must move
    assert any(
        not math.isclose(ox, nx) or not math.isclose(oy, ny)
        for (ox, oy), (nx, ny) in zip(original_coords, new_coords)
    )
