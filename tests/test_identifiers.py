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

import earthkit.data
import xarray as xr

from earthkit.plots.identifiers import (
    find,
    find_latitude,
    find_longitude,
    find_time,
    find_uv_pair,
    find_x,
    find_y,
    is_regular_latlon,
    xarray_variable_name,
)


def test_find():
    array = ["latitude", "temperature", "time"]
    identity = ["time", "t"]
    assert find(array, identity) == "time"

    identity = ["pressure", "humidity"]
    assert find(array, identity) is None


def test_find_x():
    array = ["longitude", "lat", "t"]
    assert find_x(array) == "longitude"

    array = ["year", "time", "latitude"]
    assert find_x(array) == "time"


def test_find_y():
    array = ["projection_y_coordinate", "time", "longitude"]
    assert find_y(array) == "projection_y_coordinate"

    array = ["lat", "time", "longitude"]
    assert find_y(array) == "lat"


def test_find_uv_pair():
    array = ["10u", "10v", "temperature"]
    assert find_uv_pair(array) == ("10u", "10v")

    array = ["u_component_of_wind", "v_component_of_wind", "time"]
    assert find_uv_pair(array) == ("u_component_of_wind", "v_component_of_wind")

    array = ["latitude", "longitude"]
    assert find_uv_pair(array) is None

    array = ["u_component_of_wind", "longitude"]
    assert find_uv_pair(array) is None


def test_find_latitude():
    array = ["lat", "time", "temperature"]
    assert find_latitude(array) == "lat"

    array = ["longitude", "temperature"]
    assert find_latitude(array) is None


def test_find_longitude():
    array = ["longitude", "lat", "time"]
    assert find_longitude(array) == "longitude"

    array = ["latitude", "temperature"]
    assert find_longitude(array) is None


def test_find_time():
    array = ["valid_time", "temperature"]
    assert find_time(array) == "valid_time"

    array = ["latitude", "longitude"]
    assert find_time(array) is None


def test_is_regular_latlon():
    data = earthkit.data.from_object(
        xr.Dataset(
            {"temperature": (("latitude", "longitude"), [[1, 2], [3, 4]])},
            coords={"latitude": [0, 1], "longitude": [0, 1]},
        )
    )

    assert is_regular_latlon(data) is True

    data = earthkit.data.from_object(
        xr.Dataset(
            {"temperature": (("x", "y"), [[1, 2], [3, 4]])},
            coords={"x": [0, 1], "y": [0, 1]},
        )
    )
    assert is_regular_latlon(data) is False


def test_xarray_variable_name():
    dataset = xr.Dataset(
        {
            "temperature": (("latitude", "longitude"), [[1, 2], [3, 4]]),
        },
        attrs={"long_name": "Temperature"},
    )

    assert xarray_variable_name(dataset) == "temperature"

    dataset["temperature"].attrs["long_name"] = "Surface Temperature"
    assert xarray_variable_name(dataset, "temperature") == "Surface Temperature"

    dataset["temperature"].attrs = {}  # Remove attributes
    assert xarray_variable_name(dataset, "temperature") == "temperature"
