import hypothesis.extra.numpy as npst
import hypothesis.strategies as st

import xarray as xr


def shapes(ndim=None):
    return npst.array_shapes()


dtypes = (
    npst.integer_dtypes()
    | npst.unsigned_integer_dtypes()
    | npst.floating_dtypes()
    | npst.complex_number_dtypes()
)


def numpy_array(shape=None):
    if shape is None:
        shape = npst.array_shapes()
    return npst.arrays(dtype=dtypes, shape=shape)


def create_dimension_names(ndim):
    return [f"dim_{n}" for n in range(ndim)]


@st.composite
def variable(draw, create_data, dims=None, shape=None, sizes=None):
    if sizes is not None:
        dims, sizes = zip(*draw(sizes).items())
    else:
        if shape is None:
            shape = draw(shapes())
        if dims is None:
            dims = create_dimension_names(len(shape))

    data = create_data(shape)

    return xr.Variable(dims, draw(data))


def valid_axis(ndim):
    return st.none() | st.integers(-ndim, ndim - 1)


def valid_axes(ndim):
    return valid_axis(ndim) | npst.valid_tuple_axes(ndim)
