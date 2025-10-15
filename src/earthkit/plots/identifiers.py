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

from typing import Callable

from earthkit.plots.utils import iter_utils

X = [
    "x",
    "X",
    "xc",
    "projection_x_coordinate",
    "longitude",
    "long",
    "lon",
]

Y = [
    "y",
    "Y",
    "yc",
    "projection_y_coordinate",
    "latitude",
    "lat",
]

U = [
    "u",
    "U",
    "10u",
    "u10",
    "100u",
    "u100",
    "eastward_wind",
    "U component of wind",
    "10m_u_component_of_wind",
    "100m_u_component_of_wind",
    "10 metre U wind component",
    "100 metre U wind component",
    "u_component_of_wind",
]

V = [
    "v",
    "V",
    "10v",
    "v10",
    "100v",
    "v100",
    "northward_wind",
    "V component of wind",
    "10m_v_component_of_wind",
    "100m_v_component_of_wind",
    "10 metre V wind component",
    "100 metre V wind component",
    "v_component_of_wind",
]

UV_PAIRS = list(zip(U, V))

LATITUDE = [
    "latitude",
    "lat",
]

LONGITUDE = [
    "longitude",
    "long",
    "lon",
]

TIME = [
    "time",
    "valid_time",
    "t",
    "date",
    "dayofyear",
    "month",
    "year",
]

VARIABLE_NAME_PREFERENCE = [
    "long_name",
    "standard_name",
    "name",
    "short_name",
]

# Dimensions that are typically NOT primary data (coordinates, metadata, etc.)
COORDINATE_DIMS = [
    "x",
    "y",
    "z",
    "X",
    "Y",
    "Z",
    "longitude",
    "long",
    "lon",
    "latitude",
    "lat",
    "time",
    "valid_time",
    "t",
    "date",
    "dayofyear",
    "month",
    "year",
    "level",
    "height",
    "depth",
    "pressure",
    "altitude",
    "ensemble",
    "member",
    "realization",
    "forecast_time",
    "forecast_period",
    "lead_time",
    "step",
    "step_type",
    "step_units",
    "grid_type",
    "grid_name",
    "projection_x_coordinate",
    "projection_y_coordinate",
    "xc",
    "yc",
]


def find(array, identity):
    if array.__class__.__name__ == "DataArray":
        array = list(array.coords)
    for candidate in identity:
        if candidate in array:
            return candidate


def find_x(array):
    return find(array, X) or find(array, TIME)


def find_y(array):
    return find(array, Y)


def find_u(array):
    return find(array, U)


def find_v(array):
    return find(array, V)


def find_uv_pair(array):
    for u, v in UV_PAIRS:
        if u in array and v in array:
            return u, v


def find_latitude(array):
    return find(array, LATITUDE)


def find_longitude(array):
    return find(array, LONGITUDE)


def find_time(array):
    return find(array, TIME)


def identify_primary(data, exclude_dims=None):
    """
    Identify the primary data variable (not coordinates or metadata).

    This function identifies the main data variable for unit conversion and other
    data processing tasks. For Datasets, it returns the variable name. For DataArrays,
    it returns the DataArray name. If no variables exist, it falls back to dimensions.

    Parameters
    ----------
    data : xarray.DataArray, xarray.Dataset, or list
        The data to analyze. Can be a DataArray, Dataset, or list of dimension names.
    exclude_dims : list, optional
        Additional dimensions to exclude from consideration as primary data.
        Defaults to COORDINATE_DIMS. Only used for fallback dimension identification.

    Returns
    -------
    str or None
        The name of the primary variable or dimension, or None if not found.
    """
    if exclude_dims is None:
        exclude_dims = COORDINATE_DIMS

    # Handle xarray Dataset - return first data variable
    if hasattr(data, "data_vars") and data.data_vars:
        data_vars = list(data.data_vars.keys())
        return data_vars[0]  # Return first variable

    # Handle xarray DataArray - return the DataArray name
    if hasattr(data, "name") and data.name is not None:
        return data.name

    # Handle xarray DataArray without a name - return None to trigger fallback
    if hasattr(data, "dims") and not hasattr(data, "data_vars"):
        # This is a DataArray without a name
        return None

    # Fallback: Handle dimension-based identification for other cases
    if hasattr(data, "dims"):
        # xarray DataArray or Dataset
        dims = list(data.dims)
    elif hasattr(data, "coords"):
        # xarray object with coords
        dims = list(data.coords.keys())
    elif isinstance(data, (list, tuple)):
        # List of dimension names
        dims = list(data)
    else:
        return None

    # Filter out coordinate/metadata dimensions
    primary_dims = [dim for dim in dims if dim not in exclude_dims]

    if not primary_dims:
        # If no non-coordinate dims, return first dimension
        return dims[0] if dims else None

    # Return first non-coordinate dimension
    return primary_dims[0]


def is_regular_latlon(data):
    """Determine whether data is on a regular lat-lon grid."""
    dataset = data.to_xarray().squeeze()
    return all(
        any(name in dataset.dims for name in names) for names in (LATITUDE, LONGITUDE)
    )


def xarray_variable_name(dataset, element=None):
    """
    Get the best long name representing the variable in an xarray Dataset.

    Parameters
    ----------
    dataarray : xarray.Dataset
        The Dataset from which to extract a variable name.
    element : str, optional
        If passed, the variable name for the given element will be extracted.
    """
    if isinstance(element, str):
        da = dataset[element]
        for attr in VARIABLE_NAME_PREFERENCE:
            if attr in da.attrs:
                label = da.attrs[attr]
                break
        else:
            label = element
    else:
        label = list(dataset.data_vars)[0]
    return label


VECTOR_CHECKS: list[Callable[[set], tuple[str, str] | None]] = [find_uv_pair]


def group_vectors(data) -> list:
    """Group vector components in the data."""
    unique_values = set(iter_utils.flatten(arg.metadata("param") for arg in data))
    leftover_values = unique_values.copy()

    grouped_data = []
    for check in VECTOR_CHECKS:
        if pair := check(unique_values):
            leftover_values.difference_update(pair)
            grouped_data.append(data.sel(param=pair))

    grouped_data.extend(data.sel(param=val) for val in leftover_values)
    return grouped_data
