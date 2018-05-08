from __future__ import absolute_import, division, print_function

import numpy as np
import pytest

import xarray as xr
from xarray.tests import assert_allclose, requires_scipy
from . import has_dask, has_scipy

try:
    import scipy
except ImportError:
    pass


def get_example_data(case):
    x = np.linspace(0, 1, 100)
    y = np.linspace(0, 0.1, 30)
    data = xr.DataArray(
        np.sin(x[:, np.newaxis]) * np.cos(y), dims=['x', 'y'],
        coords={'x': x, 'y': y, 'x2': ('x', x**2)})

    if case == 0:
        return data
    elif case == 1:
        return data.chunk({'y': 3})
    elif case == 2:
        return data.chunk({'x': 25, 'y': 3})
    elif case == 3:
        x = np.linspace(0, 1, 100)
        y = np.linspace(0, 0.1, 30)
        z = np.linspace(0.1, 0.2, 10)
        return xr.DataArray(
            np.sin(x[:, np.newaxis, np.newaxis]) * np.cos(
                y[:, np.newaxis]) * z,
            dims=['x', 'y', 'z'],
            coords={'x': x, 'y': y, 'x2': ('x', x**2), 'z': z})
    elif case == 4:
        return get_example_data(3).chunk({'z': 5})


@pytest.mark.parametrize('method', ['linear', 'cubic'])
@pytest.mark.parametrize('dim', ['x', 'y'])
@pytest.mark.parametrize('case', [0, 1])
def test_interpolate_1d(method, dim, case):
    if not has_scipy:
        pytest.skip('scipy is not installed.')

    if not has_dask and case in [1]:
        pytest.skip('dask is not installed in the environment.')

    da = get_example_data(case)
    xdest = np.linspace(0.0, 0.9, 80)

    if dim == 'y' and case == 1:
        with pytest.raises(ValueError):
            actual = da.interp(method=method, **{dim: xdest})
        pytest.skip('interpolation along chunked dimension is '
                    'not yet supported')

    actual = da.interp(method=method, **{dim: xdest})

    # scipy interpolation for the reference
    def func(obj, new_x):
        return scipy.interpolate.interp1d(
            da[dim], obj.data, axis=obj.get_axis_num(dim), bounds_error=False,
            fill_value=np.nan, kind=method)(new_x)

    if dim == 'x':
        coords = {'x': xdest, 'y': da['y'], 'x2': ('x', func(da['x2'], xdest))}
    else:  # y
        coords = {'x': da['x'], 'y': xdest, 'x2': da['x2']}

    expected = xr.DataArray(func(da, xdest), dims=['x', 'y'], coords=coords)
    assert_allclose(actual, expected)


@pytest.mark.parametrize('method', ['cubic', 'zero'])
def test_interpolate_1d_methods(method):
    if not has_scipy:
        pytest.skip('scipy is not installed.')

    da = get_example_data(0)
    dim = 'x'
    xdest = np.linspace(0.0, 0.9, 80)

    actual = da.interp(method=method, **{dim: xdest})

    # scipy interpolation for the reference
    def func(obj, new_x):
        return scipy.interpolate.interp1d(
            da[dim], obj.data, axis=obj.get_axis_num(dim), bounds_error=False,
            fill_value=np.nan, kind=method)(new_x)

    coords = {'x': xdest, 'y': da['y'], 'x2': ('x', func(da['x2'], xdest))}
    expected = xr.DataArray(func(da, xdest), dims=['x', 'y'], coords=coords)
    assert_allclose(actual, expected)


@pytest.mark.parametrize('use_dask', [False, True])
def test_interpolate_vectorize(use_dask):
    if not has_scipy:
        pytest.skip('scipy is not installed.')

    if not has_dask and use_dask:
        pytest.skip('dask is not installed in the environment.')

    # scipy interpolation for the reference
    def func(obj, dim, new_x):
        shape = [s for i, s in enumerate(obj.shape)
                 if i != obj.get_axis_num(dim)]
        for s in new_x.shape[::-1]:
            shape.insert(obj.get_axis_num(dim), s)

        return scipy.interpolate.interp1d(
            da[dim], obj.data, axis=obj.get_axis_num(dim),
            bounds_error=False, fill_value=np.nan)(new_x).reshape(shape)

    da = get_example_data(0)
    if use_dask:
        da = da.chunk({'y': 5})

    # xdest is 1d but has different dimension
    xdest = xr.DataArray(np.linspace(0.1, 0.9, 30), dims='z',
                         coords={'z': np.random.randn(30),
                                 'z2': ('z', np.random.randn(30))})

    actual = da.interp(x=xdest, method='linear')

    expected = xr.DataArray(func(da, 'x', xdest), dims=['z', 'y'],
                            coords={'z': xdest['z'], 'z2': xdest['z2'],
                                    'y': da['y'],
                                    'x': ('z', xdest.values),
                                    'x2': ('z', func(da['x2'], 'x', xdest))})
    assert_allclose(actual, expected.transpose('y', 'z'))

    # xdest is 2d
    xdest = xr.DataArray(np.linspace(0.1, 0.9, 30).reshape(6, 5),
                         dims=['z', 'w'],
                         coords={'z': np.random.randn(6),
                                 'w': np.random.randn(5),
                                 'z2': ('z', np.random.randn(6))})

    actual = da.interp(x=xdest, method='linear')

    expected = xr.DataArray(
        func(da, 'x', xdest),
        dims=['z', 'w', 'y'],
        coords={'z': xdest['z'], 'w': xdest['w'], 'z2': xdest['z2'],
                'y': da['y'], 'x': (('z', 'w'), xdest),
                'x2': (('z', 'w'), func(da['x2'], 'x', xdest))})
    assert_allclose(actual, expected.transpose('y', 'z', 'w'))


@pytest.mark.parametrize('case', [3, 4])
def test_interpolate_nd(case):
    if not has_scipy:
        pytest.skip('scipy is not installed.')

    if not has_dask and case == 4:
        pytest.skip('dask is not installed in the environment.')

    da = get_example_data(case)

    # grid -> grid
    xdest = np.linspace(0.1, 1.0, 11)
    ydest = np.linspace(0.0, 0.2, 10)
    actual = da.interp(x=xdest, y=ydest, method='linear')

    # linear interpolation is separateable
    expected = da.interp(x=xdest, method='linear')
    expected = expected.interp(y=ydest, method='linear')
    assert_allclose(actual, expected.transpose('x', 'y', 'z'))

    # grid -> 1d-sample
    xdest = xr.DataArray(np.linspace(0.1, 1.0, 11), dims='y')
    ydest = xr.DataArray(np.linspace(0.0, 0.2, 11), dims='y')
    actual = da.interp(x=xdest, y=ydest, method='linear')

    # linear interpolation is separateable
    expected_data = scipy.interpolate.RegularGridInterpolator(
        (da['x'], da['y']), da.transpose('x', 'y', 'z').values,
        method='linear', bounds_error=False,
        fill_value=np.nan)(np.stack([xdest, ydest], axis=-1))
    expected = xr.DataArray(
        expected_data, dims=['y', 'z'],
        coords={'z': da['z'], 'y': ydest, 'x': ('y', xdest.values),
                'x2': da['x2'].interp(x=xdest)})
    assert_allclose(actual, expected.transpose('z', 'y'))


@pytest.mark.parametrize('method', ['linear'])
@pytest.mark.parametrize('case', [0, 1])
def test_interpolate_scalar(method, case):
    if not has_scipy:
        pytest.skip('scipy is not installed.')

    if not has_dask and case in [1]:
        pytest.skip('dask is not installed in the environment.')

    da = get_example_data(case)
    xdest = 0.4

    actual = da.interp(x=xdest, method=method)

    # scipy interpolation for the reference
    def func(obj, new_x):
        return scipy.interpolate.interp1d(
            da['x'], obj.data, axis=obj.get_axis_num('x'), bounds_error=False,
            fill_value=np.nan)(new_x)

    coords = {'x': xdest, 'y': da['y'], 'x2': func(da['x2'], xdest)}
    expected = xr.DataArray(func(da, xdest), dims=['y'], coords=coords)
    assert_allclose(actual, expected)


@pytest.mark.parametrize('method', ['linear'])
@pytest.mark.parametrize('case', [3, 4])
def test_interpolate_nd_scalar(method, case):
    if not has_scipy:
        pytest.skip('scipy is not installed.')

    if not has_dask and case in [4]:
        pytest.skip('dask is not installed in the environment.')

    da = get_example_data(case)
    xdest = 0.4
    ydest = 0.05

    actual = da.interp(x=xdest, y=ydest, method=method)
    # scipy interpolation for the reference
    expected_data = scipy.interpolate.RegularGridInterpolator(
        (da['x'], da['y']), da.transpose('x', 'y', 'z').values,
        method='linear', bounds_error=False,
        fill_value=np.nan)(np.stack([xdest, ydest], axis=-1))

    coords = {'x': xdest, 'y': ydest, 'x2': da['x2'].interp(x=xdest),
              'z': da['z']}
    expected = xr.DataArray(expected_data[0], dims=['z'], coords=coords)
    assert_allclose(actual, expected)


@requires_scipy
def test_errors():
    da = xr.DataArray([0, 1, np.nan, 2], dims='x', coords={'x': range(4)})
    actual = da.interp(x=[0.5, 1.5])
    # not all values are nan
    assert actual.count() > 0

    da = xr.DataArray([0, 1, np.nan, 2], dims='x', coords={'x': range(4)})
    for method in ['akima', 'spline']:
        with pytest.raises(ValueError):
            actual = da.interp(x=[0.5, 1.5], method=method)
