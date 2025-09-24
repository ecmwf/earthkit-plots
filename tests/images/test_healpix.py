import earthkit.data
import pytest

import earthkit.plots
from earthkit.plots import schema


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_healpix_interpolated():
    import matplotlib.pyplot as plt
    import warnings
    
    # Debug: Check settings right at the start of the test
    warnings.warn(f"In test - Font family: {plt.rcParams['font.family']}")
    warnings.warn(f"In test - Font size: {plt.rcParams['font.size']}")
    warnings.warn(f"In test - Axes linewidth: {plt.rcParams['axes.linewidth']}")
    
    data = earthkit.data.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = earthkit.plots.Map()
    chart.quickplot(data, units="celsius")

    chart.legend()
    chart.coastlines()
    chart.title()
    chart.gridlines()
    
    # Debug: Check what font is actually being used in the figure
    fig = chart.fig
    if fig.axes:
        ax = fig.axes[0]
        if ax.get_xticklabels():
            actual_font = ax.get_xticklabels()[0].get_fontname()
            warnings.warn(f"Actual font being used: {actual_font}")

    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_healpix_pixels():
    data = earthkit.data.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = earthkit.plots.Map(domain=["France", "Spain"])
    chart.grid_cells(data, units="celsius")

    chart.legend()

    chart.coastlines()

    chart.title()
    chart.gridlines()

    return chart.fig
