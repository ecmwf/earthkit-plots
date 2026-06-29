Welcome to the earthkit-plots documentation
======================================================

|Static Badge| |image1| |License: Apache 2.0|

.. |Static Badge| image:: https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE/foundation_badge.svg
   :target: https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE
.. |image1| image:: https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity/graduated_badge.svg
   :target: https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity
.. |License: Apache 2.0| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://opensource.org/licenses/apache-2-0

.. important::

    This software is in **release candidate** stage. It is not yet considered stable and may still undergo significant changes before the final 1.0 release. We welcome feedback and contributions as we approach that milestone.

**earthkit-plots** is a high-level Python library for producing publication-quality
scientific graphics with minimal code. Built on **matplotlib**, **cartopy**,
**xarray**, and the broader **earthkit** ecosystem, it enriches these tools with
domain-specific knowledge so you can focus on your data rather than plot
configuration.

.. grid:: 1
   :gutter: 2

   .. grid-item-card:: Why earthkit-plots?
      :img-top: _static/earthkit-plots-grey.svg
      :link: why
      :link-type: doc
      :class-card: sd-shadow-sm

      The motivation and key features of earthkit-plots.


.. grid:: 1 1 2 2
   :gutter: 2

   .. grid-item-card:: Installation
      :img-top: _static/rocket.svg
      :link: install
      :link-type: doc
      :class-card: sd-shadow-sm

      New to earthkit-plots? Start here with installation.

   .. grid-item-card:: Tutorials
      :img-top: _static/book.svg
      :link: examples/examples/examples
      :link-type: doc
      :class-card: sd-shadow-sm

      Step-by-step examples to learn earthkit-plots.

   .. grid-item-card:: Gallery
      :img-top: _static/palette.svg
      :link: examples/gallery/gallery
      :link-type: doc
      :class-card: sd-shadow-sm

      A visual gallery of what earthkit-plots can produce.

   .. grid-item-card:: Styles gallery
      :img-top: _static/tool.svg
      :link: styles-gallery
      :link-type: doc
      :class-card: sd-shadow-sm

      Browse the built-in style libraries and colour scales.

   .. grid-item-card:: Domains gallery
      :img-top: _static/globe.svg
      :link: domains-gallery
      :link-type: doc
      :class-card: sd-shadow-sm

      Browse the predefined geographic domains.

   .. grid-item-card:: API Reference Guide
      :img-top: _static/brackets-contain.svg
      :link: api
      :link-type: doc
      :class-card: sd-shadow-sm

      Detailed documentation of all functions and classes.


.. important::

    This software is **Graduated** and subject to ECMWF's guidelines on `Software Maturity <https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity>`_.

**Support**

Have a feature request or found a bug? Feel free to open an
`issue <https://github.com/ecmwf/earthkit-plots/issues/new/choose>`_.


.. toctree::
   :maxdepth: 1
   :hidden:

   why

.. toctree::
   :caption: User guide
   :maxdepth: 1
   :hidden:

   install
   examples/examples/examples.ipynb
   examples/gallery/gallery.ipynb
   styles-gallery
   domains-gallery
   api


.. toctree::
   :caption: Developer guide
   :maxdepth: 1
   :hidden:

   development


.. toctree::
   :caption: Extras
   :maxdepth: 1
   :hidden:

   release-notes/index
   licence
   genindex
