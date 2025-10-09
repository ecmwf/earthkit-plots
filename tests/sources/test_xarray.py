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


def test_xarray_source_invalid_dimension():
    """Test that XarraySource raises a ValueError for invalid dimension names."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    with pytest.raises(ValueError):
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


def test_xarray_source_1d_dimensionless():
    """Test XarraySource with 1D dimensionless data."""
    data = xr.DataArray(np.array([1, 2, 3, 4, 5]))
    source = XarraySource(data)
    assert np.array_equal(source.x_values, np.array([0, 1, 2, 3, 4]))
    assert np.array_equal(source.y_values, np.array([1, 2, 3, 4, 5]))
    assert source.z_values is None


def test_xarray_source_1d_with_dimension():
    """Test XarraySource with 1D data having one dimension."""
    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        name="temperature",
    )
    source = XarraySource(data)
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([10, 20, 30]))
    assert source.z_values is None
    assert source._x == "time"
    assert source._y == "temperature"
    assert source._z is None


def test_xarray_source_1d_explicit_x():
    """Test XarraySource with 1D data and explicit x coordinate."""
    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        name="temperature",
    )
    source = XarraySource(data, x="time")
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([10, 20, 30]))
    assert source.z_values is None
    assert source._x == "time"
    assert source._y == "temperature"


def test_xarray_source_1d_explicit_y():
    """Test XarraySource with 1D data and explicit y coordinate."""
    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        name="temperature",
    )
    source = XarraySource(data, y="time")
    assert np.array_equal(source.y_values, np.array([0, 1, 2]))
    assert np.array_equal(source.x_values, np.array([10, 20, 30]))
    assert source.z_values is None
    assert source._x == "temperature"
    assert source._y == "time"


def test_xarray_source_1d_explicit_both():
    """Test XarraySource with 1D data and explicit x and y coordinates."""
    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["bananas"],
        coords={"bananas": [0, 1, 2]},
        name="onions",
    )
    source = XarraySource(data, x="bananas", y="onions")
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([10, 20, 30]))
    assert source.z_values is None


def test_xarray_source_explicit_2d_all_coords():
    """Test XarraySource with 2D data and all coordinates explicitly specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = XarraySource(data, x="lon", y="lat", z="temperature")
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_explicit_2d_x_only():
    """Test XarraySource with 2D data and only x coordinate specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = XarraySource(data, x="lon")
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source._x == "lon"
    assert source._y == "lat"


def test_xarray_source_explicit_2d_y_only():
    """Test XarraySource with 2D data and only y coordinate specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = XarraySource(data, y="lat")
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source._x == "lon"
    assert source._y == "lat"


def test_xarray_source_explicit_2d_z_only():
    """Test XarraySource with 2D data and only z coordinate specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = XarraySource(data, z="temperature")
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source._x == "lon"
    assert source._y == "lat"


def test_xarray_source_x_metadata():
    """Test x_metadata property."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    data["lon"].attrs = {"long_name": "Longitude", "units": "degrees_east"}
    source = XarraySource(data)
    metadata = source.x_metadata
    assert metadata["long_name"] == "Longitude"
    assert metadata["units"] == "degrees_east"


def test_xarray_source_y_metadata():
    """Test y_metadata property."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    data["lat"].attrs = {"long_name": "Latitude", "units": "degrees_north"}
    source = XarraySource(data)
    metadata = source.y_metadata
    assert metadata["long_name"] == "Latitude"
    assert metadata["units"] == "degrees_north"


def test_xarray_source_z_metadata():
    """Test z_metadata property."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    data.attrs = {"long_name": "Temperature", "units": "Celsius"}
    source = XarraySource(data)
    metadata = source.z_metadata
    assert metadata["long_name"] == "Temperature"
    assert metadata["units"] == "Celsius"


def test_xarray_source_metadata_fallback():
    """Test metadata fallback when no attributes are present."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = XarraySource(data)
    x_metadata = source.x_metadata
    y_metadata = source.y_metadata
    z_metadata = source.z_metadata

    assert x_metadata["long_name"] == "lon"
    assert y_metadata["long_name"] == "lat"
    assert z_metadata["long_name"] == "temperature"


def test_xarray_source_invalid_coordinate_name():
    """Test XarraySource raises ValueError for invalid coordinate names."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )
    with pytest.raises(ValueError, match="not found in dimensions"):
        XarraySource(data, x="invalid_coord")


def test_xarray_source_invalid_variable_name():
    """Test XarraySource raises ValueError for invalid variable names."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    with pytest.raises(ValueError, match="not found in dimensions"):
        XarraySource(data, z="invalid_var")


def test_xarray_source_array_like_coordinates():
    """Test XarraySource with array-like coordinate values."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )
    custom_x = np.array([200, 210, 220])
    custom_y = np.array([30, 40])
    source = XarraySource(data, x=custom_x, y=custom_y)
    assert np.array_equal(source.x_values, custom_x)
    assert np.array_equal(source.y_values, custom_y)
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_dataset_variable_selection():
    """Test XarraySource with dataset variable selection."""
    data = xr.Dataset(
        {
            "temperature": (["lat", "lon"], [[1, 2, 3], [4, 5, 6]]),
            "humidity": (["lat", "lon"], [[30, 35, 40], [45, 50, 55]]),
        },
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )
    source = XarraySource(data, z="humidity")
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[30, 35, 40], [45, 50, 55]]))


def test_xarray_source_coordinate_vs_data_variable():
    """Test XarraySource distinguishing between coordinates and data variables."""
    data = xr.Dataset(
        {
            "temperature": (["lat", "lon"], [[1, 2, 3], [4, 5, 6]]),
            "pressure": (["lat", "lon"], [[1013, 1014, 1015], [1016, 1017, 1018]]),
        },
        coords={
            "lat": [10, 20],
            "lon": [100, 110, 120],
            "elevation": (["lat", "lon"], [[100, 200, 300], [400, 500, 600]]),
        },
    )
    # Test using elevation coordinate
    source = XarraySource(data, z="elevation")
    assert np.array_equal(source.x_values, np.array([100, 110, 120]))
    assert np.array_equal(source.y_values, np.array([10, 20]))
    assert np.array_equal(source.z_values, np.array([[100, 200, 300], [400, 500, 600]]))


def test_xarray_source_1d_edge_cases():
    """Test edge cases for 1D data handling."""
    data = xr.DataArray(
        np.array([1, 2, 3]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        name="temperature",
    )
    source = XarraySource(data, z="temperature")
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([0, 1, 2]))
    assert np.array_equal(source.z_values, np.array([1, 2, 3]))


def test_xarray_source_2d_edge_cases():
    """Test edge cases for 2D data handling."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["dim1", "dim2"],
        coords={"dim1": [10, 20], "dim2": [100, 110, 120]},
        name="temperature",
    )
    source = XarraySource(data)
    assert np.array_equal(source.x_values, np.array([10, 20]))  # dim1 values
    assert np.array_equal(source.y_values, np.array([100, 110, 120]))  # dim2 values
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source._x == "dim1"
    assert source._y == "dim2"


def test_xarray_dataset_key_variable_selection():
    """Test automatic selection of key variable from Dataset with coordinate dimensions."""
    # Create a dataset similar to the user's example
    import pandas as pd

    # Create time coordinate
    times = pd.date_range("2025-08-20", "2025-08-23T23:00:00", freq="h")

    # Create dataset with one variable having coordinate dimensions and others not
    data = xr.Dataset(
        {
            "t2m": (["valid_time"], np.random.randn(96)),  # Has coordinate dimension
            "latitude": 45.0,  # No coordinate dimensions
            "longitude": -120.0,  # No coordinate dimensions
        },
        coords={"valid_time": times},
    )

    # Should automatically select 't2m' as the key variable
    source = XarraySource(data)

    # Verify the correct variable was selected
    assert source._data.name == "t2m"
    assert np.array_equal(
        source.y_values, data["t2m"].values
    )  # 1D data goes to y_values
    assert source.x_values is not None  # Should have time values
    assert source.z_values is None  # 1D data, no z dimension
    assert source._x == "valid_time"  # Should identify the time dimension as x
    assert source._y == "t2m"  # Should identify the data variable as y
    assert source._z is None  # No z dimension for 1D data


def test_xarray_dataset_multiple_coordinate_variables():
    """Test error when multiple variables have coordinate dimensions."""
    import pandas as pd

    times = pd.date_range("2025-08-20", "2025-08-23T23:00:00", freq="h")

    # Create dataset with multiple variables having coordinate dimensions
    data = xr.Dataset(
        {
            "t2m": (["valid_time"], np.random.randn(96)),  # Has coordinate dimension
            "rh": (
                ["valid_time"],
                np.random.randn(96),
            ),  # Also has coordinate dimension
            "latitude": 45.0,  # No coordinate dimensions
            "longitude": -120.0,  # No coordinate dimensions
        },
        coords={"valid_time": times},
    )

    # Should raise an error since multiple variables have coordinate dimensions
    with pytest.raises(
        ValueError, match="Multiple variables found in the xarray Dataset"
    ):
        XarraySource(data)


def test_xarray_dataset_no_coordinate_variables():
    """Test error when no variables have coordinate dimensions."""
    # Create dataset with no variables having coordinate dimensions
    data = xr.Dataset(
        {
            "latitude": 45.0,
            "longitude": -120.0,
            "elevation": 100.0,
        }
    )

    # Should raise an error since no variables have coordinate dimensions
    with pytest.raises(
        ValueError, match="Multiple variables found in the xarray Dataset"
    ):
        XarraySource(data)
