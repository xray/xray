"""Testing functions exposed to the user API"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from xarray.core import ops


def decode_string_data(data):
    if data.dtype.kind == 'S':
        return np.core.defchararray.decode(data, 'utf-8', 'replace')
    return data


def data_allclose_or_equiv(arr1, arr2, rtol=1e-05, atol=1e-08):
    if any(arr.dtype.kind == 'S' for arr in [arr1, arr2]):
        arr1 = decode_string_data(arr1)
        arr2 = decode_string_data(arr2)
    exact_dtypes = ['M', 'm', 'O', 'U']
    if any(arr.dtype.kind in exact_dtypes for arr in [arr1, arr2]):
        return ops.array_equiv(arr1, arr2)
    else:
        return ops.allclose_or_equiv(arr1, arr2, rtol=rtol, atol=atol)


def assert_dataset_allclose(d1, d2, rtol=1e-05, atol=1e-08):
    """Similar to numpy.testing.assert_allclose, but for Datasets."""
    assert sorted(d1, key=str) == sorted(d2, key=str)
    assert sorted(d1.coords, key=str) == sorted(d2.coords, key=str)
    for k in d1:
        v1 = d1.variables[k]
        v2 = d2.variables[k]
        assert v1.dims == v2.dims
        allclose = data_allclose_or_equiv(
            v1.values, v2.values, rtol=rtol, atol=atol)
        assert allclose, (k, v1.values, v2.values)


def assert_equal(a, b):
    """Similar to numpy.testing.assert_array_equal, but for xarray objects."""
    import xarray as xr
    ___tracebackhide__ = True  # noqa: F841
    assert type(a) == type(b)
    if isinstance(a, (xr.Variable, xr.DataArray, xr.Dataset)):
        assert a.equals(b), '{}\n{}'.format(a, b)
    else:
        raise TypeError('{} not supported by assertion comparison'
                        .format(type(a)))


def assert_identical(a, b):
    """Like assert_equal, but also checks all attributes."""

    import xarray as xr
    ___tracebackhide__ = True  # noqa: F841
    assert type(a) == type(b)
    if isinstance(a, xr.DataArray):
        assert a.name == b.name
        assert_identical(a._to_temp_dataset(), b._to_temp_dataset())
    elif isinstance(a, (xr.Dataset, xr.Variable)):
        assert a.identical(b), '{}\n{}'.format(a, b)
    else:
        raise TypeError('{} not supported by assertion comparison'
                        .format(type(a)))


def assert_allclose(a, b, rtol=1e-05, atol=1e-08):
    """Similar to numpy.testing.assert_allclose, but for xarray objects."""
    import xarray as xr
    ___tracebackhide__ = True  # noqa: F841
    assert type(a) == type(b)
    if isinstance(a, xr.Variable):
        assert a.dims == b.dims
        allclose = data_allclose_or_equiv(
            a.values, b.values, rtol=rtol, atol=atol)
        assert allclose, '{}\n{}'.format(a.values, b.values)
    elif isinstance(a, xr.DataArray):
        assert_allclose(a.variable, b.variable)
        for v in a.coords.variables:
            # can't recurse with this function as coord is sometimes a
            # DataArray, so call into data_allclose_or_equiv directly
            allclose = data_allclose_or_equiv(
                a.coords[v].values, b.coords[v].values, rtol=rtol, atol=atol)
            assert allclose, '{}\n{}'.format(a.coords[v].values,
                                             b.coords[v].values)
    elif isinstance(a, xr.Dataset):
        assert sorted(a, key=str) == sorted(b, key=str)
        for k in list(a.variables) + list(a.coords):
            assert_allclose(a[k], b[k], rtol=rtol, atol=atol)

    else:
        raise TypeError('{} not supported by assertion comparison'
                        .format(type(a)))
