Version 1.0 Updates
///////////////////

Version 1.0.0 is the first stable release of earthkit-plots. It
introduces a high-level functional API, a built-in styles library, support for
new grid types and plot types, and a large number of performance improvements
and bug fixes accumulated across the 1.0 release-candidate series.

New features
++++++++++++

- **Functional API via** ``ekp.geo`` **(and other namespaces)**: A new high-level functional API
  organises plotting shortcuts into namespaces - ``ekp.geo`` for geographic maps, ``ekp.timeseries``
  for time series plots, and ``ekp.climatology`` for annual-cycle plots. A single call handles layout,
  styling, and decoration automatically:

  .. code-block:: python

      ekp.geo.plot(era5_2t, domain="Europe", units="celsius")

  Every functional shortcut returns the underlying earthkit-plots object (a ``Map`` for a single
  panel, a ``Figure`` for multi-panel layouts). Methods on these returned objects are **chainable**,
  so you can keep refining the plot in a single fluent expression:

  .. code-block:: python

      (
          ekp.geo.contourf(era5_2t, domain="Europe", units="celsius")
          .coastlines(linewidth=0.5)
          .borders()
          .gridlines(xstep=10, ystep=10)
          .title("ERA5 {variable_name} — {time:%B %Y}")
          .show()
      )

  The functional and object-oriented APIs are fully interchangeable - start with a shortcut for
  sensible defaults, then switch to ``ekp.Map`` / ``ekp.Figure`` methods for precise control.
  See the `API layers examples <../examples/examples/introduction/03-api-layers.ipynb>`_ for a
  detailed walkthrough.

- **Climatology and time series plots**: A new ``ekp.timeseries`` namespace and ``ekp.climatology``
  namespace bring high-level shortcuts for temporal data, following the same chainable pattern as
  ``ekp.geo``.

  ``ekp.timeseries`` covers standard time series visualisation - ``line``, ``bar``, ``scatter``,
  ``fill_between``, ``multiboxplot``, and ``stripes`` - with automatic axis labelling, unit
  conversion, and metadata-driven titles:

  .. code-block:: python

      ekp.timeseries.line(ds, units="celsius").show()

  ``ekp.climatology`` is designed for multi-year data folded onto a shared Jan-Dec x-axis. Pass a
  continuous multi-year ``DataArray`` and earthkit-plots automatically splits it by year - one line
  per year, no manual looping needed. A ``DataArray`` with a ``dayofyear`` dimension is treated as a
  pre-computed annual cycle and mapped directly onto the same axis:

  .. code-block:: python

      chart = ekp.climatology.line(temp_1940_2022, color="#e6e6e6", label="1940–2022")
      chart.line(temp_2024, color="red", label="2024")
      chart.line(clim_daily, linestyle="--", label="1991–2020 mean")  # dayofyear DataArray
      chart.show()

  Climate stripe plots (warming stripes) are supported via ``ekp.timeseries.stripes``, which takes
  an annual anomaly ``DataArray`` and colours each year by its departure from a baseline:

  .. code-block:: python

      ekp.timeseries.stripes(anomaly, cmap="RdBu_r").xticks(frequency="10Y").show()

  See the
  `time series introduction <../examples/examples/time-series/timeseries-introduction.ipynb>`_,
  `climate stripes <../examples/examples/time-series/timeseries-climate-stripes.ipynb>`_, and
  `global temperature chart <../examples/examples/time-series/timeseries-global-temperature.ipynb>`_
  notebooks.

- **ORCA grid support**: earthkit-plots can now plot data on ORCA tripolar ocean grids.
  As with other grids, three rendering methods are supported - ``grid_cells`` (exact cell geometry),
  ``point_cloud`` (cell centres), and ``contourf`` (interpolated to a regular grid). See the
  `ORCA grid-types example <../examples/examples/grid-types/grid-types-orca.ipynb>`_.

- **Spaghetti plots**: A new ``spaghetti()`` method on ``Map`` (and via ``ekp.geo.spaghetti``)
  overlays a single contour line at a chosen value for every member of an ensemble forecast,
  giving an immediate visual impression of forecast uncertainty. The ``highlight`` parameter
  picks out one or more members (e.g. the control forecast) in a distinct style:

  .. code-block:: python

      chart.spaghetti(
          z_en,
          levels=[12500],
          highlight={"metadata.dataType": "cf"},
          label="Ensemble members",
      )

  See the `spaghetti plot example <../examples/examples/contour/contour-spaghetti.ipynb>`_.

- **Choropleth maps**: A new ``choropleth()`` method (and ``ekp.geo.choropleth`` shortcut) colours
  geographic regions from any GeoDataFrame according to a data column. Supports ``Style`` objects
  for colour scales and unit conversion, ``domain`` for zooming, and ``labels`` format strings for
  per-region text annotations:

  .. code-block:: python

      ekp.geo.choropleth(nuts_mean_2t, z="2t", domain="Europe", labels="{2t:.1f}")

  See the `choropleth example <../examples/examples/misc/choropleth.ipynb>`_.

- **Scatter plots**: The ``scatter()`` method on both maps and time series is now more transparent, passing
  through cleanly to matplotlib's ``scatter`` keyword arguments (including a per-point ``s`` size
  argument). Legends and colorbars for scatter layers - both on geographic maps and in line plots -
  now render correctly (:pr:`202`).

- **Animation, batch export, and interactive browsing**: A new ``earthkit.plots.frames`` submodule
  steps through the extra dimensions of a multi-field dataset frame by frame. ``Batch`` renders each
  frame to a separate output file for bulk export, while ``Browser`` provides an interactive slider
  widget for stepping through frames in a Jupyter notebook:

  .. code-block:: python

      from earthkit.plots.frames import Batch

      batch = Batch(m)
      m.contourf(data, style="auto")
      m.coastlines()
      paths = batch.save("{variable_name}_{valid_time:%Y%m%d_%H}.png")

  (:pr:`188`)

- **Automatic resampling**: Gridded data is now automatically resampled based on the available
  resolution and the size of the target subplot, avoiding unnecessary work when plotting
  high-resolution data into small panels (:pr:`197`).

- **Built-in default styles**: The default style library (previously distributed as the separate
  ``earthkit-plots-default-styles`` package) is now bundled directly into earthkit-plots. This
  covers variables including 2m temperature, mean sea-level pressure, precipitation, wind, sea
  surface temperature, and more. The external package is no longer required and has been removed
  from the dependencies.

- **style="auto" parameter**: A new cleaner syntax for automatic style detection. Instead of ``auto_style=True``,
  users can now pass ``style="auto"`` to plotting methods. The ``auto_style`` parameter is now deprecated and will
  be removed in a future version.

  .. code-block:: python

      # New syntax (recommended)
      chart.pcolormesh(data, style="auto")

      # Old syntax (deprecated)
      chart.pcolormesh(data, auto_style=True)

- **cmap as alias for colors**: The ``cmap`` parameter can now be used interchangeably with ``colors`` in all
  plotting methods and in ``Style`` initialisation. An error is raised only when both are specified together.
  This helps users coming from matplotlib, where ``cmap`` is the standard parameter name for colormaps.

  .. code-block:: python

      # These are equivalent
      chart.pcolormesh(data, colors="viridis")
      chart.pcolormesh(data, cmap="viridis")

      # Also works in Style initialisation
      style = Style(cmap="plasma", levels=[0, 10, 20])

      # Error only when both specified
      chart.pcolormesh(data, cmap="viridis", colors="plasma")  # ValueError

- **schema.reset()**: A new ``schema.reset()`` method returns the global schema to the earthkit-plots
  built-in defaults after a call to ``schema.use()``:

  .. code-block:: python

      schema.use("my-plugin")
      # ... plots using the plugin's style ...
      schema.reset()  # back to earthkit-plots defaults

Performance
+++++++++++

- **Faster figure-level plotting of multiple domains**: Figures containing many panels/domains plot
  significantly faster. Ancillary data loading and bounding-box CRS transforms are now cached,
  geometry is clipped to the active domain before projection, and the number of geometry-projection
  calls has been reduced. Import time has also been cut by around 70% (:pr:`194`).

Bug fixes
+++++++++

- Fixed grid detection for xarray data so that the grid specification is retrieved via the earthkit
  xarray accessor and the ``_earthkit`` attribute, improving grid detection for xarray inputs
  (:pr:`213`).

- Fixed regridding of HEALPix data defined in xarray without explicit geographic coordinates.
  Previously this produced incorrect output; the fix correctly derives lat/lon from the grid
  specification before regridding (:pr:`184`).

- Added a clear error when 1D data is passed to a geographic 2D plot context without a recognised
  grid specification. Previously this would produce a cryptic Qhull error or silent garbage output;
  now a ``ValueError`` is raised immediately with an actionable message (:pr:`184`).

- Fixed plotting of GRIB2 data on grid cells: the 0–360 longitude wrapping bug for fieldlists is
  resolved, and the automatic domain of coarse-resolution global data is now correctly extended to
  cover the whole globe (:pr:`190`).

- Fixed a bug which caused regular grid cells to be plotted half a cell out of position (:pr:`200`).

- Stopped cropping polygons in stereographic (and other non-cylindrical) projections, and fixed the
  plotting of very westerly domains near the dateline (:pr:`195`, :pr:`194`).

- Fixed Robinson coastlines and the rendering of dates in titles (:pr:`189`).

- Ensured that each distinct data variable receives its own style and its own legend entry, rather
  than sharing a single style/legend across different variables (:pr:`192`).

- Prevented a colorbar from being drawn on vector layers that have no associated colours (:pr:`199`).

- Fixed a bug which made the ``transform`` argument transparent (ignored); the ``transform`` argument
  is now respected (:pr:`201`).

- Improved handling of plots whose layers do not all contain a given metadata key, so titles and
  labels no longer fail when a key is missing from some layers (:pr:`187`).

- Fixed a bug when plotting data with integer units (:pr:`186`).

- Accept single-element 1D coordinates in metadata format strings, as well as scalars (:pr:`188`).

- Adapted time detection to work with earthkit-data 1.0.0, including better support for
  ``time.step`` with xarray inputs, and use of the earthkit-data time namespace (:pr:`191`, :pr:`193`).

- Addressed deprecation warnings and errors under matplotlib 3.11 and the latest earthkit-data
  (:pr:`210`).

- Corrected a dask chunking pattern (:pr:`198`).

- Removed unnecessary warnings emitted during plotting (:pr:`193`).

- Fixed a bug where the global matplotlib ``rcParams`` could be permanently modified by
  earthkit-plots style context managers. Style application is now fully scoped - matplotlib's
  global state is no longer mutated outside of an active ``Figure`` context.

Packaging
+++++++++

- Removed the ``fiona`` dependency. ``fiona`` is no longer required; installation is lighter and
  there is no change in functionality for users.

- The default style library is now bundled in-tree, so the external
  ``earthkit-plots-default-styles`` package is no longer a dependency (see above).
