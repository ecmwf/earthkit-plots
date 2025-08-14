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

VARIABLE_NAME_PREFERENCE = [
    "long_name",
    "standard_name",
    "name",
    "short_name",
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
    Identify which dimension/variable is the primary data (not coordinates or metadata).

    This function is useful for determining which dimension should be used for unit
    conversion, statistical operations, or other data processing tasks.

    Parameters
    ----------
    data : xarray.DataArray, xarray.Dataset, or list
        The data to analyze. Can be a DataArray, Dataset, or list of dimension names.
    exclude_dims : list, optional
        Additional dimensions to exclude from consideration as primary data.
        Defaults to COORDINATE_DIMS.

    Returns
    -------
    str or None
        The name of the primary dimension/variable, or None if not found.
    """
    if exclude_dims is None:
        exclude_dims = COORDINATE_DIMS

    # Handle different input types
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
        return None

    # If multiple primary dimensions, try to identify the most likely one
    if len(primary_dims) == 1:
        return primary_dims[0]

    # For multiple primary dimensions, use heuristics to choose the best one
    # Priority: data variables > non-coordinate dimensions > first available

    # Check if any are data variables (for xarray objects)
    if hasattr(data, "data_vars"):
        data_vars = list(data.data_vars.keys())
        for dim in primary_dims:
            if dim in data_vars:
                return dim

    # Check if any have non-numeric names (likely data, not coordinates)
    for dim in primary_dims:
        if not any(
            coord_name in dim.lower()
            for coord_name in ["x", "y", "z", "time", "lat", "lon"]
        ):
            return dim

    # Default to first available
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
