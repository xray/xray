from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import pytest
import numpy as np
from numpy import array, nan
from distutils.version import LooseVersion
from . import assert_array_equal
from xarray.core.duck_array_ops import (
    first, last, count, mean, array_notnull_equiv, where, stack, concatenate
)
from xarray import DataArray
from xarray.testing import assert_allclose
from xarray import concat

from . import TestCase, raises_regex, has_dask


class TestOps(TestCase):
    def setUp(self):
        self.x = array([[[nan,  nan,   2.,  nan],
                         [nan,   5.,   6.,  nan],
                         [8.,   9.,  10.,  nan]],

                        [[nan,  13.,  14.,  15.],
                         [nan,  17.,  18.,  nan],
                         [nan,  21.,  nan,  nan]]])

    def test_first(self):
        expected_results = [array([[nan, 13, 2, 15],
                                   [nan, 5, 6, nan],
                                   [8, 9, 10, nan]]),
                            array([[8, 5, 2, nan],
                                   [nan, 13, 14, 15]]),
                            array([[2, 5, 8],
                                   [13, 17, 21]])]
        for axis, expected in zip([0, 1, 2, -3, -2, -1],
                                  2 * expected_results):
            actual = first(self.x, axis)
            assert_array_equal(expected, actual)

        expected = self.x[0]
        actual = first(self.x, axis=0, skipna=False)
        assert_array_equal(expected, actual)

        expected = self.x[..., 0]
        actual = first(self.x, axis=-1, skipna=False)
        assert_array_equal(expected, actual)

        with raises_regex(IndexError, 'out of bounds'):
            first(self.x, 3)

    def test_last(self):
        expected_results = [array([[nan, 13, 14, 15],
                                   [nan, 17, 18, nan],
                                   [8, 21, 10, nan]]),
                            array([[8, 9, 10, nan],
                                   [nan, 21, 18, 15]]),
                            array([[2, 6, 10],
                                   [15, 18, 21]])]
        for axis, expected in zip([0, 1, 2, -3, -2, -1],
                                  2 * expected_results):
            actual = last(self.x, axis)
            assert_array_equal(expected, actual)

        expected = self.x[-1]
        actual = last(self.x, axis=0, skipna=False)
        assert_array_equal(expected, actual)

        expected = self.x[..., -1]
        actual = last(self.x, axis=-1, skipna=False)
        assert_array_equal(expected, actual)

        with raises_regex(IndexError, 'out of bounds'):
            last(self.x, 3)

    def test_count(self):
        assert 12 == count(self.x)

        expected = array([[1, 2, 3], [3, 2, 1]])
        assert_array_equal(expected, count(self.x, axis=-1))

    def test_where_type_promotion(self):
        result = where([True, False], [1, 2], ['a', 'b'])
        assert_array_equal(result, np.array([1, 'b'], dtype=object))

        result = where([True, False], np.array([1, 2], np.float32), np.nan)
        assert result.dtype == np.float32
        assert_array_equal(result, np.array([1, np.nan], dtype=np.float32))

    def test_stack_type_promotion(self):
        result = stack([1, 'b'])
        assert_array_equal(result, np.array([1, 'b'], dtype=object))

    def test_concatenate_type_promotion(self):
        result = concatenate([[1], ['b']])
        assert_array_equal(result, np.array([1, 'b'], dtype=object))

    def test_all_nan_arrays(self):
        assert np.isnan(mean([np.nan, np.nan]))


class TestArrayNotNullEquiv():
    @pytest.mark.parametrize("arr1, arr2", [
        (np.array([1, 2, 3]), np.array([1, 2, 3])),
        (np.array([1, 2, np.nan]), np.array([1, np.nan, 3])),
        (np.array([np.nan, 2, np.nan]), np.array([1, np.nan, np.nan])),
    ])
    def test_equal(self, arr1, arr2):
        assert array_notnull_equiv(arr1, arr2)

    def test_some_not_equal(self):
        a = np.array([1, 2, 4])
        b = np.array([1, np.nan, 3])
        assert not array_notnull_equiv(a, b)

    def test_wrong_shape(self):
        a = np.array([[1, np.nan, np.nan, 4]])
        b = np.array([[1, 2], [np.nan, 4]])
        assert not array_notnull_equiv(a, b)

    @pytest.mark.parametrize("val1, val2, val3, null", [
        (1, 2, 3, None),
        (1., 2., 3., np.nan),
        (1., 2., 3., None),
        ('foo', 'bar', 'baz', None),
    ])
    def test_types(self, val1, val2, val3, null):
        arr1 = np.array([val1, null, val3, null])
        arr2 = np.array([val1, val2, null, null])
        assert array_notnull_equiv(arr1, arr2)


def construct_dataarray(dim_num, dtype, contains_nan, dask):
    # dimnum <= 3
    rng = np.random.RandomState(0)
    shapes = [16, 8, 4][:dim_num]
    dims = ('x', 'y', 'z')[:dim_num]

    if np.issubdtype(dtype, np.floating):
        array = rng.randn(*shapes).astype(dtype)
    elif np.issubdtype(dtype, np.integer):
        array = rng.randint(0, 10, size=shapes).astype(dtype)
    elif np.issubdtype(dtype, np.bool_):
        array = rng.randint(0, 1, size=shapes).astype(dtype)
    elif dtype == str:
        array = rng.choice(['a', 'b', 'c', 'd'], size=shapes)
    else:
        raise ValueError
    da = DataArray(array, dims=dims, coords={'x': np.arange(16)}, name='da')

    if contains_nan:
        da = da.reindex(x=np.arange(20))
    if dask and has_dask:
        chunks = {d: 4 for d in dims}
        da = da.chunk(chunks)

    return da


def from_series_or_scalar(se):
    try:
        return DataArray.from_series(se)
    except AttributeError:  # scalar case
        return DataArray(se)


def series_reduce(da, func, dim, **kwargs):
    """ convert DataArray to pd.Series, apply pd.func, then convert back to
    a DataArray. Multiple dims cannot be specified."""
    if dim is None or da.ndim == 1:
        se = da.to_series()
        return from_series_or_scalar(getattr(se, func)(**kwargs))
    else:
        da1 = []
        dims = list(da.dims)
        dims.remove(dim)
        d = dims[0]
        for i in range(len(da[d])):
            da1.append(series_reduce(da.isel(**{d: i}), func, dim, **kwargs))

        if d in da.coords:
            return concat(da1, dim=da[d])
        return concat(da1, dim=d)


@pytest.mark.parametrize('dim_num', [1, 2])
@pytest.mark.parametrize('dtype', [float, int, np.float32, np.bool_])
@pytest.mark.parametrize('dask', [False, True])
@pytest.mark.parametrize('func', ['sum', 'min', 'max', 'mean', 'var'])
@pytest.mark.parametrize('skipna', [False, True])
@pytest.mark.parametrize('aggdim', [None, 'x'])
def test_reduce(dim_num, dtype, dask, func, skipna, aggdim):

    if aggdim == 'y' and dim_num < 2:
        return

    if dtype == np.bool_ and func == 'mean':
        return  # numpy does not support this

    if dask and not has_dask:
        return

    rtol = 1e-04 if dtype == np.float32 else 1e-05

    da = construct_dataarray(dim_num, dtype, contains_nan=True, dask=dask)
    axis = None if aggdim is None else da.get_axis_num(aggdim)

    if dask and not skipna and func in ['var', 'std'] and dtype == np.bool_:
        # TODO this might be dask's bug
        return

    if (LooseVersion(np.__version__) >= LooseVersion('1.13.0') and
            da.dtype.kind == 'O' and skipna):
        # Numpy < 1.13 does not handle object-type array.
        try:
            if skipna:
                expected = getattr(np, 'nan{}'.format(func))(da.values,
                                                             axis=axis)
            else:
                expected = getattr(np, func)(da.values, axis=axis)

            actual = getattr(da, func)(skipna=skipna, dim=aggdim)
            assert np.allclose(actual.values, np.array(expected), rtol=1.0e-4,
                               equal_nan=True)
        except (TypeError, AttributeError, ZeroDivisionError):
            # TODO currently, numpy does not support some methods such as
            # nanmean for object dtype
            pass

    # make sure the compatiblility with pandas' results.
    actual = getattr(da, func)(skipna=skipna, dim=aggdim)
    if func == 'var':
        expected = series_reduce(da, func, skipna=skipna, dim=aggdim, ddof=0)
        assert_allclose(actual, expected, rtol=rtol)
        # also check ddof!=0 case
        actual = getattr(da, func)(skipna=skipna, dim=aggdim, ddof=5)
        expected = series_reduce(da, func, skipna=skipna, dim=aggdim, ddof=5)
        assert_allclose(actual, expected, rtol=rtol)
    else:
        expected = series_reduce(da, func, skipna=skipna, dim=aggdim)
        assert_allclose(actual, expected, rtol=rtol)

    # make sure the dtype argument
    if func not in ['max', 'min']:
        actual = getattr(da, func)(skipna=skipna, dim=aggdim, dtype=float)
        assert actual.dtype == float

    # without nan
    da = construct_dataarray(dim_num, dtype, contains_nan=False, dask=dask)
    actual = getattr(da, func)(skipna=skipna)
    expected = getattr(np, 'nan{}'.format(func))(da.values)
    assert np.allclose(actual.values, np.array(expected), rtol=rtol)


@pytest.mark.parametrize('dim_num', [1, 2])
@pytest.mark.parametrize('dtype', [float, int, np.float32, np.bool_, str])
@pytest.mark.parametrize('contains_nan', [True, False])
@pytest.mark.parametrize('dask', [False, True])
@pytest.mark.parametrize('func', ['min', 'max'])
@pytest.mark.parametrize('skipna', [False, True])
@pytest.mark.parametrize('aggdim', ['x', 'y'])
def test_argmin_max(dim_num, dtype, contains_nan, dask, func, skipna, aggdim):
    # pandas-dev/pandas#16830, we do not check consistency with pandas but
    # just make sure da[da.argmin()] == da.min()

    if aggdim == 'y' and dim_num < 2:
        return

    if dask and not has_dask:
        return

    if contains_nan:
        if not skipna:
            # numpy's argmin (not nanargmin) does not handle object-dtype
            return
        if skipna and np.dtype(dtype).kind in 'iufc':
            # numpy's nanargmin raises ValueError for all nan axis
            return

    da = construct_dataarray(dim_num, dtype, contains_nan=contains_nan,
                             dask=dask)

    if aggdim == 'y' and contains_nan and skipna:
        with pytest.raises(ValueError):
            actual = da.isel(**{
                aggdim: getattr(da, 'arg'+func)(dim=aggdim,
                                                skipna=skipna).compute()})
        return

    actual = da.isel(**{
        aggdim: getattr(da, 'arg'+func)(dim=aggdim, skipna=skipna).compute()})
    expected = getattr(da, func)(dim=aggdim, skipna=skipna)
    assert_allclose(actual.drop(actual.coords), expected.drop(expected.coords))
