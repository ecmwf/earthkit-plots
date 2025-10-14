Version 0.4 Updates
/////////////////////////

Version 0.4.1
===============

Bug fixes
++++++++++++++++++

 - Made the default behaviour of quickplot to **not** combine vector components by default. This is to avoid unforeseen
   issues with some data sources. This will be addressed in release 0.6.

Version 0.4.0
===============

New features
++++++++++++++++++

- Added streamplot support (:pr:`112`). See the gallery example for usage: :ref:`/examples/gallery/vector-data/streamlines.ipynb`.
- Added vector identification in quickplots, making the default behaviour be to plot vector components as a quiver field with quickplot (:pr:`117`).
- Added support for styles to require matching multiple criteria. This makes it possible to have automatic styles for vector fields (:pr:`108`).
- General improvements to documentation, including more links to underlying libraries
  like cartopy and matplotlib, more extensive API documentation, and more examples (:pr:`122`).
- Added support for unit aliases to make certain common units in meteorology compatible with Pint (:pr:`102`).
- Added `cities` convenience method to the `Figure` class (:pr:`104`).
- Added image comparison tests to ensure that the plots produced by earthkit-plots
  are consistent across different versions (:pr:`107`).

Bug fixes
++++++++++++++++++
- Fixed a bug where the magic key `"{lead_time}"` was not working correctly with layer indexing in metadata formatters (:pr:`123`).
- Fixed a bug where quiver arrows were far too long when using a regular latitude-longitude coordinate system (:issue:`83`).
- Fixed a bug where contour lines would have messy graphical errors when a supertitle was added to a plot (:pr:`113`).
- Fixed a bug where huge 1D arrays were incorrectly attempting to form a meshgrid with themselves, causing memory errors (:pr:`97`).
- Fixed a bug where schemas were holding state from the default schema and preventing overrides (:pr:`101`).
- Fixed a bug where plotting wind barbs failed if there was already a legend on the plot (:pr:`118`).
- Fixed an issue where ecCodes debug messages about the gridSpec key were printed on every plot (:pr:`124`).
