# Copyright 2024, European Centre for Medium Range Weather Forecasts.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from plotly.subplots import make_subplots

from earthkit.plots.interactive import bar, box, inputs, line

DEFAULT_LAYOUT = {
    "colorway": [
        "#636EFA",
        "#EF553B",
        "#00CC96",
        "#AB63FA",
        "#FFA15A",
        "#19D3F3",
        "#FF6692",
        "#B6E880",
        "#FF97FF",
        "#FECB52",
    ],
    "hovermode": "x",
    "plot_bgcolor": "white",
    "xaxis": {
        "gridwidth": 1,
        "showgrid": False,
        "showline": False,
        "zeroline": False,
    },
    "yaxis": {
        "linecolor": "black",
        "gridcolor": "#EEEEEE",
        "showgrid": True,
        "showline": True,
        "zeroline": False,
    },
    "height": 750,
    "showlegend": False,
}


class Chart:
    """
    A class for creating and managing multi-subplot interactive charts using Plotly.

    Parameters
    ----------
    rows : int, optional
        Number of rows in the chart grid. Default is 1.
    columns : int, optional
        Number of columns in the chart grid. Default is 1.
    **kwargs : dict
        Additional arguments passed to `plotly.subplots.make_subplots`.
    """

    def __init__(self, rows=None, columns=None, **kwargs):
        self._rows = rows
        self._columns = columns

        self._fig = None
        self._subplots = []
        self._subplots_kwargs = kwargs
        self._subplot_titles = None
        self._subplot_y_titles = None
        self._subplot_x_titles = None
        self._layout_override = dict()

    def set_subplot_titles(method):
        def wrapper(self, *args, **kwargs):
            if self._subplot_titles is None:
                if args:
                    try:
                        ds = inputs.to_xarray(args[0])
                    except Exception:
                        pass
                    else:
                        self._subplot_titles = list(ds.data_vars)
                        titles = [
                            ds[data_var].attrs.get("units", "")
                            for data_var in ds.data_vars
                        ]
                        if kwargs.get("y") is not None:
                            self._subplot_x_titles = titles
                        else:
                            self._subplot_y_titles = titles
            return method(self, *args, **kwargs)

        return wrapper

    @property
    def fig(self):
        """
        The Plotly figure object representing the chart.
        """
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
        """The number of rows in the chart grid."""
        if self._rows is None:
            self._rows = 1
        return self._rows

    @property
    def columns(self):
        """The number of columns in the chart grid."""
        if self._columns is None:
            self._columns = 1
        return self._columns

    def add_trace(self, *args, **kwargs):
        """
        Adds a trace to the chart at the appropriate location.

        Parameters
        ----------
        *args : tuple
            Positional arguments passed to `plotly.graph_objects.Figure.add_trace`.
        **kwargs : dict
            Keyword arguments passed to `plotly.graph_objects.Figure.add_trace`.
        """
        self.fig.add_trace(*args, **kwargs)

    @set_subplot_titles
    def line(self, *args, **kwargs):
        """
        Adds a line plot to the chart.

        Parameters
        ----------
        data : array-like or earthkit.data.FieldList
            The data to be plotted.
        *args : tuple
            Positional arguments passed to the line plot generation function.
        **kwargs : dict
            Additional options for customizing the line plot.

        Notes
        -----
        Line plots are added as individual traces to each subplot.
        Titles are inferred from data attributes if not provided.
        """
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
        """
        Generate a set of box plot traces based on the provided data and quantiles.

        Parameters
        ----------
        data : array-like or earthkit.data.FieldList
            The data to be plotted.

        *args : tuple
            Positional arguments passed to the plotly `go.Box` constructors.

        quantiles : list of float, optional
            A list of quantiles to calculate for the data. The default is
            [0.05, 0.25, 0.5, 0.75, 0.95]. Note that any number of quantiles
            can be provided, but the default is based on the standard five-point
            box plot.

        time_axis : int, optional
            The axis along which to calculate the quantiles. The default is 0.

        **kwargs : dict
            Additional keyword arguments passed to the `go.Box` constructor.

        Returns
        -------
        list of plotly.graph_objects.Box

        Notes
        -----
        - The width of the box plots is scaled based on the x-axis spacing.
        - Extra boxes are added for quantiles beyond the standard five-point box plot.
        - Hover information is included for quantile scatter points, showing the
          quantile value and percentage.
        """
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
        """
        Adds a bar plot to the chart.

        Parameters
        ----------
        data : array-like or earthkit.data.FieldList
            The data to be plotted.
        *args : tuple
            Positional arguments passed to the bar plot generation function.
        **kwargs : dict
            Additional options for customizing the bar plot.

        Notes
        -----
        Bar plots are added as individual traces to each subplot.
        Titles are inferred from data attributes if not provided.
        """
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

    def title(self, title):
        """
        Set the overall chart title.

        Parameters
        ----------
        title : str
            The title to display at the top of the chart.
        """
        self._layout_override["title"] = title

    def show(self, *args, **kwargs):
        """
        Display the chart.

        Parameters
        ----------
        *args : tuple
            Additional arguments for `plotly.graph_objects.Figure.show`.
        renderer : str, optional
            The renderer to use for displaying the chart. The default is "browser".
            For static plots, use "png".
        **kwargs : dict
            Additional options for rendering the chart.

        Returns
        -------
        None
        """
        layout = {
            **DEFAULT_LAYOUT,
            **self._layout_override,
        }
        # Temporary fix to remove _parent keys from nested dictionaries
        for k in layout:
            if isinstance(layout[k], dict):
                layout[k] = {
                    k2: v for k2, v in layout[k].items() if not k2.startswith("_")
                }
        self.fig.update_layout(**layout)
        for i in range(self.rows * self.columns):
            y_key = f"yaxis{i+1 if i>0 else ''}"
            x_key = f"xaxis{i+1 if i>0 else ''}"
            if self._subplot_x_titles:
                self.fig.update_layout(
                    **{
                        y_key: layout["yaxis"],
                        x_key: {
                            **layout["xaxis"],
                            **{"title": self._subplot_x_titles[i]},
                        },
                    }
                )
            if self._subplot_y_titles:
                self.fig.update_layout(
                    **{
                        x_key: layout["xaxis"],
                        y_key: {
                            **layout["yaxis"],
                            **{"title": self._subplot_y_titles[i]},
                        },
                    }
                )
        return self.fig.show(*args, **kwargs)
