import cartopy.crs as ccrs
import numpy as np
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
    source = get_source(
        data["temperature"], x="longitude", y="latitude", z="temperature"
    )
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
    assert np.array_equal(
        source.x.values[0, :], np.array([100, 110, 120])
    )  # dim2 values
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
    # Note: source._data is the original Dataset, but the adaptor selects the DataArray
    # We verify selection by checking the extracted coordinates
    assert np.array_equal(
        source.y.values, data["t2m"].values
    )  # 1D data goes to y_values
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
