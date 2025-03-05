import warnings

from earthkit.plots.components.figures import Figure
from earthkit.plots.components import layouts
from earthkit.plots.schemas import schema
from earthkit.plots.utils import iter_utils

import earthkit.data
from earthkit.data import FieldList
from earthkit.data.core import Base

def quickplot(
    *args,
    rows=None,
    columns=None,
    domain=None,
    crs=None,
    methods="quickplot",
    mode="subplots",
    groupby=None,
    units=None,
    subplot_titles=None,
    **kwargs
):
    """
    Generate a convenient plot from the given data with optional grouping.
    
    Parameters
    ----------
    *args : list
        The data to be plotted.
    rows : int, optional
        Number of rows in the subplot layout.
    columns : int, optional
        Number of columns in the subplot layout.
    domain : string or tuple, optional
        The domain of the plot.
    methods : string or list, optional
        The plot method(s) to apply.
    mode : string, optional
        'subplots' (default) or 'overlay'.
    groupby : string, optional
        Dimension along which to group the data.
    units : string or list, optional
        Units to convert the data to.
    **kwargs : dict
        Additional arguments for the plot method(s).
    """
    field_list = []
    for arg in args:
        if isinstance(arg, FieldList):
            field_list.extend(list(arg))
        else:
            if not isinstance(arg, Base):
                arg = earthkit.data.from_object(arg)
            field_list.append(arg)
    args = FieldList.from_fields(field_list)
    
    if subplot_titles is None and groupby:
        subplot_titles = f"{{{groupby}}}"
    
    if groupby:
        unique_values = iter_utils.flatten(arg.metadata(groupby) for arg in args)
        unique_values = list(dict.fromkeys(unique_values))
        grouped_data = {val: args.sel(**{groupby: val}) for val in unique_values}
        
    elif mode == "subplots":
        grouped_data = {i: field for i, field in enumerate(args)}
    else:
        grouped_data = {None: args}
    
    n_plots = len(grouped_data)
    if mode == "subplots":
        rows, columns = layouts.rows_cols(n_plots, rows, columns)
    else:
        rows, columns = 1, 1
    
    figure = Figure(rows=rows, columns=columns)
    if not isinstance(methods, (list, tuple)):
        methods = [methods] * len(args)
    if not isinstance(units, (list, tuple)):
        units = [units] * len(args)
    
    for i, (group_val, group_args) in enumerate(grouped_data.items()):
        subplot = figure.add_map(domain=domain, crs=crs)
        
        if isinstance(group_args, FieldList):
            for j, (arg, method) in enumerate(zip(group_args, methods)):
                unit = units[j]
                try:
                    getattr(subplot, method)(arg, units=unit, **kwargs)
                except Exception as err:
                    warnings.warn(
                        f"Failed to execute {method} on given data with: \n"
                        f"{err}\n\n"
                        "consider constructing the plot manually."
                    )
                    raise err
        else:
            unit = units[i]
            try:
                getattr(subplot, methods[i])(group_args, units=unit, **kwargs)
            except Exception as err:
                warnings.warn(
                    f"Failed to execute {methods[i]} on given data with: \n"
                    f"{err}\n\n"
                    "consider constructing the plot manually."
                )
                raise err
        
        for m in schema.quickmap_subplot_workflow:
            args = []
            if m == "title" and subplot_titles:
                args = [subplot_titles]
            try:
                getattr(subplot, m)(*args)
            except Exception as err:
                warnings.warn(
                    f"Failed to execute {m} on given data with: \n"
                    f"{err}\n\n"
                    "consider constructing the plot manually."
                )
    
    for m in schema.quickmap_figure_workflow:
        try:
            getattr(figure, m)()
        except Exception as err:
            warnings.warn(
                f"Failed to execute {m} on given data with: \n"
                f"{err}\n\n"
                "consider constructing the plot manually."
            )
    
    return figure
