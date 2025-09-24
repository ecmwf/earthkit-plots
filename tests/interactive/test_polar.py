import numpy as np
import pytest

import earthkit.plots.interactive.polar as polar


def test_circular_var_known_values():
    """Tests that circular variance is ~0 for concentrated data and ~1 for uniform data."""
    data_concentrated = np.deg2rad([45, 45, 45, 45.1])
    assert polar.circular_var(data_concentrated) == pytest.approx(0.0, abs=1e-6)

    data_uniform = np.deg2rad([0, 90, 180, 270])
    assert polar.circular_var(data_uniform) == pytest.approx(1.0)


def test_vonmises_kde_properties():
    """Tests that the von Mises KDE output is a valid probability distribution."""
    data = np.deg2rad([90, 95])
    bins, kde = polar.vonmises_kde(data, kappa=50, n_bins=360)

    # The output should be a 1D array of the specified size.
    assert kde.shape == (360,)

    # The integral of the density function over its domain must be 1.
    integral = np.trapz(kde, x=bins)
    assert integral == pytest.approx(1.0)


def test_hybrid_vonmises_grid_peak_location():
    """Tests that the density peak is close to the input data's central point."""
    expected_speed = 20.0
    expected_dir = 270.0

    # Slight random variations around our point.
    speed_data = np.random.normal(loc=expected_speed, scale=0.1, size=100)
    dir_data = np.random.normal(loc=expected_dir, scale=0.1, size=100)

    # Run the calculation.
    density, dirs, speeds = polar.calculate_wind_density_hybrid_vonmises_on_grid(
        speed_data, dir_data, num_direction_points=72, num_speed_points=80
    )

    # Find the grid coordinates (row, col) of the highest density value.
    i_dir, i_spd = np.unravel_index(np.argmax(density), density.shape)

    # Check if the results are within an acceptable tolerance.
    # For speed, the tolerance is the size of one grid cell.
    speed_tolerance = speeds[1] - speeds[0]
    assert speeds[i_spd] == pytest.approx(expected_speed, abs=speed_tolerance)

    # For direction, the tolerance is the width of one angular sector.
    dir_tolerance = dirs[1] - dirs[0]
    angular_distance = min(
        abs(dirs[i_dir] - expected_dir), 360 - abs(dirs[i_dir] - expected_dir)
    )
    assert angular_distance <= dir_tolerance


def test_hybrid_vonmises_grid_empty_input():
    """Tests that the function handles empty data gracefully and returns a zero-grid."""
    density, dirs, speeds = polar.calculate_wind_density_hybrid_vonmises_on_grid(
        [], [], num_direction_points=10, num_speed_points=5
    )

    assert density.shape == (10, 5)
    assert np.all(density == 0)


def test_smoothed_hull_insufficient_points():
    """Tests that contour generation returns empty arrays for inputs with too few points."""
    points_insufficient = np.array([[0, 0], [1, 1], [0, 1]])

    r_smooth, theta_smooth = polar.generate_smoothed_hull_contour(points_insufficient)

    assert r_smooth.size == 0
    assert theta_smooth.size == 0
