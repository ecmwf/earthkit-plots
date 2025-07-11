import numpy as np
import pytest

from earthkit.plots.sources.numpy import NumpySource


def test_NumpySource_1D_data():
    """Test 1D data as a single positional argument (interpreted as y-values)."""
    source = NumpySource([1, 2, 3])
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([1, 2, 3]))
    assert source.z_values is None


def test_NumpySource_2D_data():
    """Test 2D data as a single positional argument (interpreted as z-values for a heatmap)."""
    source = NumpySource([[1, 2, 3], [4, 5, 6]])
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([0, 1]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_NumpySource_two_positional_args():
    """Test two positional arguments to set x and y values directly."""
    source = NumpySource([1, 2, 3], [3, 6, 4])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([3, 6, 4]))
    assert source.z_values is None


def test_NumpySource_xy_keywords():
    """Test x and y values passed as keyword arguments."""
    source = NumpySource(x=[1, 2, 3], y=[3, 6, 4])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([3, 6, 4]))
    assert source.z_values is None


def test_NumpySource_three_args():
    """Test three positional arguments to set x, y, and z values directly."""
    source = NumpySource([1, 2, 3], [3, 6], [[1, 2, 3], [4, 5, 6]])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([3, 6]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_NumpySource_named_x():
    """Test x passed as a keyword with a positional argument for y-values."""
    source = NumpySource([4, 5, 6], x=[1, 2, 3])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([4, 5, 6]))
    assert source.z_values is None


def test_NumpySource_named_y():
    """Test y passed as a keyword with a positional argument for x-values."""
    source = NumpySource([4, 5, 6], y=[10, 20, 30])
    assert np.array_equal(source.x_values, np.array([4, 5, 6]))
    assert np.array_equal(source.y_values, np.array([10, 20, 30]))
    assert source.z_values is None


def test_NumpySource_xy_z_keyword():
    """Test x, y, and z values passed as keyword arguments."""
    source = NumpySource(x=[1, 2, 3], y=[4, 5], z=[[10, 20, 30], [40, 50, 60]])
    assert np.array_equal(source.x_values, np.array([1, 2, 3]))
    assert np.array_equal(source.y_values, np.array([4, 5]))
    assert np.array_equal(source.z_values, np.array([[10, 20, 30], [40, 50, 60]]))


def test_NumpySource_no_arguments():
    """Test that initializing without any arguments raises a TypeError."""
    with pytest.raises(ValueError):
        NumpySource()


def test_NumpySource_3D_data_error():
    """Test that 3D data raises an error since only 1D and 2D are supported."""
    data_3d = np.random.rand(3, 3, 3)
    with pytest.raises(ValueError):
        NumpySource(data_3d)


def test_NumpySource_only_x():
    """Test only x keyword argument, where y is automatically generated as indices."""
    source = NumpySource(x=[5, 10, 15])
    assert np.array_equal(source.x_values, np.array([5, 10, 15]))
    assert np.array_equal(source.y_values, np.array([0, 1, 2]))
    assert source.z_values is None


def test_NumpySource_only_y():
    """Test only y keyword argument, where x is automatically generated as indices."""
    source = NumpySource(y=[5, 10, 15])
    assert np.array_equal(source.x_values, np.array([0, 1, 2]))
    assert np.array_equal(source.y_values, np.array([5, 10, 15]))
    assert source.z_values is None


def test_NumpySource_2D_data_with_explicit_x_y():
    """Test a 2D positional data with explicit x and y values for overriding defaults."""
    source = NumpySource([[1, 2, 3], [4, 5, 6]], x=[10, 20, 30], y=[100, 200])
    assert np.array_equal(source.x_values, np.array([10, 20, 30]))
    assert np.array_equal(source.y_values, np.array([100, 200]))
    assert np.array_equal(source.z_values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_NumpySource_all_2d():
    """Test with all inputs as 2D arrays."""
    source = NumpySource(
        [[1, 2, 3], [1, 2, 3]],
        [[1, 1, 1], [2, 2, 2]],
        [[1, 2, 3], [4, 5, 6]],
    )
    assert np.array_equal(source.x_values, [[1, 2, 3], [1, 2, 3]])
    assert np.array_equal(source.y_values, [[1, 1, 1], [2, 2, 2]])
    assert np.array_equal(source.z_values, [[1, 2, 3], [4, 5, 6]])


def test_NumpySource_2d_x_z_missing_y():
    """Test x and z as 2D inputs. y is not generated as a 2D index, instead raises."""
    with pytest.raises(ValueError):
        NumpySource(
            x=[[1, 2, 3], [1, 2, 3]],
            z=[[1, 2, 3], [4, 5, 6]],
        )


def test_NumpySource_x_y_different_dims():
    """Test exception is raised when x and y are different dimensionalities."""
    with pytest.raises(ValueError):
        NumpySource(
            x=[[1, 2, 3], [1, 2, 3]],
            y=[1, 2, 3],
            z=[[1, 2, 3], [4, 5, 6]],
        )


def test_NumpySource_all_1d_positional():
    """Test all 1D inputs."""
    source = NumpySource(
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    )
    assert np.array_equal(source.x_values, [1, 2, 3])
    assert np.array_equal(source.y_values, [4, 5, 6])
    assert np.array_equal(source.z_values, [7, 8, 9])


def test_NumpySource_all_1d_keywords():
    """Test all 1D inputs when passed as keywords."""
    source = NumpySource(
        x=[1, 2, 3],
        y=[4, 5, 6],
        z=[7, 8, 9],
    )
    assert np.array_equal(source.x_values, [1, 2, 3])
    assert np.array_equal(source.y_values, [4, 5, 6])
    assert np.array_equal(source.z_values, [7, 8, 9])


def test_NumpySource_private_xyz():
    source = NumpySource(
        z=[[1, 2, 3], [4, 5, 6]],
    )
    assert source._x is None
    assert source._y is None
    assert np.array_equal(source._z, [[1, 2, 3], [4, 5, 6]])


def test_metadata():
    """Test that metadata is extracted from the data object."""
    source = NumpySource([1, 2, 3], metadata={"key": "value"})
    assert source.metadata("key") == "value"


def test_units():
    """Test that units are extracted from the metadata."""
    source = NumpySource([1, 2, 3], metadata={"units": "meters"})
    assert source.units == "meters"
