

import plotly.graph_objects as go
from pandas import Timestamp

from earthkit.plots.meteograms.analysis import meteogramify


TIME_DIMS = ["time", "t", "month"]

DEFAULT_QUANTILES = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]

def violin(data, quantiles=None, dim=None, time_frequency=None, how="mean", colors=["#F74F4F", "blue"]):
    
    if dim is None:
        dim = guess_dim(data)
    time_dim = "t" #get_time_dim(data)

    quantiles = quantiles or DEFAULT_QUANTILES
    extra_boxes = (len(quantiles) - 5) // 2

    if time_frequency is not None:
        if not isinstance(how, list):
            how = [how]
        data = [
            meteogramify(data, time_frequency=time_frequency, how=method)
            for method in how
        ]
    else:
        data = [data]
    timesteps = data[0][time_dim].values
    
    fig = go.Figure()
    
    trace_timesteps = timesteps
    for j in range(len(trace_timesteps)):
        for i in range(len(data)):
            quantile_values = data[i].squeeze().values.T
            fig.add_trace(
                go.Violin(
                    y=quantile_values[j],
                    # x=[trace_timesteps[j] for _ in quantile_values[j]],
                    x=[j]*len(quantile_values[j]),
                    fillcolor='#EE3233' if i else '#A3D6F5',
                    line_color='#a50d0d' if i else '#47aceb',
                    quartilemethod="exclusive",
                    side='positive' if i else 'negative',
                    # line={"color": "black", "width": 1},
                    # whiskerwidth=0,
                    # width=0.4*60*60*1000,
                    # hoverinfo='skip',
                )
            )
        
        # for j in range(extra_boxes):
        #     fig.add_trace(
        #         go.Box(
        #             lowerfence=quantile_values[0],
        #             upperfence=quantile_values[-1],
        #             showwhiskers=False,
        #             q1=quantile_values[1+(j+1)],
        #             q3=quantile_values[-2-(j+1)],
        #             median=quantile_values[len(quantiles)//2],
        #             x=[Timestamp(t).to_pydatetime(t) for t in trace_timesteps],
        #             fillcolor=colors[i],
        #             line={"color": "black", "width": 1},
        #             whiskerwidth=0,
        #             width=0.8*60*60*1000,
        #             hoverinfo='skip',
        #         )
        #     )

        # for y, p in zip(quantile_values, quantiles):
        #     fig.add_trace(
        #         go.Scatter(
        #             y=y,
        #             x=[Timestamp(t).to_pydatetime(t) for t in trace_timesteps],
        #             mode='markers',
        #             marker={'size': 0.00001, 'color': 'rgb(247, 79, 79)'},
        #             hovertemplate=f"P<sub>{p*100:g}%</sub>: %{{y:.1f}}°C<extra></extra>",
        #         )
        #     )

    fig.update_traces(meanline_visible=True)

    fig.update_layout(
        showlegend=False,
        # boxmode="overlay",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x",
        yaxis=dict(
            # fixedrange=True,
            # title="temperature (°C)",
            showgrid=True,
            gridcolor="#e6e6e6",
            
        ),
        xaxis=dict(
            # dtick=6*60*60*1000,
            # ticklabelmode="period",
            # tickformat="%H %a %-d",
            # minor=dict(
            #     dtick=6*60*60*1000,
            #     tick0="2017-01-01T00",
            #     ticklen=4,
            # ),
            showgrid=True,
            gridcolor="#e6e6e6",
            # range=['2016-12-31T21', '2017-01-14T03'],
        ),
        height=400,
    )

    return fig
    

def get_time_dim(data):
    dims = dict(data.squeeze().dims)
    for dim in TIME_DIMS:
        if dim in dims:
            return dim
    


def guess_dim(data):
    dims = list(data.squeeze().dims)
    for dim in TIME_DIMS:
        if dim in dims:
            dims.pop(dims.index(dim))
            break
    
    if len(dims) == 1:
        return list(dims)[0]
    
    else:
        raise ValueError("could not identify single dim over which to aggregate")