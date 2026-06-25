Version 0.3 Updates
/////////////////////////

Version 0.3.1
===============

Bug fixes
++++++++++++++++++

 - Fixed a bug that prevented plotting of NumPy arrays with a grid specification.
   You can now pass 1D NumPy arrays describing HEALPix or Octahedral data along
   with a corresponding gridspec to generate plots correctly.

Version 0.3.0
===============

Deprecations
+++++++++++++++++++

- :ref:`deprecated-quickplot`
- :ref:`deprecated-plot-method`
- :ref:`deprecated-block`
- :ref:`deprecated-gridpoints`

Quickplot module → function
++++++++++++++++++

The API for quickplot has changed:
 - `quickplot` is now a *function* rather than a *module*.
 - The `quickmap` module has also now been absorbed into the functionality of `quickplot`;
   `quickmap` has been deprecated and will be removed in a future release.
 - The `quickplot` function will attempt to infer an "optimal" style for the data
   passed to it, based on the metadata of the data.
 - You cannot currently choose different plot types (e.g. `contour`, `scatter`, etc.)
   using the `quickplot` function. This will be added in a future release. If you
   want more control over the plot type, you should construct the plot from the
   core `earthkit.plots` API.
See :ref:`here <deprecated-quickplot>` for more details.

Also see the user guide section :ref:`/examples/guide/02-quickplot.ipynb` for some examples using the
new `quickplot` function.

Quickplot method on `earthkit.plots.Map` objects
++++++++++++++++++

 - The `plot` method on `earthkit.plots.Map` objects has been deprecated and will be
   removed in a future release. The `quickplot` function should be used instead.
See :ref:`here <deprecated-plot-method>` for more details.

Renaming of `block` → `grid_cells`
++++++++++++++++++

 - The `block` method on `earthkit.plots.Map` objects has been renamed to `grid_celss`.
   The old name will be removed in a future release. The new name is more descriptive of
   the method's functionality, which is to represent the original grid cells of the data.
See :ref:`here <deprecated-block>` for more details.

Renaming of `gridpoints` → `grid_points`
++++++++++++++++++

 - The `gridpoints` method on `earthkit.plots.Map` objects has been renamed to `grid_points`.
   The old name will be removed in a future release. The new name follows the naming
   convention of other methods in `earthkit.plots`.
See :ref:`here <deprecated-gridpoints>` for more details.

Expanded interpolation & support for unstructured data
++++++++++++++++++

See :ref:`/examples/examples/unstructured-data.ipynb` for more details.

Formatting of units
++++++++++++++++

Whenever you include `"{units}"` in a title or label, you can choose to format the units
using exponential notation (default) or fractional notation. This is done in the
following way:

    - `"{units:~E}"` will format the units in exponential notation as a :math:`\LaTeX` string
      (e.g. :math:`m \cdot s^{-1}`).
    - `"{units:~F}"` will format the units in **inline** fractional notation as a :math:`\LaTeX` string (e.g. :math:`m/s`).
    - `"{units:~L}"` will format the units in **stacked** fractional notation as a :math:`\LaTeX` string
      (e.g. :math:`\frac{m}{s}`).
    - The tilde (`~`) character specifies whether the units should be shortened
      or not - excluding it will result in the full unit name (e.g. *metre/second*).

See :ref:`/examples/examples/string-formatting-units.ipynb` for more details.

Other new features
++++++++++++++++++

 - Added support for automatic style definitions which have no units.
 - Added support for EPSG codes for the `crs` argument in `earthkit.plots.Map`.
 - Added support for list-of-dicts `FieldList` objects from earthkit-data.
 - Added the `"Global"` named domain as an option for the `domain` argument in
   `earthkit.plots.Map`. This will plot the data over the entire globe, regardless
   of the data's original grid.
 - Better handling of non-contiguous data.

Bug fixes
++++++++++++++++++

 - Fixed a bug where data to the east of the prime meridian was not displayed correctly.
 - Fixed a bug where legends could not be plotted if certain metadata was missing.
 - Fixed a bug where there was sometimes a gap between grid cells around the prime meridian.
 - Tweaked behaviour of hatched contour plots to support newer versions of matplotlib, where
   `GeoContourSet` is now a subclass of `Collection`. This should fix compatibility issues
   for users of matplotlib 3.7.0 and above.
 - Overhaul of `Source` objects, which operate under the hood to provide a consistent
   interface for different data sources. This should improve performance and
   reliability.
