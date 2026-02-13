Version 0.6 Updates
///////////////////

Version 0.6.1
=============

New features
++++++++++++

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

  .. code-block:: python

      # These are equivalent
      chart.pcolormesh(data, colors="viridis")
      chart.pcolormesh(data, cmap="viridis")

      # Also works in Style initialisation
      style = Style(cmap="plasma", levels=[0, 10, 20])

      # Error only when both specified
      chart.pcolormesh(data, cmap="viridis", colors="plasma")  # ValueError

Version 0.6.0
=============

New features
++++++++++++

- **Sources module redesign**: The sources module has been redesigned around a Strategy pattern,
  providing clearer separation of data source extraction logic. Most of this is not visible to users,
  but it lays the groundwork for future improvements in data handling and plotting consistency.

  Key improvements include:

  - New ``DimensionInfo`` class for representing plot dimensions with units-aware abstractions
  - Dimension-aware string formatting (e.g., ``{y.units}``, ``{z.variable_name}``)
  - Unit conversion and regridding now performed within ``Source`` objects for consistency
  - Enhanced x, y, z extraction with plot context awareness for better handling of ambiguous cases
  - Completely rewritten xarray extraction logic with improved documentation

  (:pr:`161`)

- Slight adjustments to the built-in Denmark and Ireland domains to better align with coastlines and islands (:pr:`151`).

- **Faster Natural Earth layer rendering**: Natural Earth layers (e.g., coastlines, borders) now render
  2-3x faster, with up to 10x speedup in some cases. The improvement uses pre-transformation of geometry
  to the map's projection via a new ``transform_first`` parameter, enabled by default for features like
  coastlines where it produces no visible differences. For features with long straight segments that may
  be susceptible to warping, the parameter remains available but disabled by default. (:pr:`162`)

- **Multiple data sources for ancillary shapes**: Ancillary shape methods (coastlines, borders, countries)
  now support multiple data sources including Natural Earth and GISCO. The ``borders`` and ``countries``
  methods now formally support GISCO sources, and a new ``nuts_regions`` convenience method has been added
  for plotting NUTS regions. (:pr:`163`)

Bug fixes
++++++++++++++++++

- Fixed auto-range detection in ``contourf`` to properly handle infinite values alongside NaN values,
  preventing errors when plotting data containing infinities (:issue:`155`).
