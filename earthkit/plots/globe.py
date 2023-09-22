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

import plotly.graph_objects as go
import numpy as np
from numpy import pi, sin, cos


def globe(data, *args, **kwargs):
    latlon = data.to_latlon()
    lat = latlon["lat"]
    lon = latlon["lon"]
    values = data.to_numpy()
    
    # # Shift 'lon' from [0,360] to [-180,180]
    # tmp_lon = np.array(
    #     [lon[n]-360 if l>=180 else lon[n] for n,l in enumerate(lon)])
    
    # i_east, = np.where(tmp_lon>=0)  # indices of east lon
    # i_west, = np.where(tmp_lon<0)   # indices of west lon
    # lon = np.hstack((tmp_lon[i_west], tmp_lon[i_east]))  # stack the 2 halves

    # # Correspondingly, shift the values array
    # values_ground = np.array(values)
    # values = np.hstack((values_ground[:,i_west], values_ground[:,i_east]))
    
    colorscale=[
        [0.0, '#313695'],
        [0.07692307692307693, '#3a67af'],
        [0.15384615384615385, '#5994c5'],
        [0.23076923076923078, '#84bbd8'],
        [0.3076923076923077, '#afdbea'],
        [0.38461538461538464, '#d8eff5'],
        [0.46153846153846156, '#d6ffe1'],
        [0.5384615384615384, '#fef4ac'],
        [0.6153846153846154, '#fed987'],
        [0.6923076923076923, '#fdb264'],
        [0.7692307692307693, '#f78249'],
        [0.8461538461538461, '#e75435'],
        [0.9230769230769231, '#cc2727'],
        [1.0, '#a50026'],
    ]

    clons=np.array(lon, dtype=np.float64)
    clats=np.array(lat, dtype=np.float64)
    clons, clats=np.meshgrid(clons, clats)
    
    XS, YS, ZS=mapping_map_to_sphere(clons, clats)

    nrows, ncolumns=clons.shape
    OLR=np.zeros(clons.shape, dtype=np.float64)
    OLR[:, :ncolumns-1]=np.copy(np.array(values,  dtype=np.float64))
    OLR[:, ncolumns-1]=np.copy(values[:, 0])


    sphere=dict(type='surface',
            x=XS, 
            y=YS, 
            z=ZS,
            colorscale=colorscale,
            surfacecolor=OLR,
            cmin=-20, 
            cmax=20,
            colorbar=dict(thickness=20, len=0.75, ticklen=4, title= 'W/m²'),
        )

    noaxis=dict(showbackground=False,
            showgrid=False,
            showline=False,
            showticklabels=False,
            ticks='',
            title='',
            zeroline=False)

    layout3d=dict(title='Outgoing Longwave Radiation Anomalies<br>Dec 2017-Jan 2018',
              font=dict(family='Balto', size=14),
              width=800, 
              height=800,
              scene=dict(xaxis=noaxis, 
                         yaxis=noaxis, 
                         zaxis=noaxis,
                         aspectratio=dict(x=1,
                                          y=1,
                                          z=1),
                         camera=dict(eye=dict(x=1.15, 
                                     y=1.15, 
                                     z=1.15)
                                    )
            ),
           )

    fig=go.Figure(data=[sphere], layout=layout3d)
    return fig




def degree2radians(degree):
    #convert degrees to radians
    return degree*pi/180


def mapping_map_to_sphere(lon, lat, radius=1):
    #this function maps the points of coords (lon, lat) to points onto the  sphere of radius radius
    
    lon=np.array(lon, dtype=np.float64)
    lat=np.array(lat, dtype=np.float64)
    lon=degree2radians(lon)
    lat=degree2radians(lat)
    xs=radius*cos(lon)*cos(lat)
    ys=radius*sin(lon)*cos(lat)
    zs=radius*sin(lat)
    return xs, ys, zs


def polygons_to_traces(poly_paths, N_poly):
    ''' 
    pos arg 1. (poly_paths): paths to polygons
    pos arg 2. (N_poly): number of polygon to convert
    '''
    # init. plotting list
    lons=[]
    lats=[]

    for i_poly in range(N_poly):
        poly_path = poly_paths[i_poly]
        
        # get the Basemap coordinates of each segment
        coords_cc = np.array(
            [(vertex[0],vertex[1]) 
             for (vertex,code) in poly_path.iter_segments(simplify=False)]
        )
        
        # convert coordinates to lon/lat by 'inverting' the Basemap projection
        lon_cc, lat_cc = m(coords_cc[:,0],coords_cc[:,1], inverse=True)
    
        
        lats.extend(lat_cc.tolist()+[None]) 
        lons.extend(lon_cc.tolist()+[None])
        
       
    return lons, lats