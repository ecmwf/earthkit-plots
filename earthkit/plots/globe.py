# Copyright 2023, European Centre for Medium Range Weather Forecasts.
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

import earthkit.maps

import warnings
import io
import matplotlib
from matplotlib.gridspec import GridSpec
import plotly.graph_objects as go
import numpy as np
from numpy import pi, sin, cos
from PIL import Image


warnings.warn("earthkit.plots.globe is an EXPERIMENTAL feature")


RADIUS = 1


def style_to_grayscale(style):
    colors = [(0, 0, 0)]
    
    if style.gradients:
        gradient_range = sum(style.gradients)
        for gradient in style.gradients:
            increment = colors[-1][0] + gradient/gradient_range
            colors.append((increment, increment, increment))
    else:
        level_range = abs(style._levels[-1]-style._levels[0])
        for i in range(len(style._levels)-1):
            increment = (style._levels[i+1]-style._levels[i])/level_range
            colors.append[(increment, increment, increment)]

    new_style = style.__class__(
        colors=colors,
        levels=style._levels,
        gradients=style.gradients,
        units=style._units,
        **style.kwargs,
    )
    
    return new_style


def matplotlib_to_plotly(cmap, pl_entries=255):
    h = 1.0/(pl_entries-1)
    pl_colorscale = []

    for k in range(pl_entries):
        C = [np.uint8(item) for item in np.array(cmap(k*h)[:3])*255]
        pl_colorscale.append([k*h, 'rgb'+str((C[0], C[1], C[2]))])

    return pl_colorscale


def globe(data, *args, style, **kwargs):
    backend = matplotlib.rcParams['backend']
    matplotlib.use("Agg")
    
    cmap = style.to_kwargs(data)["cmap"]
    colorscale = matplotlib_to_plotly(cmap)
    
    style = style_to_grayscale(style)
    
    gs = GridSpec(1, 1, left=0, right=1, bottom=0, top=1)
    earthkit.maps.schema.figsize = (6, 3)
    chart = earthkit.maps.Superplot.from_gridspec(gs)
    chart.add_subplot(frameon=False)
    chart.plot(data, style=style)
    

    buf = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        chart.save(buf, format="png")
    matplotlib.use(backend)
    buf.seek(0)
    
    texture = np.asarray(Image.open(buf)).T[0]
    shape = texture.shape
    
    texture = np.array(normalize(texture, (0, 255), (style._levels[0], style._levels[-1]))).reshape(shape)
    
    lons = np.linspace(-180, 180-(360/shape[0]), shape[0])
    lats = np.linspace(-90, 90-(180/shape[1]), shape[1])
    
    lons, lats = np.meshgrid(lons, lats)

    # text=[['lon: '+'{:.2f}'.format(lons[i,j])+'<br>lat: '+'{:.2f}'.format(lats[i, j])
    #      for j in range(shape[0])] for i in range(shape[1])]

    x,y,z = sphere(RADIUS ,texture, lats, lons)
    # x, y, z=mapping_map_to_sphere(x, y)
    surf = go.Surface(x=x, y=y, z=z,
                    surfacecolor=texture,
                    colorscale=colorscale,
                    # text=text,
                    # hoverinfo='text'
                    )    

    layout = go.Layout(
        scene=dict(
            aspectratio=dict(x=1, y=1, z=1),
            xaxis = dict(visible=False),
            yaxis = dict(visible=False),
            zaxis =dict(visible=False),
            camera=dict(eye=dict(x=1.15, 
                                        y=1.15, 
                                        z=1.15)
                                        )
        )
    )

    fig = go.Figure(data=[surf], layout=layout)
    buf.close()

    return fig


def sphere(size, texture, lats=None, lons=None): 
    N_lat = int(texture.shape[0])
    N_lon = int(texture.shape[1])
    theta = np.linspace(0,2*np.pi,N_lat)
    phi = np.linspace(0,np.pi,N_lon)
    
    # Set up coordinates for points on the sphere
    x0 = size * np.outer(np.cos(theta),np.sin(phi))
    y0 = size * np.outer(np.sin(theta),np.sin(phi))
    z0 = size * np.outer(np.ones(N_lat),np.cos(phi))
    
    # if lats is not None:
    #     lon=np.array(lons, dtype=np.float64)
    #     lat=np.array(lats, dtype=np.float64)
    #     lon=degree2radians(lon)
    #     lat=degree2radians(lat)
    #     x0=RADIUS*cos(lon)*cos(lat)
    #     y0=RADIUS*sin(lon)*cos(lat)
    #     z0=RADIUS*sin(lat)
        
    
    # Set up trace
    return x0,y0,z0


def normalize(values, actual_bounds, desired_bounds):
    return [
        desired_bounds[0] + (x - actual_bounds[0]) * (desired_bounds[1] - desired_bounds[0]) / (actual_bounds[1] - actual_bounds[0]) for y in values for x in y
    ]


def degree2radians(degree):
    #convert degrees to radians
    return degree*pi/180


def mapping_map_to_sphere(lon, lat, radius=RADIUS):
    #this function maps the points of coords (lon, lat) to points onto the  sphere of radius radius
    
    lon=np.array(lon, dtype=np.float64)
    lat=np.array(lat, dtype=np.float64)
    lon=degree2radians(lon)
    lat=degree2radians(lat)
    xs=radius*cos(lon)*cos(lat)
    ys=radius*sin(lon)*cos(lat)
    zs=radius*sin(lat)
    return xs, ys, zs