import cartopy.crs as ccrs
import numpy as np
import pytest
import xarray as xr

from earthkit.plots.sources import XarraySource


def test_xarray_source_auto_dimensions():
    """Test that XarraySource automatically detects x and y dimensions."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    source = XarraySource(data)
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_dataset_source():
    """Test that XarraySource can handle xarray datasets."""
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    source = XarraySource(data)
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_dataset_multi_var():
    """Test that a ValueError is raised when multiple variables are present in the xarray dataset."""
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
            "humidity": (["latitude", "longitude"], [[30, 35, 40], [45, 50, 55]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    with pytest.raises(ValueError):
        XarraySource(data)


def test_xarray_source_specified_dimensions():
    """Test that XarraySource uses specified x and y dimension names."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )
    source = XarraySource(data, x="lon", y="lat")
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_dimension_as_string():
    """Test that XarraySource uses specified string for z variable within xarray data."""
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    source = XarraySource(
        data["temperature"], x="longitude", y="latitude", z="temperature"
    )
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_multiple_variables():
    """Test that XarraySource correctly extracts specified variable from xarray dataset with multiple variables."""
    # Create a dataset with multiple variables
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[15, 16, 17], [18, 19, 20]]),
            "humidity": (["latitude", "longitude"], [[30, 35, 40], [45, 50, 55]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )

    # Specify the variable to extract (e.g., "humidity")
    source = XarraySource(data, x="longitude", y="latitude", z="humidity")

    # Verify that x, y, and z values correspond to the specified variable
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[30, 35, 40], [45, 50, 55]]))


def test_xarray_source_fallback_to_numpy_behavior():
    """Test that XarraySource falls back to numpy behavior with array inputs."""
    data = np.array([[1, 2, 3], [4, 5, 6]])
    source = XarraySource(data)
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([0, 1]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_invalid_dimension():
    """Test that XarraySource raises a ValueError for invalid dimension names."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    with pytest.raises(KeyError):
        XarraySource(data, x="invalid_x", y="latitude")


def test_metadata():
    """Test that metadata retrieval works as expected from attrs of xarray source."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
        attrs={"description": "Test data array"},
    )
    assert XarraySource(data).metadata("description") == "Test data array"


def test_units():
    """Test that units are extracted from the metadata of the xarray source."""
    data = xr.DataArray(
        np.array([1, 2, 3]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        attrs={"units": "seconds"},
    )
    assert XarraySource(data).units == "seconds"


def test_variable_units():
    """Test that units are extracted from the metadata of the xarray variable."""
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    data["temperature"].attrs["units"] = "Celsius"
    assert XarraySource(data["temperature"]).units == "Celsius"


def test_xarray_source_crs_with_cf_grid_mapping():
    """Test that XarraySource extracts the CRS from a CF-compliant grid_mapping."""
    # Create the projection variable with CF-compliant attributes
    projection = xr.DataArray(
        0,
        attrs={
            "grid_mapping_name": "lambert_conformal_conic",
            "standard_parallel": [25.0, 35.0],
            "longitude_of_central_meridian": -95.0,
            "latitude_of_projection_origin": 15.0,
        },
    )

    # Create the data variable with a grid_mapping attribute pointing to the projection
    data = xr.DataArray(
        [[1, 2], [3, 4]],
        dims=["y", "x"],
        coords={
            "x": ("x", [100000, 200000]),
            "y": ("y", [300000, 400000]),
        },
        attrs={"grid_mapping": "lambert_conformal_conic"},
    )

    # Create the dataset including the projection
    dataset = xr.Dataset({"temperature": data, "lambert_conformal_conic": projection})

    # Initialize XarraySource with the dataset
    source = XarraySource(dataset, x="x", y="y", z="temperature")

    # Check that the crs property is correctly extracted
    assert isinstance(source.crs, ccrs.LambertConformal)
    assert source.crs.proj4_params["lat_1"], source.crs.proj4_params["lat_2"] == (
        25.0,
        35.0,
    )
    assert source.crs.proj4_params["lon_0"] == -95.0
    assert source.crs.proj4_params["lat_0"] == 15.0


# def test_1D():
#     """Test that units are extracted from the metadata of the xarray source."""
#     data = xr.DataArray(
#         np.array([1, 2, 3]),
#         dims=["time"],
#         coords={"time": [0, 1, 2]},
#         attrs={"units": "seconds"},
#     )
#     source = XarraySource(data)
#     assert np.array_equal(source.x_values, [0, 1, 2])
#     assert np.array_equal(source.y_values, [1, 2, 3])
#     assert source.z_values is None
