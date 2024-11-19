import numpy as np

from earthkit.plots.sources import get_source


def test_numpy_source():
    """Test that get_source returns the correct source for a numpy array."""
    source = get_source(np.array([1, 2, 3]))
    assert source.__class__.__name__ == "NumpySource"
