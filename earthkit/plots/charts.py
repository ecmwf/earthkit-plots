from plotly.subplots import make_subplots

from earthkit.plots import bar, box, inputs, line
from earthkit.plots.schemas import schema


class Chart:
    def __init__(self, rows=None, columns=None, **kwargs):
        self._rows = rows
        self._columns = columns

        self._fig = None
        self._subplots = []
        self._subplots_kwargs = kwargs
        self._subplot_titles = None
        self._subplot_y_titles = None
        self._layout_override = dict()

    def set_subplot_titles(method):
        def wrapper(self, *args, **kwargs):
            if self._subplot_titles is None:
                if args:
                    try:
                        ds = inputs.to_xarray(args[0])
                    except NotImplementedError:
                        pass
                    else:
                        self._subplot_titles = list(ds.data_vars)
                        self._subplot_y_titles = [
                            ds[data_var].attrs.get("units", "")
                            for data_var in ds.data_vars
                        ]
            return method(self, *args, **kwargs)

        return wrapper

    @property
    def fig(self):
        if self._fig is None:
            self._fig = make_subplots(
                rows=self.rows,
                cols=self.columns,
                subplot_titles=self._subplot_titles,
                **self._subplots_kwargs,
            )
        return self._fig

    @property
    def rows(self):
        if self._rows is None:
            self._rows = 1
        return self._rows

    @property
    def columns(self):
        if self._columns is None:
            self._columns = 1
        return self._columns

    def add_trace(self, *args, **kwargs):
        self.fig.add_trace(*args, **kwargs)

    @set_subplot_titles
    def line(self, *args, **kwargs):
        traces = line.line(*args, **kwargs)
        for i, trace in enumerate(traces):
            if isinstance(trace, list):
                if self._fig is None:
                    self._rows = self._rows or len(traces)
                    self._columns = self._columns or 1
                for sub_trace in trace:
                    self.add_trace(sub_trace, row=i + 1, col=1)
            else:
                self.add_trace(trace)

    @set_subplot_titles
    def box(self, *args, **kwargs):
        traces = box.box(*args, **kwargs)
        for i, trace in enumerate(traces):
            if isinstance(trace, list):
                if self._fig is None:
                    self._rows = self._rows or len(traces)
                    self._columns = self._columns or 1
                for sub_trace in trace:
                    if not isinstance(sub_trace, (list, tuple)):
                        sub_trace = [sub_trace]
                    for actual_trace in sub_trace:
                        self.add_trace(actual_trace, row=i + 1, col=1)
            else:
                self.add_trace(trace)

    @set_subplot_titles
    def bar(self, *args, **kwargs):
        traces = bar.bar(*args, **kwargs)
        for i, trace in enumerate(traces):
            if isinstance(trace, list):
                if self._fig is None:
                    self._rows = self._rows or len(traces)
                    self._columns = self._columns or 1
                for sub_trace in trace:
                    self.add_trace(sub_trace, row=i + 1, col=1)
            else:
                self.add_trace(trace)

    def title(self, label):
        self._layout_override["title"] = label

    def show(self):
        layout = {
            **schema.figures.figure.layout,
            **self._layout_override,
        }
        self.fig.update_layout(**layout)
        for i in range(self.rows * self.columns):
            y_key = f"yaxis{i+1 if i>0 else ''}"
            x_key = f"xaxis{i+1 if i>0 else ''}"
            self.fig.update_layout(
                **{
                    x_key: layout["xaxis"],
                    y_key: {
                        **layout["yaxis"],
                        **{"title": self._subplot_y_titles[i]},
                    },
                }
            )
        return self.fig.show()
