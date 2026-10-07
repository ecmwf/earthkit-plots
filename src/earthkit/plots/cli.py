# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""Commands contributed by earthkit-data to the shared ``earthkit`` command line interface.

The ``earthkit`` console script itself lives in :mod:`earthkit.utils.cli`. The commands
defined here are registered with it through the ``earthkit.cli`` entry point group in
``pyproject.toml``, so ``earthkit ls <file>`` becomes available once earthkit-data is installed.
"""

import click


@click.command()
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
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
def plot(filename, save, index, domain, method, crs, style, units, groupby, size, title, subtitles, rows, cols):
    """List the contents of FILENAME as a metadata summary table."""
    import earthkit.data as ekd
    import earthkit.plots as ekp
    
    data = ekd.from_source("file", filename)
    if index is not None:
        if not index.isdigit():
            islice = slice(*map(int, index.split("/")))  
            data = data.to_fieldlist()[islice]
        else:
            data = data.to_fieldlist()[int(index)]
    
    chart = getattr(ekp.geo, method)(data, domain=domain, crs=crs, style=style, units=units, groupby=groupby, figsize=size.split("/"), rows=rows, columns=cols)
    if title is not None:
        chart.title(title)
    if subtitles is not None:
        chart.subplot_titles(subtitles)
    if save:
        chart.save(save)
    else:
        chart.show()


COMMANDS = {
    "plot": plot,
}