
from plotly.subplots import make_subplots
from cf_units.tex import tex
from cf_units import Unit
import earthkit.data


DEFAULT_COLOR = "#779FD6"


XAXIS_DEFAULT = dict(
    dtick=6*60*60*1000,
    ticklabelmode="period",
    tickformat="%H %a %-d",
    minor=dict(
        dtick=6*60*60*1000,
        tick0="2017-01-01T00",
        ticklen=4,
    ),
    showgrid=True,
    gridcolor="#e6e6e6",
)

YAXIS_DEFAULT = dict(
    fixedrange=True,
    showgrid=True,
    gridcolor="#e6e6e6",
    zeroline=True,
    zerolinewidth=0.5,
    zerolinecolor="#e6e6e6",
)


PRETTY_UNITS = {
    "celsius": "°C",
}


def unpack(data):
    if isinstance(data, earthkit.data.core.Base):
        data = data.to_xarray()
    return data


def multi_variable(function):
    def wrapper(data, *args, colors=DEFAULT_COLOR, units=None, accumulations=["Total Precipitation"], **kwargs):
        data = unpack(data)
        
        if not isinstance(colors, list):
            colors = [colors]
        if len(colors) < len(data.data_vars):
            colors = colors * int((len(data.data_vars) / len(colors))+1)
        
        fig = make_subplots(
            rows=len(data.data_vars), cols=1,
            shared_xaxes=True,
            subplot_titles=list(data.data_vars),
        )
        
        for i, (var_name, da) in enumerate(data.data_vars.items()):
            target_units = units
            if isinstance(units, dict):
                target_units = units.get(var_name)
            
            if target_units is not None:
                source_units = Unit(da.attrs.get("units"))
                da.values = source_units.convert(da.values, target_units)
                da.attrs["units"] = target_units
            
            for trace in function(da, *args, color=colors[i], **kwargs):
                fig.add_trace(trace, row=i+1, col=1)
        
        fig.update_layout(
            showlegend=False,
            boxmode="overlay",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x",
            height=200*len(data.data_vars),
        )
        
        for i, (var_name, da) in enumerate(data.data_vars.items()):
            
            if var_name in accumulations:
                test = da.values.copy()
                test = test[0][0][0]
                test[1:] = test[1:] - test[:-1].copy()
                da.values[0][0][0] = test
            
            units = da.attrs.get("units", "")
            units = PRETTY_UNITS.get(units, units)
            try:
                units = f"${tex(units)}$"
            except SyntaxError:
                pass
            
            y_key = f"yaxis{i+1 if i>0 else ''}"
            x_key = f"xaxis{i+1 if i>0 else ''}"
            fig.update_layout(
                **{
                    x_key: XAXIS_DEFAULT,
                    y_key: {
                        **YAXIS_DEFAULT,
                        **{"title": units},
                    }
                },
            )
        
        return fig
    return wrapper