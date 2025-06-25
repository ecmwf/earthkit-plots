import pytest

import earthkit.plots


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare
def test_named_europe():
    chart = earthkit.plots.Map(domain="Europe")
    chart.coastlines()
    chart.gridlines()
    chart.title("{domain} ({crs})")
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare
def test_named_new_zealand():
    chart = earthkit.plots.Map(domain="New Zealand")
    chart.coastlines()
    chart.gridlines()
    chart.title("{domain} ({crs})")
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare
def test_named_africa():
    chart = earthkit.plots.Map(domain="Africa")
    chart.coastlines()
    chart.gridlines()
    chart.title("{domain} ({crs})")
    return chart.fig
