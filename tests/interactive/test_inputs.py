import numpy as np
import pandas as pd
import pytest
import xarray as xr

from earthkit.plots.interactive.inputs import _earthkitify, to_numpy, to_xarray


class MockEarthkitData:
    def __init__(self, data):
        self.data = data

    def to_xarray(self):
        return xr.DataArray(self.data)

    def to_pandas(self):
        return pd.Series(self.data)

    def to_numpy(self):
        return np.array(self.data)


@pytest.fixture
def mock_earthkit(monkeypatch):
    """Mock the earthkit.data.from_object function to return mock data."""

    def mock_from_object(data):
        return MockEarthkitData(data)

    monkeypatch.setattr("earthkit.data.from_object", mock_from_object)


def test_earthkitify_with_list(mock_earthkit):
    """Test _earthkitify with a list input."""
    data = [1, 2, 3]
    result = _earthkitify(data)
    assert isinstance(result, MockEarthkitData)
    assert np.array_equal(result.to_numpy(), np.array(data))


def test_earthkitify_with_numpy(mock_earthkit):
    """Test _earthkitify with a numpy array."""
    data = np.array([1, 2, 3])
    result = _earthkitify(data)
    assert isinstance(result, MockEarthkitData)
    assert np.array_equal(result.to_numpy(), data)


def test_to_xarray(mock_earthkit):
    """Test to_xarray conversion."""
    data = [1, 2, 3]
    result = to_xarray(data)
    assert isinstance(result, xr.DataArray)
    assert np.array_equal(result.values, np.array(data))


def test_to_numpy(mock_earthkit):
    """Test to_numpy conversion."""
    data = [1, 2, 3]
    result = to_numpy(data)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, np.array(data))
