Installation
============

Installing **earthkit-maps**
----------------------------

The easiest way to install **earthkit-maps** is with `pip`:

.. code-block:: bash

    pip install earthkit-maps

Alternatively, install via ``conda`` with:

.. code-block:: bash

    conda install earthkit-maps -c conda-forge

Optional dependencies
---------------------

To take advantage of all **earthkit-maps** features, you will need a few
additional dependencies.

- `SciPy <https://scipy.org/install/>`_: required for efficiently extracting
  sub-domains from data to speed up plotting.
- `cf-units <https://github.com/SciTools/cf-units>`_: required for advanced
  units features, including automatic unit conversion for styles with units
  attached.
