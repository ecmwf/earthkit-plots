import earthkit as ek

data = ek.data.from_source("sample", "era5-monthly-mean-2t-199312.grib")

chart = ek.plots.Map()
chart.grid_points(data)
