import numpy as np
import pytest

from earthkit.plots.geo.grids import interpolate_unstructured, is_structured

X = np.array([0, 1, 2, 3, 0, 1, 2, 3])
Y = np.array([0, 0, 1, 1, 2, 2, 3, 3])
Z = np.array([10, 20, 30, 40, 50, 60, 70, 80])
Z_NAN = np.array([10, 20, 30, 40, np.nan, 60, np.nan, 80])


@pytest.mark.parametrize(
    "z, method, result_1_1",
    (
        (Z, "linear", 40.0),
        (Z, "nearest", 20.0),
        (Z, "cubic", 37.70238233696268),
        (Z_NAN, "linear", 40.0),
        (Z_NAN, "nearest", 20.0),
        (Z_NAN, "cubic", 35.25912398199118),
    ),
)
def test_interpolate_unstructured_auto_detect(z, method, result_1_1, x=X, y=Y):
    grid_x, grid_y, grid_z = interpolate_unstructured(x, y, z, method=method)
    assert (
        grid_x.shape == grid_y.shape == grid_z.shape == (4, 4)
    ), "Grid shapes do not match"
    assert np.array_equal(
        grid_x[:, 0].squeeze(), np.array([0, 1, 2, 3])
    ), "grid_x[:, 0] values do not match exactly"
    assert np.array_equal(
        grid_y[0, :].squeeze(), np.array([0, 1, 2, 3])
    ), "grid_y[0, :] values do not match exactly"
    assert np.isclose(
        grid_z[1, 1], result_1_1
    ), "grid_z[1, 1] value is not close enough to test result"
    assert not np.isnan(grid_z).all(), "All grid values are NaN"


@pytest.mark.parametrize(
    "z, method, result_1_1",
    (
        (Z, "linear", 32.5),
        (Z, "nearest", 20.0),
        (Z, "cubic", 31.16515181455966),
        (Z_NAN, "linear", 32.5),
        (Z_NAN, "nearest", 20.0),
        (Z_NAN, "cubic", 30.26403836889215),
    ),
)
def test_interpolate_unstructured_target_shape(z, method, result_1_1, x=X, y=Y):
    shape = 5
    grid_x, grid_y, grid_z = interpolate_unstructured(
        x, y, z, target_shape=(shape, shape), method=method
    )
    assert (
        grid_x.shape == grid_y.shape == grid_z.shape == (shape, shape)
    ), "Grid shapes do not match"
    assert np.array_equal(
        grid_x[:, 0].squeeze(), np.array([0.0, 0.75, 1.5, 2.25, 3.0])
    ), "grid_x[:, 0] values do not match exactly"
    assert np.array_equal(
        grid_y[0, :].squeeze(), np.array([0.0, 0.75, 1.5, 2.25, 3.0])
    ), "grid_y[0, :] values do not match exactly"
    assert np.isclose(
        grid_z[1, 1], result_1_1
    ), "grid_z[1, 1] value is not close enough to test result"
    assert not np.isnan(grid_z).all(), "All grid values are NaN"


@pytest.mark.parametrize(
    "z, method, result_1_1",
    (
        (Z, "linear", 25.0),
        (Z, "nearest", 10.0),
        (Z, "cubic", 25.559625355772425),
        (Z_NAN, "linear", 25.0),
        (Z_NAN, "nearest", 10.0),
        (Z_NAN, "cubic", 24.37143485416529),
    ),
)
def test_interpolate_unstructured_target_resolution(z, method, result_1_1, x=X, y=Y):
    resolution = 0.5
    grid_x, grid_y, grid_z = interpolate_unstructured(
        x, y, z, target_resolution=(resolution, resolution), method=method
    )
    assert grid_x.shape == grid_y.shape == grid_z.shape, "Grid shapes do not match"
    assert np.array_equal(
        grid_x[:, 0].squeeze(), np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    ), "grid_x[:, 0] values do not match exactly"
    assert np.array_equal(
        grid_y[0, :].squeeze(), np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    ), "grid_y[0, :] values do not match exactly"
    assert np.isclose(
        grid_z[1, 1], result_1_1
    ), "grid_z[1, 1] value is not close enough to test result"
    assert not np.isnan(grid_z).all(), "All grid values are NaN"


def test_invalid_interpolation_method(x=X, y=Y, z=Z):
    with pytest.raises(ValueError):
        interpolate_unstructured(x, y, z, method="invalid")


@pytest.mark.parametrize(
    "threshold, expected_nans", ((0.75, 68), ("auto", 84), ("3 cells", 68))
)
def test_interpolation_distance_threshold(threshold, expected_nans):
    x = np.array([0, 3, 0, 3, 0, 3, 0, 3])
    y = np.array([0, 0, 3, 3, 0, 0, 3, 3])
    z = np.array([10, 20, 30, 40, 50, 60, 70, 80])
    grid_x, grid_y, grid_z = interpolate_unstructured(
        x,
        y,
        z,
        target_shape=(10, 10),
        method="linear",
        distance_threshold=threshold,
    )
    assert (
        np.isnan(grid_z).sum() == expected_nans
    ), "Thresholding did not introduce the correct number of NaNs"


def test_1d_structured():
    x = np.linspace(0, 360, 361)
    y = np.linspace(-90, 90, 181)
    assert is_structured(x, y)


def test_1d_unstructured():
    x = np.linspace(0, 360, 361)
    y = np.sort(np.random.rand(181) * 180 - 90)  # Not equally spaced
    assert not is_structured(x, y)


def test_2d_structured():
    lon = np.linspace(0, 360, 361)
    lat = np.linspace(-90, 90, 181)
    x, y = np.meshgrid(lon, lat)
    assert is_structured(x, y)


def test_2d_unstructured():
    lon = np.linspace(0, 360, 361)
    lat = np.sort(np.random.rand(181) * 180 - 90)
    x, y = np.meshgrid(lon, lat)
    x[0, 0] += 0.1  # Introduce slight inconsistency
    assert not is_structured(x, y)


def test_lon_wrap_0_360():
    lon = np.linspace(0, 360, 361)
    lat = np.linspace(-90, 90, 181)
    x, y = np.meshgrid(lon, lat)
    x[:, -1] = x[:, -1] % 360  # Ensure wrap
    assert is_structured(x, y, lon_wrap=True)


def test_lon_wrap_negative180_180():
    lon = np.linspace(-180, 180, 361)
    lat = np.linspace(-90, 90, 181)
    x, y = np.meshgrid(lon, lat)
    assert is_structured(x, y, lon_wrap=True)


def test_no_wrap_fails_on_wrapping_grid():
    lon = np.linspace(0, 360, 361)
    lat = np.linspace(-90, 90, 181)
    x, y = np.meshgrid(lon, lat)
    x[:, -1] = x[:, -1] % 360
    assert not is_structured(x, y, lon_wrap=False)


def test_tolerance_effect():
    lon = np.linspace(0, 360, 361)
    lat = np.linspace(-90, 90, 181)
    x, y = np.meshgrid(lon, lat)
    x[0, 1] += 1e-6  # Within tolerance
    assert is_structured(x, y, tol=1e-5)
    assert not is_structured(x, y, tol=1e-8)
