from plotly.subplots import make_subplots

from earthkit.plots import bar, box, inputs, line, metadata
from earthkit.plots.schemas import schema

ADD_TRACE_KWARGS = [
    "row",
    "col",
    "column",
    "secondary_y",
]


def get_title(ds, order=None):
    if ds.__class__.__name__ == "Dataset":
        name = list(order or ds.data_vars)
        if len(name) == 1:
            name = name[0]
    else:
        name = ds.name
    return name


def get_units(ds, order=None):
    if ds.__class__.__name__ == "Dataset":
        units = [
            metadata.units.pretty_units(ds[var].attrs.get("units", ""))
            for var in list(order or ds.data_vars)
        ]
        if len(units) == 1:
            units = units[0]
    else:
        units = metadata.units.pretty_units(ds.attrs.get("units", ""))
    return units


class Chart:
    def __init__(self, rows=None, columns=None, **kwargs):
        self._rows = rows
        self._columns = columns

        self._fig = None
        self._subplots = []
        self._subplots_kwargs = kwargs
        self._subplot_titles = dict()
        self._subplot_y_titles = None
        self._layout_override = dict()

        self._prepared = False

    def add_traces(method):
        def wrapper(self, *args, units=None, order=None, **kwargs):

            trace_kwargs = {k: kwargs.pop(k) for k in ADD_TRACE_KWARGS if k in kwargs}
            if "column" in trace_kwargs:
                trace_kwargs["col"] = trace_kwargs.pop("column")

            title = ""
            units_string = ""
            if args:
                ds = inputs.to_xarray(args[0])
                if units is not None:
                    ds = metadata.units.convert_dataset_units(ds, units)

                title = get_title(ds, order)
                units_string = get_units(ds, order)
                traces = method(self, ds, order=order, **kwargs)
            else:
                traces = method(self, *args, order=order, **kwargs)

            for i, trace in enumerate(traces):
                if isinstance(trace, list):
                    if self._fig is None:
                        self._rows = self._rows or len(traces)
                        self._columns = self._columns or 1
                        self._subplot_y_titles = [" "] * (self._rows * self._columns)
                    for sub_trace in trace:
                        if not isinstance(sub_trace, (list, tuple)):
                            sub_trace = [sub_trace]
                        actual_trace_kwargs = {
                            k: v
                            for k, v in trace_kwargs.items()
                            if k not in ("row", "col")
                        }
                        row = trace_kwargs.get("row", i + 1)
                        col = trace_kwargs.get("col", 1)
                        j = self._columns * (row - 1) + (col - 1)

                        if isinstance(title, list):
                            self._subplot_titles = {
                                str(k): title[k] for k in range(len(title))
                            }
                            self._subplot_y_titles = units_string
                        else:
                            self._subplot_titles[str(j)] = title
                            self._subplot_y_titles[j] = units_string

                        for actual_trace in sub_trace:
                            self.add_trace(
                                actual_trace, row=row, col=col, **actual_trace_kwargs
                            )
                else:
                    self.add_trace(trace, **trace_kwargs)
            return self

        return wrapper

    @property
    def fig(self):
        if self._fig is None:
            self._fig = make_subplots(
                rows=self.rows,
                cols=self.columns,
                subplot_titles=[f"{i}" for i in range(self._rows * self._columns)],
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

    @add_traces
    def line(self, *args, **kwargs):
        return line.line(*args, **kwargs)

    @add_traces
    def box(self, *args, **kwargs):
        return box.box(*args, **kwargs)

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

    def _prepare_fig(self):
        if self._prepared:
            return
        layout = {
            **schema.figures.figure.layout,
            **self._layout_override,
        }
        self.fig.update_layout(**layout)
        for i in range(self.rows * self.columns):
            y_key = f"yaxis{i + 1 if i > 0 else ''}"
            x_key = f"xaxis{i + 1 if i > 0 else ''}"

            self.fig.update_layout(
                **{
                    x_key: layout["xaxis"],
                    y_key: {
                        **layout["yaxis"],
                        **{"title": self._subplot_y_titles[i]},
                    },
                }
            )
        self.fig.for_each_annotation(
            lambda a: a.update(text=self._subplot_titles[a.text])
        )
        self._prepared = True

    def show(self):
        self._prepare_fig()
        return self.fig.show()

    def save(self, filename):
        self._prepare_fig()
        return self.fig.write_image(filename)
