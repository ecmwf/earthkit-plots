import earthkit.plots
import earthkit.data
import pytest

@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(baseline_dir="/Users/mavj/ek/test-images/images/")
def test_healpix_interpolated():
    data = earthkit.data.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = earthkit.plots.Map()
    chart.quickplot(data, units="celsius")

    chart.legend()

    chart.coastlines()

    chart.title()
    chart.gridlines()
    
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(baseline_dir="/Users/mavj/ek/test-images/images/")
def test_healpix_pixels():
    data = earthkit.data.from_source("sample", "healpix-h128-nested-2t.grib")
    chart = earthkit.plots.Map(domain=["France", "Spain"])
    chart.grid_cells(data, units="celsius")

    chart.legend()

    chart.coastlines()

    chart.title()
    chart.gridlines()
    
    return chart.fig