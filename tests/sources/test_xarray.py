import cartopy.crs as ccrs
import numpy as np
import pytest
import xarray as xr

from earthkit.plots.sources import get_source


def test_xarray_source_auto_dimensions():
    """Test that get_source automatically detects x and y dimensions."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    source = get_source(data)
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_dataset_source():
    """Test that get_source can handle xarray datasets."""
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    source = get_source(data)
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_specified_dimensions():
    """Test that get_source uses specified x and y dimension names."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )
    source = get_source(data, x="lon", y="lat")
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_dimension_as_string():
    """Test that get_source uses specified string for z variable within xarray data."""
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    source = get_source(data["temperature"], x="longitude", y="latitude", z="temperature")
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_multiple_variables():
    """Test that get_source correctly extracts specified variable from xarray dataset with multiple variables."""
    # Create a dataset with multiple variables
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[15, 16, 17], [18, 19, 20]]),
            "humidity": (["latitude", "longitude"], [[30, 35, 40], [45, 50, 55]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )

    # Specify the variable to extract (e.g., "humidity")
    source = get_source(data, x="longitude", y="latitude", z="humidity")

    # Verify that x, y, and z values correspond to the specified variable
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[30, 35, 40], [45, 50, 55]]))


def test_metadata():
    """Test that metadata retrieval works as expected from attrs of xarray source."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
        attrs={"description": "Test data array"},
    )
    assert get_source(data).metadata("description") == "Test data array"


def test_units():
    """Test that units are extracted from the metadata of the xarray source."""
    data = xr.DataArray(
        np.array([1, 2, 3]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        attrs={"units": "seconds"},
    )
    from earthkit.plots.sources.context import PlotContext

    assert get_source(data, context=PlotContext.CARTESIAN_1D).units == "seconds"


def test_variable_units():
    """Test that units are extracted from the metadata of the xarray variable."""
    data = xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    data["temperature"].attrs["units"] = "Celsius"
    assert get_source(data["temperature"]).units == "Celsius"


def test_xarray_source_crs_with_cf_grid_mapping():
    """Test that get_source extracts the CRS from a CF-compliant grid_mapping."""
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

    dataset = xr.Dataset({"temperature": data, "lambert_conformal_conic": projection})

    source = get_source(dataset, x="x", y="y", z="temperature")

    # Check that the crs property is correctly extracted
    assert isinstance(source.crs, ccrs.LambertConformal)
    assert source.crs.proj4_params["lat_1"], source.crs.proj4_params["lat_2"] == (
        25.0,
        35.0,
    )
    assert source.crs.proj4_params["lon_0"] == -95.0
    assert source.crs.proj4_params["lat_0"] == 15.0


def test_xarray_source_1d_dimensionless():
    """Test get_source with 1D dimensionless data."""
    from earthkit.plots.sources.context import PlotContext

    data = xr.DataArray(np.array([1, 2, 3, 4, 5]))
    source = get_source(data, context=PlotContext.CARTESIAN_1D)
    assert np.array_equal(source.x.values, np.array([0, 1, 2, 3, 4]))
    assert np.array_equal(source.y.values, np.array([1, 2, 3, 4, 5]))
    assert source.z is None


def test_xarray_source_1d_with_dimension():
    """Test get_source with 1D data having one dimension."""
    from earthkit.plots.sources.context import PlotContext

    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        name="temperature",
    )
    source = get_source(data, context=PlotContext.CARTESIAN_1D)
    assert np.array_equal(source.x.values, np.array([0, 1, 2]))
    assert np.array_equal(source.y.values, np.array([10, 20, 30]))
    assert source.z is None
    assert source.x.name == "time"
    assert source.y.name == "temperature"
    assert source.z is None


def test_xarray_source_1d_explicit_x():
    """Test get_source with 1D data and explicit x coordinate."""
    from earthkit.plots.sources.context import PlotContext

    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        name="temperature",
    )
    source = get_source(data, x="time", context=PlotContext.CARTESIAN_1D)
    assert np.array_equal(source.x.values, np.array([0, 1, 2]))
    assert np.array_equal(source.y.values, np.array([10, 20, 30]))
    assert source.z is None
    assert source.x.name == "time"
    assert source.y.name == "temperature"


def test_xarray_source_1d_explicit_y():
    """Test get_source with 1D data and explicit y coordinate."""
    from earthkit.plots.sources.context import PlotContext

    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        name="temperature",
    )
    source = get_source(data, y="time", context=PlotContext.CARTESIAN_1D)
    assert np.array_equal(source.y.values, np.array([0, 1, 2]))
    assert np.array_equal(source.x.values, np.array([10, 20, 30]))
    assert source.z is None
    assert source.x.name == "temperature"
    assert source.y.name == "time"


def test_xarray_source_1d_explicit_both():
    """Test get_source with 1D data and explicit x and y coordinates."""
    from earthkit.plots.sources.context import PlotContext

    data = xr.DataArray(
        np.array([10, 20, 30]),
        dims=["bananas"],
        coords={"bananas": [0, 1, 2]},
        name="onions",
    )
    source = get_source(data, x="bananas", y="onions", context=PlotContext.CARTESIAN_1D)
    assert np.array_equal(source.x.values, np.array([0, 1, 2]))
    assert np.array_equal(source.y.values, np.array([10, 20, 30]))
    assert source.z is None


def test_xarray_source_explicit_2d_all_coords():
    """Test get_source with 2D data and all coordinates explicitly specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = get_source(data, x="lon", y="lat", z="temperature")
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_explicit_2d_x_only():
    """Test get_source with 2D data and only x coordinate specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = get_source(data, x="lon")
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source.x.name == "lon"
    assert source.y.name == "lat"


def test_xarray_source_explicit_2d_y_only():
    """Test get_source with 2D data and only y coordinate specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = get_source(data, y="lat")
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source.x.name == "lon"
    assert source.y.name == "lat"


def test_xarray_source_explicit_2d_z_only():
    """Test get_source with 2D data and only z coordinate specified."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = get_source(data, z="temperature")
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source.x.name == "lon"
    assert source.y.name == "lat"


def test_xarray_source_x_metadata():
    """Test x dimension metadata."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    data["lon"].attrs = {"long_name": "Longitude", "units": "degrees_east"}
    source = get_source(data)
    assert source.x.metadata("long_name") == "Longitude"
    assert source.x.metadata("units") == "degrees_east"


def test_xarray_source_y_metadata():
    """Test y dimension metadata."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    data["lat"].attrs = {"long_name": "Latitude", "units": "degrees_north"}
    source = get_source(data)
    assert source.y.metadata("long_name") == "Latitude"
    assert source.y.metadata("units") == "degrees_north"


def test_xarray_source_z_metadata():
    """Test z dimension metadata."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    data.attrs = {"long_name": "Temperature", "units": "Celsius"}
    source = get_source(data)
    assert source.z.metadata("long_name") == "Temperature"
    assert source.z.metadata("units") == "Celsius"


def test_xarray_source_metadata_fallback():
    """Test metadata fallback when no attributes are present."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
        name="temperature",
    )
    source = get_source(data)

    assert source.x.metadata("name") == "lon"
    assert source.y.metadata("name") == "lat"
    assert source.z.metadata("name") == "temperature"


def test_xarray_source_array_like_coordinates():
    """Test get_source with array-like coordinate values."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["lat", "lon"],
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )
    custom_x = np.array([200, 210, 220])
    custom_y = np.array([30, 40])
    source = get_source(data, x=custom_x, y=custom_y)
    # Should create meshgrid from 1D custom coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], custom_x)
    assert np.array_equal(source.y.values[:, 0], custom_y)
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_xarray_source_dataset_variable_selection():
    """Test get_source with dataset variable selection."""
    data = xr.Dataset(
        {
            "temperature": (["lat", "lon"], [[1, 2, 3], [4, 5, 6]]),
            "humidity": (["lat", "lon"], [[30, 35, 40], [45, 50, 55]]),
        },
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )
    source = get_source(data, z="humidity")
    # Should create meshgrid from 1D coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[30, 35, 40], [45, 50, 55]]))


def test_xarray_source_coordinate_vs_data_variable():
    """Test get_source distinguishing between coordinates and data variables."""
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
    source = get_source(data, z="elevation")
    # Should create meshgrid from 1D coordinates (elevation is already 2D, so it stays 2D)
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))
    assert np.array_equal(source.z.values, np.array([[100, 200, 300], [400, 500, 600]]))


def test_xarray_source_2d_edge_cases():
    """Test edge cases for 2D data handling."""
    data = xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["dim1", "dim2"],
        coords={"dim1": [10, 20], "dim2": [100, 110, 120]},
        name="temperature",
    )
    source = get_source(data)
    # Should create meshgrid from 1D coordinates
    # dim1 (first dimension) maps to y, dim2 (second dimension) maps to x
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.x.values[0, :], np.array([100, 110, 120]))  # dim2 values
    assert np.array_equal(source.y.values[:, 0], np.array([10, 20]))  # dim1 values
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))
    assert source.x.name == "dim2"
    assert source.y.name == "dim1"


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
    from earthkit.plots.sources.context import PlotContext

    source = get_source(data, context=PlotContext.CARTESIAN_1D)

    # Verify the correct variable was selected
    # Note: source._data is the original Dataset, but the extractor selects the DataArray
    # We verify selection by checking the extracted coordinates
    assert np.array_equal(source.y.values, data["t2m"].values)  # 1D data goes to y_values
    assert source.x.values is not None  # Should have time values
    assert source.z is None  # 1D data, no z dimension
    assert source.x.name == "valid_time"  # Should identify the time dimension as x
    assert source.y.name == "t2m"  # Should identify the data variable as y
    assert source.z is None  # No z dimension for 1D data


def test_xarray_source_1d_point_data_with_lat_lon():
    """Test get_source with 1D point data that has latitude and longitude coordinates."""
    from earthkit.plots.sources.context import PlotContext

    # Example: temperature measurements at different lat/lon points
    data = xr.DataArray(
        np.array([20, 25, 30, 22]),
        dims=["point"],
        coords={
            "point": [0, 1, 2, 3],
            "latitude": ("point", [10.0, 20.0, 30.0, 40.0]),
            "longitude": ("point", [5.0, 15.0, 25.0, 35.0]),
        },
        name="temperature",
    )

    source = get_source(data, context=PlotContext.GEOGRAPHIC_1D)

    # Should detect longitude as x, latitude as y, and temperature as z
    assert np.array_equal(source.x.values, np.array([5.0, 15.0, 25.0, 35.0]))
    assert np.array_equal(source.y.values, np.array([10.0, 20.0, 30.0, 40.0]))
    assert np.array_equal(source.z.values, np.array([20, 25, 30, 22]))
    assert source.x.name == "longitude"
    assert source.y.name == "latitude"
    assert source.z.name == "temperature"


def test_xarray_source_1d_time_series_with_scalar_lat_lon():
    """Test get_source with 1D time series data that has scalar latitude/longitude metadata."""
    # Example: temperature time series at a single location (lat/lon are scalars)
    import pandas as pd

    from earthkit.plots.sources.context import PlotContext

    times = pd.date_range("2025-08-20", "2025-08-23T23:00:00", freq="h")

    data = xr.DataArray(
        np.random.randn(96),
        dims=["valid_time"],
        coords={
            "valid_time": times,
            "latitude": 45.0,  # Scalar latitude
            "longitude": -120.0,  # Scalar longitude
        },
        name="t2m",
    )

    source = get_source(data, context=PlotContext.CARTESIAN_1D)

    # Should treat as time series: x=valid_time, y=t2m values, z=None
    # Should NOT use the scalar lat/lon as x/y
    assert len(source.x.values) == 96
    assert len(source.y.values) == 96
    assert source.z is None
    assert source.x.name == "valid_time"
    assert source.y.name == "t2m"
    assert source.z is None


def test_xarray_2d_without_meshgrid():
    """Test that meshgrid is not applied when coordinates are already 2D."""
    # Create 2D coordinate arrays (e.g., curvilinear grid)
    x_2d = np.array([[100, 110, 120], [101, 111, 121]])
    y_2d = np.array([[10, 11, 12], [20, 21, 22]])
    z_data = np.array([[1, 2, 3], [4, 5, 6]])

    data = xr.DataArray(
        z_data,
        dims=["y", "x"],
        coords={
            "lon": (["y", "x"], x_2d),
            "lat": (["y", "x"], y_2d),
        },
        name="temperature",
    )

    source = get_source(data, x="lon", y="lat")

    # Should use 2D arrays as-is, not apply meshgrid
    assert np.array_equal(source.x.values, x_2d)
    assert np.array_equal(source.y.values, y_2d)
    assert np.array_equal(source.z.values, z_data)


def test_xarray_unit_conversion():
    """Test unit conversion for xarray data."""
    data = xr.DataArray(
        np.array([273.15, 283.15, 293.15]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        attrs={"units": "K"},
        name="temperature",
    )

    from earthkit.plots.sources.context import PlotContext

    source = get_source(data, units="degC", context=PlotContext.CARTESIAN_1D)

    # Values should be converted from K to °C
    expected = np.array([0.0, 10.0, 20.0])
    assert np.allclose(source.y.values, expected)


def test_xarray_datetime_coordinate():
    """Test extraction of datetime coordinates."""
    import pandas as pd

    from earthkit.plots.sources.context import PlotContext

    times = pd.date_range("2025-01-01", periods=5, freq="D")
    data = xr.DataArray(
        np.array([10, 20, 30, 40, 50]),
        dims=["time"],
        coords={"time": times},
        name="temperature",
    )

    source = get_source(data, context=PlotContext.CARTESIAN_1D)

    # Should extract datetime values
    assert len(source.x.values) == 5
    assert source.x.values[0] == times[0]
    assert np.array_equal(source.y.values, np.array([10, 20, 30, 40, 50]))


def test_xarray_projected_crs_uses_dimension_coords():
    """Test that projected CRS uses x/y dimension coordinates, not lat/lon."""
    # Create a dataset mimicking Lambert Azimuthal Equal Area projection
    # with x, y dimension coordinates and 2D latitude, longitude arrays
    ny, nx = 3, 4

    # Dimension coordinates in projection space (meters)
    x_coords = np.array([2.5e6, 3.5e6, 4.5e6, 5.5e6])
    y_coords = np.array([5.5e6, 4.5e6, 3.5e6])

    # Create 2D lat/lon arrays (for reference only)
    lon_2d = np.array([
        [10.0, 15.0, 20.0, 25.0],
        [10.5, 15.5, 20.5, 25.5],
        [11.0, 16.0, 21.0, 26.0],
    ])
    lat_2d = np.array([
        [50.0, 50.5, 51.0, 51.5],
        [45.0, 45.5, 46.0, 46.5],
        [40.0, 40.5, 41.0, 41.5],
    ])

    # Data values
    data_values = np.random.rand(ny, nx)

    # Create dataset with grid mapping variable
    ds = xr.Dataset(
        {
            "temperature": (
                ["y", "x"],
                data_values,
                {"grid_mapping": "lambert_azimuthal_equal_area"},
            ),
            "lambert_azimuthal_equal_area": (
                [],
                0,
                {
                    "grid_mapping_name": "lambert_azimuthal_equal_area",
                    "latitude_of_projection_origin": 52.0,
                    "longitude_of_projection_origin": 10.0,
                    "false_easting": 4321000.0,
                    "false_northing": 3210000.0,
                },
            ),
        },
        coords={
            "x": x_coords,
            "y": y_coords,
            "latitude": (["y", "x"], lat_2d),
            "longitude": (["y", "x"], lon_2d),
        },
    )

    from earthkit.plots.sources.context import PlotContext

    source = get_source(ds, context=PlotContext.GEOGRAPHIC_2D)

    # Should use x, y dimension coordinates (1D), not 2D lat/lon
    assert source.x.values.ndim == 2  # Meshgrid applied
    assert source.y.values.ndim == 2
    assert source.z.values.ndim == 2

    # Check that we're using dimension coords by verifying values
    # After meshgrid, first row should be x_coords
    assert np.allclose(source.x.values[0, :], x_coords)
    assert np.allclose(source.y.values[:, 0], y_coords)

    # CRS should be detected as Lambert Azimuthal Equal Area
    crs = source.crs
    assert crs is not None
    assert crs.__class__.__name__ == "LambertAzimuthalEqualArea"


def test_xarray_no_crs_uses_latlon_coords():
    """Test that without CRS, lat/lon coordinates are used when available."""
    # Create a dataset with x, y dimensions and 2D lat/lon coordinates
    # but NO grid mapping (no CRS)
    ny, nx = 3, 4

    # Dimension coordinates (just indices)
    x_coords = np.arange(nx)
    y_coords = np.arange(ny)

    # Create 2D lat/lon arrays matching data shape
    lon_2d = np.array([
        [10.0, 15.0, 20.0, 25.0],
        [10.5, 15.5, 20.5, 25.5],
        [11.0, 16.0, 21.0, 26.0],
    ])
    lat_2d = np.array([
        [50.0, 50.5, 51.0, 51.5],
        [45.0, 45.5, 46.0, 46.5],
        [40.0, 40.5, 41.0, 41.5],
    ])

    # Data values
    data_values = np.random.rand(ny, nx)

    # Create dataset WITHOUT grid mapping variable
    ds = xr.Dataset(
        {
            "temperature": (["y", "x"], data_values),
        },
        coords={
            "x": x_coords,
            "y": y_coords,
            "latitude": (["y", "x"], lat_2d),
            "longitude": (["y", "x"], lon_2d),
        },
    )

    from earthkit.plots.sources.context import PlotContext

    source = get_source(ds, context=PlotContext.GEOGRAPHIC_2D)

    # Should use 2D lat/lon coordinates since there's no CRS
    assert source.x.values.ndim == 2
    assert source.y.values.ndim == 2
    assert source.z.values.ndim == 2

    # Check that we're using lat/lon coords, not dimension coords
    assert np.allclose(source.x.values, lon_2d)
    assert np.allclose(source.y.values, lat_2d)
    assert np.allclose(source.z.values, data_values)

    # CRS should be None (no grid mapping)
    assert source.crs is None


# =============================================================================
# Vector Field Tests
# =============================================================================


def test_xarray_vector_explicit_uv():
    """Test xarray vector field with explicit u and v variables."""
    ds = xr.Dataset(
        {
            "u_wind": (["lat", "lon"], [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
            "v_wind": (["lat", "lon"], [[0.5, 1.5, 2.5], [3.5, 4.5, 5.5]]),
        },
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )

    source = get_source(ds, u="u_wind", v="v_wind")

    # Check coordinates
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)

    # Check u and v components
    assert source.u is not None
    assert source.v is not None
    assert np.allclose(source.u.values, [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    assert np.allclose(source.v.values, [[0.5, 1.5, 2.5], [3.5, 4.5, 5.5]])

    # Check magnitude
    assert source.z is not None
    u_vals = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    v_vals = np.array([[0.5, 1.5, 2.5], [3.5, 4.5, 5.5]])
    expected_magnitude = np.sqrt(u_vals**2 + v_vals**2)
    assert np.allclose(source.z.values, expected_magnitude)


def test_xarray_vector_auto_detection():
    """Test auto-detection of u and v components in xarray."""
    from earthkit.plots.sources.context import PlotContext

    ds = xr.Dataset(
        {
            "u": (["lat", "lon"], [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
            "v": (["lat", "lon"], [[0.5, 1.5, 2.5], [3.5, 4.5, 5.5]]),
        },
        coords={"lat": [10, 20], "lon": [100, 110, 120]},
    )

    # Should auto-detect u and v from variable names
    source = get_source(ds, context=PlotContext.CARTESIAN_VECTOR_2D)

    assert source.u is not None
    assert source.v is not None
    assert np.allclose(source.u.values, [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    assert np.allclose(source.v.values, [[0.5, 1.5, 2.5], [3.5, 4.5, 5.5]])


def test_xarray_vector_auto_detection_standard_names():
    """Test auto-detection using standard naming conventions."""
    from earthkit.plots.sources.context import PlotContext

    # Test various standard u/v naming patterns
    test_cases = [
        ("u10", "v10"),  # Common for 10m winds
        ("u_component_of_wind", "v_component_of_wind"),
        ("eastward_wind", "northward_wind"),
    ]

    for u_name, v_name in test_cases:
        ds = xr.Dataset(
            {
                u_name: (["lat", "lon"], [[1.0, 2.0], [3.0, 4.0]]),
                v_name: (["lat", "lon"], [[0.5, 1.5], [2.5, 3.5]]),
            },
            coords={"lat": [10, 20], "lon": [100, 110]},
        )

        source = get_source(ds, context=PlotContext.CARTESIAN_VECTOR_2D)

        assert source.u is not None, f"Failed to detect u from {u_name}"
        assert source.v is not None, f"Failed to detect v from {v_name}"


def test_xarray_vector_metadata():
    """Test metadata extraction from xarray vector fields."""
    ds = xr.Dataset(
        {
            "u": (
                ["lat", "lon"],
                [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                {"units": "m/s", "long_name": "U component of wind"},
            ),
            "v": (
                ["lat", "lon"],
                [[0.5, 1.5, 2.5], [3.5, 4.5, 5.5]],
                {"units": "m/s", "long_name": "V component of wind"},
            ),
        },
        coords={
            "lat": [10, 20],
            "lon": [100, 110, 120],
        },
        attrs={"level": 850},
    )

    source = get_source(ds, u="u", v="v")

    # Check dimension metadata
    assert source.u.metadata("long_name") == "U component of wind"
    assert source.v.metadata("long_name") == "V component of wind"
    assert source.u.source_units == "m/s"
    assert source.v.source_units == "m/s"

    # TODO: Check source-level metadata from dataset attrs
    # When u/v are explicitly specified, dataset-level attrs should be preserved
    # assert source.metadata("level") == 850


def test_xarray_vector_with_time_dimension():
    """Test vector field with time dimension (should use first timestep)."""
    ds = xr.Dataset(
        {
            "u": (["time", "lat", "lon"], [[[1.0, 2.0], [3.0, 4.0]]]),
            "v": (["time", "lat", "lon"], [[[0.5, 1.5], [2.5, 3.5]]]),
        },
        coords={
            "time": ["2024-01-01"],
            "lat": [10, 20],
            "lon": [100, 110],
        },
    )

    source = get_source(ds, u="u", v="v")

    # Should extract first time step
    assert source.u.values.shape == (2, 2)
    assert source.v.values.shape == (2, 2)


def test_xarray_vector_magnitude_metadata():
    """Test that magnitude has appropriate metadata."""
    ds = xr.Dataset(
        {
            "u": (["lat", "lon"], [[1.0, 2.0], [3.0, 4.0]]),
            "v": (["lat", "lon"], [[1.0, 2.0], [3.0, 4.0]]),
        },
        coords={"lat": [10, 20], "lon": [100, 110]},
    )

    source = get_source(ds, u="u", v="v")

    # Check magnitude metadata
    assert source.z.name == "magnitude"
    assert "magnitude" in source.z.metadata("long_name", "").lower()


def test_xarray_vector_unit_conversion():
    """Test unit conversion for vector components."""
    ds = xr.Dataset(
        {
            "u": (
                ["lat", "lon"],
                [[1.0, 2.0], [3.0, 4.0]],
                {"units": "m/s"},
            ),
            "v": (
                ["lat", "lon"],
                [[0.5, 1.5], [2.5, 3.5]],
                {"units": "m/s"},
            ),
        },
        coords={"lat": [10, 20], "lon": [100, 110]},
    )

    source = get_source(ds, u="u", v="v", u_units="km/h", v_units="km/h")

    # Should convert m/s to km/h (multiply by 3.6)
    expected_u = np.array([[1.0, 2.0], [3.0, 4.0]]) * 3.6
    expected_v = np.array([[0.5, 1.5], [2.5, 3.5]]) * 3.6
    assert np.allclose(source.u.values, expected_u, rtol=1e-5)
    assert np.allclose(source.v.values, expected_v, rtol=1e-5)


# =============================================================================
# Gridspec Detection Tests
# =============================================================================


def _make_1d_da(attrs):
    """Helper: 1D DataArray with lat/lon coords and given attrs."""
    return xr.DataArray(
        np.random.rand(4),
        dims=["values"],
        coords={
            "latitude": ("values", [10.0, 20.0, 30.0, 40.0]),
            "longitude": ("values", [5.0, 15.0, 25.0, 35.0]),
        },
        attrs=attrs,
    )


def test_gridspec_ek_grid_spec_dict_reduced_gg():
    """ek_grid_spec dict with an octahedral reduced Gaussian grid is detected."""
    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({"ek_grid_spec": {"grid": "O320"}})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "reduced_gg"


def test_gridspec_ek_grid_spec_dict_healpix():
    """ek_grid_spec dict with a HEALPix grid is detected."""
    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({"ek_grid_spec": {"grid": "H256"}})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "healpix"


def test_gridspec_ek_grid_spec_json_string():
    """ek_grid_spec stored as a JSON string (e.g. after NetCDF round-trip) is parsed."""
    import json

    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({"ek_grid_spec": json.dumps({"grid": "O320"})})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "reduced_gg"


def test_gridspec_legacy_gridSpec_key():
    """Legacy 'gridSpec' attribute key is still supported."""
    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({"gridSpec": {"grid": "O320"}})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "reduced_gg"


def test_gridspec_legacy_grid_spec_key():
    """Legacy 'grid_spec' attribute key is still supported."""
    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({"grid_spec": {"grid": "N320"}})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "reduced_gg"


def test_gridspec_ek_grid_spec_takes_priority_over_legacy():
    """ek_grid_spec is preferred over legacy keys when both are present."""
    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({"ek_grid_spec": {"grid": "O320"}, "gridSpec": {"grid": "N80"}})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.to_dict()["grid"] == "O320"


def test_gridspec_earthkit_attr_json_string():
    """grid_spec nested in an '_earthkit' JSON string attr is detected."""
    import json

    from earthkit.plots.sources.gridspec import GridSpec

    earthkit_blob = {
        "message": {"__bytes_b64__": "R1JJQg=="},
        "bitsPerValue": 16,
        "grid_spec": {"grid": "O320"},
    }
    da = _make_1d_da({"_earthkit": json.dumps(earthkit_blob)})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "reduced_gg"


def test_gridspec_earthkit_attr_dict():
    """grid_spec nested in an '_earthkit' dict attr is detected."""
    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({"_earthkit": {"bitsPerValue": 16, "grid_spec": {"grid": "H256"}}})
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "healpix"


def test_gridspec_explicit_key_takes_priority_over_earthkit_attr():
    """ek_grid_spec is preferred over the nested '_earthkit' grid_spec."""
    import json

    from earthkit.plots.sources.gridspec import GridSpec

    da = _make_1d_da({
        "ek_grid_spec": {"grid": "O320"},
        "_earthkit": json.dumps({"grid_spec": {"grid": "N80"}}),
    })
    source = get_source(da)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.to_dict()["grid"] == "O320"


def test_gridspec_earthkit_attr_without_grid_spec_returns_none():
    """An '_earthkit' blob carrying no grid_spec does not raise and yields None."""
    import json

    da = _make_1d_da({"_earthkit": json.dumps({"bitsPerValue": 16})})
    source = get_source(da)
    assert source.gridspec is None


def test_gridspec_earthkit_attr_invalid_json_returns_none():
    """A non-JSON '_earthkit' string does not raise and returns None."""
    da = _make_1d_da({"_earthkit": "not-valid-json"})
    source = get_source(da)
    assert source.gridspec is None


def test_gridspec_none_when_no_attr():
    """Gridspec is None when no relevant attribute is present."""
    da = _make_1d_da({"units": "K", "long_name": "temperature"})
    source = get_source(da)
    assert source.gridspec is None


def test_gridspec_invalid_json_string_returns_none():
    """A non-JSON string in ek_grid_spec does not raise and returns None."""
    da = _make_1d_da({"ek_grid_spec": "not-valid-json"})
    source = get_source(da)
    assert source.gridspec is None


def test_gridspec_dataset_global_attrs():
    """ek_grid_spec on a Dataset's global attrs is detected."""
    from earthkit.plots.sources.gridspec import GridSpec

    ds = xr.Dataset(
        {"temperature": (["values"], np.random.rand(4))},
        coords={
            "latitude": ("values", [10.0, 20.0, 30.0, 40.0]),
            "longitude": ("values", [5.0, 15.0, 25.0, 35.0]),
        },
        attrs={"ek_grid_spec": {"grid": "O320"}},
    )
    source = get_source(ds)
    gs = source.gridspec
    assert isinstance(gs, GridSpec)
    assert gs.name == "reduced_gg"


def test_gridspec_is_structured_grid_integration():
    """_is_structured_grid returns True for an xarray source with ek_grid_spec."""
    from earthkit.plots.resample import _is_structured_grid

    da = _make_1d_da({"ek_grid_spec": {"grid": "O320"}})
    source = get_source(da)
    assert _is_structured_grid(source.gridspec) is True


def test_gridspec_is_not_structured_for_regular_grid():
    """_is_structured_grid returns False when no gridspec is present."""
    from earthkit.plots.resample import _is_structured_grid

    da = xr.DataArray(
        np.random.rand(2, 3),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )
    source = get_source(da)
    assert _is_structured_grid(source.gridspec) is False


N_CELLS = 48  # nside=2 HEALPix has 48 cells — small enough for fast tests


def _make_healpix_da(ordering="nested", gridspec_in_attrs=True, gridspec_as_json=False):
    """Build a minimal 1D HEALPix-style DataArray with no lat/lon coordinates."""
    import pandas as pd

    data = np.random.rand(N_CELLS).astype(np.float32)
    attrs = {
        "long_name": "Specific humidity",
        "standard_name": "specific_humidity",
        "units": "kg kg-1",
        "cell_methods": "time: mean cell: mean",
        "grid_mapping": "crs",
    }
    if gridspec_in_attrs:
        spec = {"grid": "H2", "ordering": ordering}
        attrs["ek_grid_spec"] = str(spec).replace("'", '"') if gridspec_as_json else spec

    return xr.DataArray(
        data,
        dims=["cell"],
        coords={
            "level_full": 89.0,
            "time": pd.Timestamp("2020-02-01"),
        },
        attrs=attrs,
        name="hus",
    )


def test_healpix_xarray_gridspec_from_attrs():
    """GridSpec is detected from ek_grid_spec attr (dict form)."""
    from earthkit.plots.resample import _is_structured_grid

    da = _make_healpix_da(gridspec_in_attrs=True)
    source = get_source(da)
    assert source.gridspec is not None
    assert _is_structured_grid(source.gridspec) is True
    assert source.gridspec.name == "healpix"


def test_healpix_xarray_gridspec_from_attrs_json_string():
    """GridSpec is detected from ek_grid_spec attr when stored as a JSON string."""
    from earthkit.plots.resample import _is_structured_grid

    da = _make_healpix_da(gridspec_in_attrs=True, gridspec_as_json=True)
    source = get_source(da)
    assert source.gridspec is not None
    assert _is_structured_grid(source.gridspec) is True


def test_healpix_xarray_gridspec_from_metadata_kwarg():
    """GridSpec is detected from user-supplied metadata= kwarg when attrs carry no gridspec."""
    from earthkit.plots.resample import _is_structured_grid

    da = _make_healpix_da(gridspec_in_attrs=False)
    assert da.attrs.get("ek_grid_spec") is None  # no gridspec in attrs

    source = get_source(da, metadata={"grid": "H2", "ordering": "nested"})
    assert source.gridspec.to_dict() == {"grid": "H2", "ordering": "nested"}
    assert _is_structured_grid(source.gridspec) is True


def test_healpix_xarray_1d_source_extracts_z():
    """1D HEALPix DataArray produces a valid Source with z values and placeholder x/y."""
    from earthkit.plots.sources.context import PlotContext

    da = _make_healpix_da()
    source = get_source(da, context=PlotContext.GEOGRAPHIC_2D)

    assert source.z is not None
    assert source.z.values.shape == (N_CELLS,)
    # x/y are placeholders (all zeros) — the Regrid step replaces them
    assert source.x.values.shape == (N_CELLS,)
    assert source.y.values.shape == (N_CELLS,)


def test_healpix_xarray_1d_no_gridspec_raises():
    """1D data with no gridspec raises a clear ValueError rather than silently plotting garbage."""
    from earthkit.plots.sources.context import PlotContext

    da = _make_healpix_da(gridspec_in_attrs=False)
    source = get_source(da, context=PlotContext.GEOGRAPHIC_2D)

    with pytest.raises(ValueError, match="no recognised grid specification"):
        _ = source.z  # triggers lazy extraction


def test_healpix_xarray_ordering():
    """GridSpec.to_dict() includes the correct ordering for nested HEALPix."""
    da = _make_healpix_da(ordering="nested")
    source = get_source(da)
    spec = source.gridspec.to_dict()
    ordering = spec.get("ordering") or spec.get("order")
    assert str(ordering).lower() == "nested"
