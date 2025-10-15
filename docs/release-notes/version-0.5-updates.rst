Version 0.5 Updates
///////////////////

Version 0.5.0
=============

New features
++++++++++++

- The logic for xarray component extraction has been completely overhauled to
  better support non-geospatial data (:pr:`115`). The new logic is as follows:

  **Implicit x, y, z handling:**

  When an xarray Dataset(Array) is passed to a plotting function **without indication of x, y and z**,
  we call `_implicit_xyz()`, which handles the following cases:

  - **Data is 1-dimensional:**
    - Dataset(Array) is **dimensionless** → `y = values`, `x = indices`
    - Dataset(Array) **has a dimension** → `y = values`, `x = dimension values`

  - **Data is 2-dimensional:**
    - Calls `find_x()` and `find_y()` to identify common spatial dimensions (e.g. `longitude`, `latitude`)
    - If none are found, assumes the **first dimension** is `x` and the **second dimension** is `y`
    - Variable values (`data.values`) are used as `z`

  - **Data is higher-dimensional (3D+):**
    - Attempts to identify `x` and `y` using `find_x()` and `find_y()`
    - If found, extracts their coordinate values
    - Uses the full data array as `z`
    - Otherwise raises an error (explicit variable selection required)

  **Explicit x, y, z handling:**

  When an xarray Dataset(Array) is passed to a plotting function **with one or more of x, y and z**,
  we call `_explicit_xyz()`, which dispatches to one of `_explicit_xyz_1d()`, `_explicit_xyz_2d()`, or `_explicit_xyz_nd()` based on dimensionality:

  - **If all three** of `x`, `y`, and `z` are provided:
    - Each is extracted directly using `_get_coordinate_or_variable_values()`
    - No inference is needed

  - **If two** of the three are provided:
    - The missing coordinate is inferred from remaining dimensions
    - If both provided values are recognized as dimensions, the missing one is assumed to be the variable (`z = data.values`)
    - If one provided value is a variable and one is a dimension, the other dimension is inferred from what remains
    - If inference is not possible (e.g. ambiguous names, multi-variable datasets), a `ValueError` is raised

  - **If one** of `x`, `y`, or `z` is provided:
    - **If `x` is provided:**
      - If `x` corresponds to a dimension, `y = data.values`
      - If `x` is a variable or coordinate, infer `y` from remaining dimensions (or use index if none exist)
    - **If `y` is provided:**
      - If `y` corresponds to a dimension, `x = data.values`
      - If `y` is a variable or coordinate, infer `x` from remaining dimensions (or use index if none exist)
    - **If `z` is provided:**
      - Extract the specified variable or coordinate for `z`
      - Attempt to infer `x` and `y` using `find_x()` and `find_y()`; if none found, fall back to dimension order or index arrays

  - **For higher-dimensional (3D+) data:**
    - `_explicit_xyz_nd()` is a placeholder and currently not implemented — explicit handling will be required to extend to 3D+ inputs.

- Added a new `Timeseries` component and a convenience function `timeseries()`, imported into the top-level namespace (:pr:`115`).
  See the gallery example for usage: :ref:`/examples/gallery/timeseries/timeseries.ipynb`.
  This is an experimental feature and may be subject to change.

Bug fixes
++++++++++++++++++

- Fixed a bug where contour plots required multiple levels to be specified, even if only one level was needed (:pr:`132`).
- Fixed a bug where unit labels in legends were sometimes incorrect when using `quickplot` (:pr:`131`).
