
from earthkit.plots.temporal.timeseries import TimeSeries
from earthkit.plots.temporal.stripes import Stripes


def timeseries(data, *args, title="{variable_name}", xticks=None, xlabel=None, ylabel=None, plot="line", **kwargs):
    ts = TimeSeries()

    getattr(ts, plot)(data, *args, **kwargs)
    ts.xlabel(xlabel)
    ts.ylabel(ylabel)
    
    if xticks is not None:
        if isinstance(xticks, str):
            xticks = {"major": xticks}
        ts.xticks(**xticks)

    ts.title(title)
    return ts


def stripes(data, *args, title=None, xticks=None, **kwargs):
    ts = Stripes()

    ts.stripes(data, *args, **kwargs)

    if xticks is not None:
        if isinstance(xticks, str):
            xticks = {"major": xticks}
        ts.xticks(**xticks)

    # ts.ax.axis("off")
    ts.ax.grid(False)

    if title is not None:
        ts.title(title)

    return ts