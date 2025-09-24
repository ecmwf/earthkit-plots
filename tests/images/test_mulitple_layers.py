import earthkit.data
import pytest

import earthkit.plots
from earthkit.plots import schema

@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_temperature_pressure():
    temperature, pressure = earthkit.data.from_source(
        "sample", "era5-2t-msl-1985122512.grib"
    )
    chart = earthkit.plots.Map(domain="Europe")
    chart.quickplot(temperature, units="celsius")
    chart.quickplot(pressure, units="hPa")

    chart.legend(location="right")

    chart.coastlines()

    chart.title()
    chart.gridlines()

    return chart.fig


@pytest.mark.mpl_image
@pytest.mark.mpl_image_compare(style=schema.to_stylesheet(include_style_sheet=False))
def test_efi_hatched():
    from earthkit.plots.styles import Hatched

    data = earthkit.data.from_source(
        "url", "https://get.ecmwf.int/repository/test-data/metview/gallery/efi.grib"
    )

    fgi = data.sel(shortName="10fgi")
    tpi = data.sel(shortName="tpi")

    LEVELS = [0.6, 0.8, 1.0]
    HATCHES = ["." * 5, "o" * 5]

    fgi_style = Hatched(
        colors="magenta",
        levels=LEVELS,
        hatches=HATCHES,
        legend_style="disjoint",
    )

    tpi_style = Hatched(
        colors="green",
        levels=LEVELS,
        hatches=HATCHES,
        legend_style="disjoint",
    )

    chart = earthkit.plots.Map(domain=(-18, 40, 30, 72))

    chart.contourf(fgi, style=fgi_style)
    chart.contourf(tpi, style=tpi_style)

    chart.land()
    chart.coastlines()
    chart.borders()
    chart.gridlines()

    chart.legend(label="{variable_name!l}", location=["top left", "top right"], ncols=2)

    return chart.fig
