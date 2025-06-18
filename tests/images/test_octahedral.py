import earthkit.plots
import earthkit.data
import pytest

@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(baseline_dir="/Users/mavj/ek/test-images/images/")
def test_octahedral_interpolated():
    data = earthkit.data.from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-regrid/test-data/global_0_360/O32.grib",
    )
    chart = earthkit.plots.Map()
    chart.quickplot(data, units="celsius")

    chart.legend()

    chart.coastlines()

    chart.title()
    chart.gridlines()
    
    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(baseline_dir="/Users/mavj/ek/test-images/images/")
def test_octahedral_point_cloud():
    data = earthkit.data.from_source(
        "url",
        "https://get.ecmwf.int/repository/test-data/earthkit-regrid/test-data/global_0_360/O32.grib",
    )
    chart = earthkit.plots.Map(domain="Europe")
    chart.point_cloud(data, units="celsius")

    chart.legend()

    chart.coastlines()

    chart.title()
    chart.gridlines()
    
    return chart.fig
