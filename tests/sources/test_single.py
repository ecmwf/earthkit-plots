import numpy as np
import pytest

from earthkit.plots.sources.single import SingleSource


def test_single_positional_1d():
    """Test a single 1D positional argument."""
    source = SingleSource([10, 20, 30])
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([10, 20, 30]))
    assert source.z_values is None


def test_single_positional_2d():
    """Test a single 2D positional argument."""
    data = np.array([[1, 2, 3], [4, 5, 6]])
    source = SingleSource(data)
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([0, 1]))
    assert np.array_equal(source.z_values, data)


def test_two_positional_args():
    """Test two positional arguments to set x and y values directly."""
    source = SingleSource([1, 2, 3], [3, 6, 9])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([3, 6, 9]))
    assert source.z_values is None


def test_three_positional_args():
    """Test three positional arguments to set x, y, and z values directly."""
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    z = np.array([[1, 2, 3], [4, 5, 6]])
    source = SingleSource(x, y, z)
    assert np.array_equal(source.x_values, x)
    assert np.array_equal(source.y_values, y)
    assert np.array_equal(source.z_values, z)


def test_x_keyword_only():
    """Test with only x specified as a keyword argument."""
    source = SingleSource(x=[10, 20, 30])
    assert np.array_equal(source.x_values, np.array([10, 20, 30]))
    assert np.array_equal(source.y_values, np.array([0, 1, 2]))
    assert source.z_values is None


def test_y_keyword_only():
    """Test with only y specified as a keyword argument."""
    source = SingleSource(y=[5, 15, 25])
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([5, 15, 25]))
    assert source.z_values is None


def test_x_and_y_keywords():
    """Test with both x and y specified as keyword arguments."""
    source = SingleSource(x=[1, 2, 3], y=[7, 8, 9])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([7, 8, 9]))
    assert source.z_values is None


def test_x_positional_y_keyword():
    """Test with x as a positional argument and y as a keyword argument."""
    source = SingleSource([1, 2, 3], y=[4, 5, 6])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([4, 5, 6]))
    assert source.z_values is None


def test_y_positional_x_keyword():
    """Test with y as a positional argument and x as a keyword argument."""
    source = SingleSource([4, 5, 6], x=[1, 2, 3])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([4, 5, 6]))
    assert source.z_values is None


def test_x_y_and_z_keywords():
    """Test with x, y, and z specified as keyword arguments."""
    x = np.array([1, 2, 3])
    y = np.array([4, 5])
    z = np.array([[10, 20, 30], [40, 50, 60]])
    source = SingleSource(x=x, y=y, z=z)
    assert np.array_equal(source.x_values, x)
    assert np.array_equal(source.y_values, y)
    assert np.array_equal(source.z_values, z)


def test_insufficient_args():
    """Test for error when neither args nor x/y keywords are provided."""
    with pytest.raises(ValueError):
        SingleSource()


def test_metadata():
    """Test metadata retrieval."""
    source = SingleSource(x=[1, 2, 3], metadata={"units": "m/s"})
    assert source.metadata("units") == "m/s"
    assert source.metadata("nonexistent_key", "default") == "default"


def test_units():
    """Test units property."""
    source = SingleSource(x=[1, 2, 3], metadata={"units": "m/s"})
    assert source.units == "m/s"
