import warnings

TIME_DIMS = ["time", "t", "month"]


def guess_time_dim(data):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dims = dict(data.squeeze().dims)
        for dim in TIME_DIMS:
            if dim in dims:
                return dim


def guess_non_time_dim(data):
    dims = list(data.squeeze().dims)
    for dim in TIME_DIMS:
        if dim in dims:
            dims.pop(dims.index(dim))
            break

    if len(dims) == 1:
        return list(dims)[0]

    else:
        raise ValueError("could not identify single dim over which to aggregate")
