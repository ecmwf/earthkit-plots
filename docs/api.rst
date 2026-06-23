API Reference
=============

This section contains the API reference for earthkit-plots. Each class and
function is documented on its own page; the tables below link through to them.

Core Components
---------------

.. currentmodule:: earthkit.plots

.. autosummary::
   :toctree: generated
   :nosignatures:

   Figure
   Subplot

High-level API
--------------

The shortcut API is exposed through three namespace objects on the top-level
``earthkit.plots`` package. Each groups the shortcut methods for one chart
type; the method tables on the pages below link through to the underlying
:mod:`~earthkit.plots.quickplot` functions.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Namespace
     - Description
   * - :doc:`ekp.geo <namespaces/geo>`
     - Geographic / map plots.
   * - :doc:`ekp.timeseries <namespaces/timeseries>`
     - Time series plots.
   * - :doc:`ekp.climatology <namespaces/climatology>`
     - Climatology (annual-cycle) plots.

.. toctree::
   :hidden:

   namespaces/geo
   namespaces/timeseries
   namespaces/climatology

Quickplot
---------

.. currentmodule:: earthkit.plots

.. autosummary::
   :toctree: generated

   quickplot

Styles
------

.. currentmodule:: earthkit.plots

.. autosummary::
   :toctree: generated
   :nosignatures:

   Style

.. autosummary::
   :toctree: generated

   load_style
   list_styles

Metadata
--------

.. autosummary::
   :toctree: generated
   :template: module.rst

   earthkit.plots.metadata.formatters
   earthkit.plots.metadata.labels
