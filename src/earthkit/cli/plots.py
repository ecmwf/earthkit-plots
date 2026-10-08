# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""Commands contributed by earthkit-plots to the shared ``earthkit`` command line interface.

The ``earthkit`` console script itself lives in :mod:`earthkit.cli.main` (earthkit-utils). This module is
part of the ``earthkit.cli`` namespace package, which is shared by all earthkit packages, and registers its
commands on the shared ``earthkit`` group with ``@earthkit.command()``, so ``earthkit plot <file>`` becomes
available once earthkit-plots is installed.

This module lives outside of ``earthkit.plots`` on purpose, so that listing the commands does not import
``earthkit.plots``. Only import :mod:`click` and light standard library modules at module level, and import
everything else inside the command functions.
"""

import click
from earthkit.cli.main import earthkit
from earthkit.cli.standard_args import add_options, source_options


@earthkit.command()
@add_options([source_options(positional=True)])
@click.option(
    "-s",
    "--save",
    type=str,
    default=None,
    help="Target file to save the plot to.",
)
@click.option(
    "-i",
    "--index",
    type=str,
    default=None,
    help="Index of the data to plot.",
)
@click.option(
    "-d",
    "--domain",
    type=str,
    default=None,
    help="Domain of the data to plot.",
)
@click.option(
    "-m",
    "--method",
    type=str,
    default="plot",
    help="Method to use for plotting the data.",
)
@click.option(
    "--crs",
    type=str,
    default=None,
    help="CRS of the plot.",
)
@click.option(
    "--style",
    type=str,
    default="auto",
    help="Style of the plot.",
)
@click.option(
    "-u",
    "--units",
    type=str,
    default=None,
    help="Units of the plot.",
)
@click.option(
    "-g",
    "--groupby",
    type=str,
    default=None,
    help="Group by parameter for the plot.",
)
@click.option(
    "--size",
    type=str,
    default=None,
    help="Size of the plot.",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="Title of the plot.",
)
@click.option(
    "--subtitles",
    type=str,
    default=None,
    help="Subtitles of the plot.",
)
@click.option(
    "--rows",
    type=int,
    default=None,
    help="Number of rows in the plot.",
)
@click.option(
    "--cols",
    type=int,
    default=None,
    help="Number of columns in the plot.",
)
def plot(source, save, index, domain, method, crs, style, units, groupby, size, title, subtitles, rows, cols):
    """Plot data on a map.

    SOURCE is the earthkit-data source to read, as [NAME:]VALUE, e.g. a file path (GRIB, NetCDF, ...),
    'url:https://myhost.int/file.nc' or a JSON request such as 'cds:{"dataset": ..., ...}'.
    NAME is 'file' if not given. Several sources are merged.

    \b
    Example:
        earthkit plot input.grib --index 0:4 --save plot.png
    """  # noqa: D301 (\b is a Click paragraph marker)
    import earthkit.plots as ekp

    data = source
    if index is not None:
        data = data.to_fieldlist()[_parse_index(index)]
    
    figsize = tuple(map(int, size.split("/"))) if size is not None else None
    chart = getattr(ekp.geo, method)(data, domain=domain, crs=crs, style=style, units=units, groupby=groupby, figsize=figsize, rows=rows, columns=cols)
    if title is not None:
        chart.title(title)
    if subtitles is not None:
        chart.subplot_titles(subtitles)
    if save:
        chart.save(save)
    else:
        chart.show()


def _parse_index(index):
    """Parse an index string: a slice ("1:7", "::2"), list ("4,5,8") or int ("3")."""
    if ":" in index:
        parts = [int(p) if p.strip() else None for p in index.split(":")]
        return slice(*parts)
    if "," in index:
        return [int(p) for p in index.split(",")]
    return int(index)