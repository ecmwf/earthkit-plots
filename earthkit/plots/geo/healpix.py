
from scipy.interpolate import NearestNDInterpolator

import cartopy.crs as ccrs
import healpy as hp
import numpy as np

def nnshow(var, nx=1000, ny=1000, ax=None, nest=False, style=None, **kwargs):
    """
    var: variable on healpix coordinates (array-like)
    nx: image resolution in x-direction
    ny: image resolution in y-direction
    ax: axis to plot on
    kwargs: additional arguments to imshow
    """
    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    # NOTE: we want the center coordinate of each pixel, thus we have to
    # compute the linspace over halve a pixel size less than the plot's limits
    dx = (xlims[1] - xlims[0]) / nx
    dy = (ylims[1] - ylims[0]) / ny
    xvals = np.linspace(xlims[0] + dx / 2, xlims[1] - dx / 2, nx)
    yvals = np.linspace(ylims[0] + dy / 2, ylims[1] - dy / 2, ny)
    xvals2, yvals2 = np.meshgrid(xvals, yvals)
    latlon = ccrs.PlateCarree().transform_points(
        ax.projection, xvals2, yvals2, np.zeros_like(xvals2)
    )
    valid = np.all(np.isfinite(latlon), axis=-1)
    points = latlon[valid].T
    pix = hp.ang2pix(
        hp.npix2nside(len(var)), theta=points[0], phi=points[1], nest=nest, lonlat=True
    )
    res = np.full(latlon.shape[:-1], np.nan, dtype=var.dtype)
    res[valid] = var[pix]
    
    if style is not None:
        kwargs = {**kwargs, **style.to_pcolormesh_kwargs(res)}

    return ax.imshow(res, extent=xlims + ylims, origin="lower", **kwargs)


def testshow(var, x, y, nx=1000, ny=1000, ax=None, **kwargs):
    """"""
    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    # NOTE: we want the center coordinate of each pixel, thus we have to
    # compute the linspace over halve a pixel size less than the plot's limits
    dx = (xlims[1] - xlims[0]) / nx
    dy = (ylims[1] - ylims[0]) / ny
    xvals = np.linspace(xlims[0] + dx / 2, xlims[1] - dx / 2, nx)
    yvals = np.linspace(ylims[0] + dy / 2, ylims[1] - dy / 2, ny)
    xvals2, yvals2 = np.meshgrid(xvals, yvals)
    
    latlon = ccrs.PlateCarree().transform_points(
        ax.projection, xvals2, yvals2, np.zeros_like(xvals2)
    )
    
    lon = latlon[:,:,0]
    lat = latlon[:,:,1]
    
    # x, y = np.meshgrid(x, y)
    
    interp = NearestNDInterpolator(list(zip(x[:,:-1].flatten(), y[:,:-1].flatten())), var.flatten())
    
    zvals = interp(lon, lat)

    return ax.imshow(zvals, extent=xlims + ylims, origin="lower", **kwargs)
    