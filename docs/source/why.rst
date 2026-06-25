Why earthkit-plots?
===================

**earthkit-plots** is a high-level Python library for producing publication-quality
scientific graphics with minimal code. Built on **matplotlib**, **cartopy**,
**xarray**, and the broader **earthkit** ecosystem, it enriches these tools with
domain-specific knowledge so you can focus on your data rather than plot
configuration.

Key features:

- **Concise API** - generate complex visualisations in just a few lines.
- **Automatic data extraction** - reads GRIB, netCDF, and zarr data; works with
  xarray DataArrays and NumPy arrays; handles geographic coordinates, grids, and
  CRS automatically.
- **Intelligent formatting** - titles, labels, and colour scales adapt based on
  detected metadata, variables, and units.
- **Style libraries** - swap styles to match your organisation, project, or
  preferences.
- **Complex grids out of the box** - HEALPix, reduced Gaussian, and more with no
  extra legwork.


Quick start
-----------

**earthkit-plots** provides a high level api to quickly visualise data.

.. code-block:: python

    (
        ekp.geo.plot(era5_2t, domain="Europe", units="celsius")
        .title("ERA5 monthly averaged {variable_name} over {domain} - {time:%B %Y}")
        .borders()
        .gridlines()
        .show()
    )

.. image:: images/plot-era5-t2m-19931201.png
   :width: 600
   :align: center
