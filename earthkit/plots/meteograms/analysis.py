
import xarray as xr


def meteogramify(data, time_frequency=None, how="mean"):    
    if time_frequency is not None:
        data = getattr(data.resample(t=time_frequency), how)()

    return data