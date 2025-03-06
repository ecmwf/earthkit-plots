import numpy as np
import pytest

from earthkit.plots.geo.grids import interpolate_unstructured

X = np.array([0, 1, 2, 3, 0, 1, 2, 3])
Y = np.array([0, 0, 1, 1, 2, 2, 3, 3])
Z = np.array([10, 20, 30, 40, 50, 60, 70, 80])
Z_nan = np.array([10, 20, 30, 40, np.nan, 60, np.nan, 80])
# TEST_GRID_X =


@pytest.mark.parametrize(
    "z, method, result_1_1",
    (
        (Z, "linear", 32.5),
        (Z, "nearest", 20.0),
        (Z, "cubic", 31.16515181455966),
        (Z_nan, "linear", 32.5),
        (Z_nan, "nearest", 20.0),
        (Z_nan, "cubic", 30.26403836889215),
    ),
)
def test_interpolation_linear(z, method, result_1_1, x=X, y=Y):
    resolution = 5
    grid_x, grid_y, grid_z = interpolate_unstructured(
        x, y, z, resolution=resolution, method=method
    )
    assert (
        grid_x.shape == grid_y.shape == grid_z.shape == (resolution, resolution)
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


def test_invalid_interpolation_method(x=X, y=Y, z=Z):
    with pytest.raises(ValueError):
        interpolate_unstructured(x, y, z, resolution=5, method="invalid")


@pytest.mark.parametrize(
    "threshold, expected_nans", ((0.75, 68), ("auto", 40), ("2 cells", 68))
)
def test_interpolation_distance_threshold(threshold, expected_nans):
    x = np.array([0, 3, 0, 3, 0, 3, 0, 3])
    y = np.array([0, 0, 3, 3, 0, 0, 3, 3])
    z = np.array([10, 20, 30, 40, 50, 60, 70, 80])
    grid_x, grid_y, grid_z = interpolate_unstructured(
        x,
        y,
        z,
        resolution=10,
        method="linear",
        interpolation_distance_threshold=threshold,
    )
    assert (
        np.isnan(grid_z).sum() == expected_nans
    ), "Thresholding did not introduce the correct number of NaNs"
