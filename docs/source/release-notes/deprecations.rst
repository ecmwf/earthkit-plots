Deprecations
=============

.. _deprecated-1.1.0:

Version 1.1.0
-----------------

.. _deprecated-quickplot-function:

`ekp.quickplot` → `ekp.geo.plot`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The top-level ``earthkit.plots.quickplot`` function (and the ``ekp.geo.quickplot``
alias) is deprecated and will be removed in earthkit-plots 2.0. Calling it now
raises a ``DeprecationWarning``. Use ``ekp.geo.plot`` instead, which accepts
exactly the same arguments and returns the same objects. See the
:doc:`ekp.geo </namespaces/geo>` namespace for the full set of map shortcuts.
``ekp.quickplot`` has been deprecated to avoid confusion when plotting arbitrary
input data. Now, namespace-specific plotting functions like ``ekp.geo.plot``
and ``ekp.timeseries.plot`` improve clarity and understanding of the plotting context.
.. _deprecated-0.3.0:

Version 0.3.0
-----------------

.. _deprecated-quickplot:

Quickplot
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The API for quickplot has changed:
 - `quickplot` is now a *function* rather than a *module*.
 - The `quickplot` function will attempt to infer an "optimal" style for the data
   passed to it, based on the metadata of the data.
 - You cannot currently choose different plot types (e.g. `contour`, `scatter`, etc.)
   using the `quickplot` function. This will be added in a future release. If you
   want more control over the plot type, you should construct the plot from the
   core `earthkit.plots` API.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_quickplot.py

   * - New code
   * -

        .. literalinclude:: include/migrated_quickplot.py

.. _deprecated-plot-method:

`plot` → `quickplot`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The `plot` method on `earthkit.plots.Map` objects has been deprecated and will be
removed in a future release. The `quickplot` function should be used instead.

.. note::

   This guidance has since been reversed. As of version 1.0, `Map.plot` is the
   auto-detecting plot method and the top-level `quickplot` function is itself
   deprecated in favour of `ekp.geo.plot`; see :ref:`deprecated-quickplot-function`.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_plot.py

   * - New code
   * -

        .. literalinclude:: include/migrated_plot.py

.. _deprecated-block:

`block` → `grid_cells`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The `block` method on `earthkit.plots.Map` objects has been renamed to `grid_cells`.
The new name is more descriptive of the method's functionality, which is to represent the
original grid cells of the data.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_block.py

   * - New code
   * -

        .. literalinclude:: include/migrated_block.py

.. _deprecated-gridpoints:

`gridpoints` → `grid_points`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The `gridpoints` method on `earthkit.plots.Map` objects has been renamed to `grid_points`.
The new name follows the naming convention of other methods in `earthkit.plots`.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_gridpoints.py

   * - New code
   * -

        .. literalinclude:: include/migrated_gridpoints.py
