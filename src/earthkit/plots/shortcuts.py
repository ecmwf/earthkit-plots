from earthkit.plots.temporal.stripes import Stripes
from earthkit.plots.temporal.timeseries import TimeSeries


def timeseries(
    data,
    *args,
    title="{variable_name}",
    xticks=None,
    yticks=None,
    xlabel=None,
    ylabel=None,
    plot="line",
    **kwargs
):
    ts = TimeSeries()

    getattr(ts, plot)(data, *args, **kwargs)
    ts.xlabel(xlabel)
    ts.ylabel(ylabel)

    if xticks is not None:
        if isinstance(xticks, str):
            ts.xticks(frequency=xticks)
        else:
            ts.xticks(**xticks)

    if yticks is not None:
        if isinstance(yticks, str):
            ts.yticks(frequency=yticks)
        else:
            ts.yticks(**yticks)

    ts.title(title)
    return ts


def stripes(data, *args, title=None, xticks=None, yticks=None, **kwargs):
    ts = Stripes()

    ts.stripes(data, *args, **kwargs)

    if yticks is not None:
        if isinstance(yticks, str):
            ts.yticks(frequency=yticks)
        else:
            ts.yticks(**yticks)

    if xticks is not None:
        if isinstance(xticks, str):
            ts.xticks(frequency=xticks)
        else:
            ts.xticks(**xticks)

    # ts.ax.axis("off")
    ts.ax.grid(False)

    if title is not None:
        ts.title(title)

    return ts
