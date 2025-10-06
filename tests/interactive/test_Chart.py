import numpy as np
import xarray as xr
from plotly.graph_objects import Figure

from earthkit.plots.interactive import (
    Chart,  # Replace 'module' with the module containing the Chart class.
)


def test_chart_initialization():
    """Test initialization of the Chart class with default values."""
    chart = Chart()
    assert chart.rows == 1
    assert chart.columns == 1
    assert chart._fig is None
    assert chart._layout_override == {}
    assert chart._subplots_kwargs == {}


def test_chart_initialization_with_args():
    """Test initialization of the Chart class with custom rows and columns."""
    chart = Chart(rows=3, columns=2)
    assert chart.rows == 3
    assert chart.columns == 2


def test_chart_fig_creation():
    """Test the creation of the figure property."""
    chart = Chart(rows=2, columns=3)
    fig = chart.fig
    assert isinstance(fig, Figure)
    assert len(fig.layout.annotations) == 0  # No subplot titles initially.


def test_chart_add_trace():
    """Test adding a trace to the chart."""
    chart = Chart(rows=1, columns=1)
    trace_data = {"x": [1, 2, 3], "y": [4, 5, 6], "type": "scatter"}
    chart.add_trace(trace_data)
    assert len(chart.fig.data) == 1
    assert chart.fig.data[0].type == "scatter"
    assert chart.fig.data[0].x == (1, 2, 3)
    assert chart.fig.data[0].y == (4, 5, 6)


def test_chart_title():
    """Test setting the chart title."""
    chart = Chart(rows=1, columns=1)
    chart.title("Test Chart Title")
    assert chart._layout_override["title"] == "Test Chart Title"


def test_chart_box():
    """Test the box method of the Chart class."""
    start = np.datetime64("2025-01-01", "ns")
    times = np.arange(start, start + np.timedelta64(4, "D"), np.timedelta64(1, "D"))
    eps_members = np.arange(1, 5)
    var1_data = np.arange(16).reshape((4, 4))
    var2_data = var1_data * 2
    q3 = np.array([2.25, 6.25, 10.25, 14.25])
    data = xr.Dataset(
        {
            "var1": (("time", "epsMember"), var1_data),
            "var2": (("time", "epsMember"), var2_data),
        },
        coords={
            "time": times,
            "epsMember": eps_members,
        },
    )
    chart = Chart()
    chart.box(data)
    assert all(chart.fig.data[0].x == times)
    assert all(chart.fig.data[1].x == times)
    assert all(chart.fig.data[6].x == times)
    assert all(chart.fig.data[0].q3 == q3)
    assert all(chart.fig.data[6].q3 == q3 * 2)
