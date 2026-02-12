Version 0.6 Updates
///////////////////

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
