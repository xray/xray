# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from copy import copy, deepcopy
from textwrap import dedent
try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    import dask.array as da
except ImportError:
    pass
from io import StringIO
from distutils.version import LooseVersion

import numpy as np
import pandas as pd
import xarray as xr
import pytest

from xarray import (align, broadcast, backends, Dataset, DataArray, Variable,
                    IndexVariable, open_dataset, set_options, MergeError)
from xarray.core import indexing, utils
from xarray.core.pycompat import (iteritems, OrderedDict, unicode_type,
                                  integer_types)
from xarray.core.common import full_like

from . import (TestCase, raises_regex, InaccessibleArray, UnexpectedDataAccess,
               requires_dask, source_ndarray)

from xarray.tests import (assert_equal, assert_allclose,
                          assert_array_equal)


def create_test_data(seed=None):
    rs = np.random.RandomState(seed)
    _vars = {'var1': ['dim1', 'dim2'],
             'var2': ['dim1', 'dim2'],
             'var3': ['dim3', 'dim1']}
    _dims = {'dim1': 8, 'dim2': 9, 'dim3': 10}

    obj = Dataset()
    obj['time'] = ('time', pd.date_range('2000-01-01', periods=20))
    obj['dim2'] = ('dim2', 0.5 * np.arange(_dims['dim2']))
    obj['dim3'] = ('dim3', list('abcdefghij'))
    for v, dims in sorted(_vars.items()):
        data = rs.normal(size=tuple(_dims[d] for d in dims))
        obj[v] = (dims, data, {'foo': 'variable'})
    obj.coords['numbers'] = ('dim3', np.array([0, 1, 2, 0, 0, 1, 1, 2, 2, 3],
                                              dtype='int64'))
    assert all(obj.data.flags.writeable for obj in obj.values())
    return obj


def create_test_multiindex():
    mindex = pd.MultiIndex.from_product([['a', 'b'], [1, 2]],
                                        names=('level_1', 'level_2'))
    return Dataset({}, {'x': mindex})


class InaccessibleVariableDataStore(backends.InMemoryDataStore):
    def __init__(self, writer=None):
        super(InaccessibleVariableDataStore, self).__init__(writer)
        self._indexvars = set()

    def store(self, variables, *args, **kwargs):
        super(InaccessibleVariableDataStore, self).store(
            variables, *args, **kwargs)
        for k, v in variables.items():
            if isinstance(v, IndexVariable):
                self._indexvars.add(k)

    def get_variables(self):
        def lazy_inaccessible(k, v):
            if k in self._indexvars:
                return v
            data = indexing.LazilyIndexedArray(InaccessibleArray(v.values))
            return Variable(v.dims, data, v.attrs)
        return dict((k, lazy_inaccessible(k, v)) for
                    k, v in iteritems(self._variables))


class TestDataset(TestCase):
    def test_repr(self):
        data = create_test_data(seed=123)
        data.attrs['foo'] = 'bar'
        # need to insert str dtype at runtime to handle both Python 2 & 3
        expected = dedent("""\
        <xarray.Dataset>
        Dimensions:  (dim1: 8, dim2: 9, dim3: 10, time: 20)
        Coordinates:
          * time     (time) datetime64[ns] 2000-01-01 2000-01-02 2000-01-03 ...
          * dim2     (dim2) float64 0.0 0.5 1.0 1.5 2.0 2.5 3.0 3.5 4.0
          * dim3     (dim3) %s 'a' 'b' 'c' 'd' 'e' 'f' 'g' 'h' 'i' 'j'
            numbers  (dim3) int64 0 1 2 0 0 1 1 2 2 3
        Dimensions without coordinates: dim1
        Data variables:
            var1     (dim1, dim2) float64 -1.086 0.9973 0.283 -1.506 -0.5786 1.651 ...
            var2     (dim1, dim2) float64 1.162 -1.097 -2.123 1.04 -0.4034 -0.126 ...
            var3     (dim3, dim1) float64 0.5565 -0.2121 0.4563 1.545 -0.2397 0.1433 ...
        Attributes:
            foo:      bar""") % data['dim3'].dtype
        actual = '\n'.join(x.rstrip() for x in repr(data).split('\n'))
        print(actual)
        self.assertEqual(expected, actual)

        with set_options(display_width=100):
            max_len = max(map(len, repr(data).split('\n')))
            assert 90 < max_len < 100

        expected = dedent("""\
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            *empty*""")
        actual = '\n'.join(x.rstrip() for x in repr(Dataset()).split('\n'))
        print(actual)
        self.assertEqual(expected, actual)

        # verify that ... doesn't appear for scalar coordinates
        data = Dataset({'foo': ('x', np.ones(10))}).mean()
        expected = dedent("""\
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            foo      float64 1.0""")
        actual = '\n'.join(x.rstrip() for x in repr(data).split('\n'))
        print(actual)
        self.assertEqual(expected, actual)

        # verify long attributes are truncated
        data = Dataset(attrs={'foo': 'bar' * 1000})
        self.assertTrue(len(repr(data)) < 1000)

    def test_repr_multiindex(self):
        data = create_test_multiindex()
        expected = dedent("""\
        <xarray.Dataset>
        Dimensions:  (x: 4)
        Coordinates:
          * x        (x) MultiIndex
          - level_1  (x) object 'a' 'a' 'b' 'b'
          - level_2  (x) int64 1 2 1 2
        Data variables:
            *empty*""")
        actual = '\n'.join(x.rstrip() for x in repr(data).split('\n'))
        print(actual)
        self.assertEqual(expected, actual)

        # verify that long level names are not truncated
        mindex = pd.MultiIndex.from_product(
            [['a', 'b'], [1, 2]],
            names=('a_quite_long_level_name', 'level_2'))
        data = Dataset({}, {'x': mindex})
        expected = dedent("""\
        <xarray.Dataset>
        Dimensions:                  (x: 4)
        Coordinates:
          * x                        (x) MultiIndex
          - a_quite_long_level_name  (x) object 'a' 'a' 'b' 'b'
          - level_2                  (x) int64 1 2 1 2
        Data variables:
            *empty*""")
        actual = '\n'.join(x.rstrip() for x in repr(data).split('\n'))
        print(actual)
        self.assertEqual(expected, actual)

    def test_repr_period_index(self):
        data = create_test_data(seed=456)
        data.coords['time'] = pd.period_range('2000-01-01', periods=20, freq='B')

        # check that creating the repr doesn't raise an error #GH645
        repr(data)

    def test_unicode_data(self):
        # regression test for GH834
        data = Dataset({u'foø': [u'ba®']}, attrs={u'å': u'∑'})
        repr(data)  # should not raise

        expected = dedent(u"""\
        <xarray.Dataset>
        Dimensions:  (foø: 1)
        Coordinates:
          * foø      (foø) <U3 %r
        Data variables:
            *empty*
        Attributes:
            å:        ∑""" % u'ba®')
        actual = unicode_type(data)
        self.assertEqual(expected, actual)

    def test_info(self):
        ds = create_test_data(seed=123)
        ds = ds.drop('dim3')  # string type prints differently in PY2 vs PY3
        ds.attrs['unicode_attr'] = u'ba®'
        ds.attrs['string_attr'] = 'bar'

        buf = StringIO()
        ds.info(buf=buf)

        expected = dedent(u'''\
        xarray.Dataset {
        dimensions:
        \tdim1 = 8 ;
        \tdim2 = 9 ;
        \tdim3 = 10 ;
        \ttime = 20 ;

        variables:
        \tdatetime64[ns] time(time) ;
        \tfloat64 dim2(dim2) ;
        \tfloat64 var1(dim1, dim2) ;
        \t\tvar1:foo = variable ;
        \tfloat64 var2(dim1, dim2) ;
        \t\tvar2:foo = variable ;
        \tfloat64 var3(dim3, dim1) ;
        \t\tvar3:foo = variable ;
        \tint64 numbers(dim3) ;

        // global attributes:
        \t:unicode_attr = ba® ;
        \t:string_attr = bar ;
        }''')
        actual = buf.getvalue()
        self.assertEqual(expected, actual)
        buf.close()

    def test_constructor(self):
        x1 = ('x', 2 * np.arange(100))
        x2 = ('x', np.arange(1000))
        z = (['x', 'y'], np.arange(1000).reshape(100, 10))

        with self.assertRaisesRegexp(ValueError, 'conflicting sizes'):
            Dataset({'a': x1, 'b': x2})
        with self.assertRaisesRegexp(ValueError, "disallows such variables"):
            Dataset({'a': x1, 'x': z})
        with self.assertRaisesRegexp(TypeError, 'tuples to convert'):
            Dataset({'x': (1, 2, 3, 4, 5, 6, 7)})
        with self.assertRaisesRegexp(ValueError, 'already exists as a scalar'):
            Dataset({'x': 0, 'y': ('x', [1, 2, 3])})

        # verify handling of DataArrays
        expected = Dataset({'x': x1, 'z': z})
        actual = Dataset({'z': expected['z']})
        self.assertDatasetIdentical(expected, actual)

    def test_constructor_invalid_dims(self):
        # regression for GH1120
        with self.assertRaises(MergeError):
            Dataset(data_vars=dict(v=('y', [1, 2, 3, 4])),
                    coords=dict(y=DataArray([.1, .2, .3, .4], dims='x')))

    def test_constructor_1d(self):
        expected = Dataset({'x': (['x'], 5.0 + np.arange(5))})
        actual = Dataset({'x': 5.0 + np.arange(5)})
        self.assertDatasetIdentical(expected, actual)

        actual = Dataset({'x': [5, 6, 7, 8, 9]})
        self.assertDatasetIdentical(expected, actual)

    def test_constructor_0d(self):
        expected = Dataset({'x': ([], 1)})
        for arg in [1, np.array(1), expected['x']]:
            actual = Dataset({'x': arg})
            self.assertDatasetIdentical(expected, actual)

        class Arbitrary(object):
            pass

        d = pd.Timestamp('2000-01-01T12')
        args = [True, None, 3.4, np.nan, 'hello', u'uni', b'raw',
                np.datetime64('2000-01-01T00'), d, d.to_datetime(),
                Arbitrary()]
        for arg in args:
            print(arg)
            expected = Dataset({'x': ([], arg)})
            actual = Dataset({'x': arg})
            self.assertDatasetIdentical(expected, actual)

    def test_constructor_deprecated(self):
        with self.assertRaisesRegexp(ValueError, 'DataArray dimensions'):
            DataArray([1, 2, 3], coords={'x': [0, 1, 2]})

    def test_constructor_auto_align(self):
        a = DataArray([1, 2], [('x', [0, 1])])
        b = DataArray([3, 4], [('x', [1, 2])])

        # verify align uses outer join
        expected = Dataset({'a': ('x', [1, 2, np.nan]),
                            'b': ('x', [np.nan, 3, 4])},
                           {'x': [0, 1, 2]})
        actual = Dataset({'a': a, 'b': b})
        self.assertDatasetIdentical(expected, actual)

        # regression test for GH346
        self.assertIsInstance(actual.variables['x'], IndexVariable)

        # variable with different dimensions
        c = ('y', [3, 4])
        expected2 = expected.merge({'c': c})
        actual = Dataset({'a': a, 'b': b, 'c': c})
        self.assertDatasetIdentical(expected2, actual)

        # variable that is only aligned against the aligned variables
        d = ('x', [3, 2, 1])
        expected3 = expected.merge({'d': d})
        actual = Dataset({'a': a, 'b': b, 'd': d})
        self.assertDatasetIdentical(expected3, actual)

        e = ('x', [0, 0])
        with self.assertRaisesRegexp(ValueError, 'conflicting sizes'):
            Dataset({'a': a, 'b': b, 'e': e})

    def test_constructor_pandas_sequence(self):

        ds = self.make_example_math_dataset()
        pandas_objs = OrderedDict(
            (var_name, ds[var_name].to_pandas()) for var_name in ['foo','bar']
        )
        ds_based_on_pandas = Dataset(pandas_objs, ds.coords, attrs=ds.attrs)
        del ds_based_on_pandas['x']
        self.assertDatasetEqual(ds, ds_based_on_pandas)

        # reindex pandas obj, check align works
        rearranged_index = reversed(pandas_objs['foo'].index)
        pandas_objs['foo'] = pandas_objs['foo'].reindex(rearranged_index)
        ds_based_on_pandas = Dataset(pandas_objs, ds.coords, attrs=ds.attrs)
        del ds_based_on_pandas['x']
        self.assertDatasetEqual(ds, ds_based_on_pandas)

    def test_constructor_pandas_single(self):

        das = [
            DataArray(np.random.rand(4), dims=['a']),  # series
            DataArray(np.random.rand(4,3), dims=['a', 'b']),  # df
            DataArray(np.random.rand(4,3,2), dims=['a','b','c']), # panel
            ]

        for da in das:
            pandas_obj = da.to_pandas()
            ds_based_on_pandas = Dataset(pandas_obj)
            for dim in ds_based_on_pandas.data_vars:
                self.assertArrayEqual(ds_based_on_pandas[dim], pandas_obj[dim])


    def test_constructor_compat(self):
        data = OrderedDict([('x', DataArray(0, coords={'y': 1})),
                            ('y', ('z', [1, 1, 1]))])
        with self.assertRaises(MergeError):
            Dataset(data, compat='equals')
        expected = Dataset({'x': 0}, {'y': ('z', [1, 1, 1])})
        actual = Dataset(data)
        self.assertDatasetIdentical(expected, actual)
        actual = Dataset(data, compat='broadcast_equals')
        self.assertDatasetIdentical(expected, actual)

        data = OrderedDict([('y', ('z', [1, 1, 1])),
                            ('x', DataArray(0, coords={'y': 1}))])
        actual = Dataset(data)
        self.assertDatasetIdentical(expected, actual)

        original = Dataset({'a': (('x', 'y'), np.ones((2, 3)))},
                           {'c': (('x', 'y'), np.zeros((2, 3))), 'x': [0, 1]})
        expected = Dataset({'a': ('x', np.ones(2)),
                            'b': ('y', np.ones(3))},
                           {'c': (('x', 'y'), np.zeros((2, 3))), 'x': [0, 1]})
        # use an OrderedDict to ensure test results are reproducible; otherwise
        # the order of appearance of x and y matters for the order of
        # dimensions in 'c'
        actual = Dataset(OrderedDict([('a', original['a'][:, 0]),
                                      ('b', original['a'][0].drop('x'))]))
        self.assertDatasetIdentical(expected, actual)

        data = {'x': DataArray(0, coords={'y': 3}), 'y': ('z', [1, 1, 1])}
        with self.assertRaises(MergeError):
            Dataset(data)

        data = {'x': DataArray(0, coords={'y': 1}), 'y': [1, 1]}
        actual = Dataset(data)
        expected = Dataset({'x': 0}, {'y': [1, 1]})
        self.assertDatasetIdentical(expected, actual)

    def test_constructor_with_coords(self):
        with self.assertRaisesRegexp(ValueError, 'found in both data_vars and'):
            Dataset({'a': ('x', [1])}, {'a': ('x', [1])})

        ds = Dataset({}, {'a': ('x', [1])})
        self.assertFalse(ds.data_vars)
        self.assertItemsEqual(ds.coords.keys(), ['a'])

        mindex = pd.MultiIndex.from_product([['a', 'b'], [1, 2]],
                                            names=('level_1', 'level_2'))
        with self.assertRaisesRegexp(ValueError, 'conflicting MultiIndex'):
            Dataset({}, {'x': mindex, 'y': mindex})
            Dataset({}, {'x': mindex, 'level_1': range(4)})

    def test_properties(self):
        ds = create_test_data()
        self.assertEqual(ds.dims,
                         {'dim1': 8, 'dim2': 9, 'dim3': 10, 'time': 20})
        self.assertEqual(list(ds.dims), sorted(ds.dims))
        self.assertEqual(ds.sizes, ds.dims)

        # These exact types aren't public API, but this makes sure we don't
        # change them inadvertently:
        self.assertIsInstance(ds.dims, utils.Frozen)
        self.assertIsInstance(ds.dims.mapping, utils.SortedKeysDict)
        self.assertIs(type(ds.dims.mapping.mapping), dict)

        self.assertItemsEqual(ds, list(ds.variables))
        self.assertItemsEqual(ds.keys(), list(ds.variables))
        self.assertNotIn('aasldfjalskdfj', ds.variables)
        self.assertIn('dim1', repr(ds.variables))
        self.assertEqual(len(ds), 7)

        self.assertItemsEqual(ds.data_vars, ['var1', 'var2', 'var3'])
        self.assertItemsEqual(ds.data_vars.keys(), ['var1', 'var2', 'var3'])
        self.assertIn('var1', ds.data_vars)
        self.assertNotIn('dim1', ds.data_vars)
        self.assertNotIn('numbers', ds.data_vars)
        self.assertEqual(len(ds.data_vars), 3)

        self.assertItemsEqual(ds.indexes, ['dim2', 'dim3', 'time'])
        self.assertEqual(len(ds.indexes), 3)
        self.assertIn('dim2', repr(ds.indexes))

        self.assertItemsEqual(ds.coords, ['time', 'dim2', 'dim3', 'numbers'])
        self.assertIn('dim2', ds.coords)
        self.assertIn('numbers', ds.coords)
        self.assertNotIn('var1', ds.coords)
        self.assertNotIn('dim1', ds.coords)
        self.assertEqual(len(ds.coords), 4)

        self.assertEqual(Dataset({'x': np.int64(1),
                                  'y': np.float32([1, 2])}).nbytes, 16)

    def test_get_index(self):
        ds = Dataset({'foo': (('x', 'y'), np.zeros((2, 3)))},
                     coords={'x': ['a', 'b']})
        assert ds.get_index('x').equals(pd.Index(['a', 'b']))
        assert ds.get_index('y').equals(pd.Index([0, 1, 2]))
        with self.assertRaises(KeyError):
            ds.get_index('z')

    def test_attr_access(self):
        ds = Dataset({'tmin': ('x', [42], {'units': 'Celcius'})},
                     attrs={'title': 'My test data'})
        self.assertDataArrayIdentical(ds.tmin, ds['tmin'])
        self.assertDataArrayIdentical(ds.tmin.x, ds.x)

        self.assertEqual(ds.title, ds.attrs['title'])
        self.assertEqual(ds.tmin.units, ds['tmin'].attrs['units'])

        self.assertLessEqual(set(['tmin', 'title']), set(dir(ds)))
        self.assertIn('units', set(dir(ds.tmin)))

        # should defer to variable of same name
        ds.attrs['tmin'] = -999
        self.assertEqual(ds.attrs['tmin'], -999)
        self.assertDataArrayIdentical(ds.tmin, ds['tmin'])

    def test_variable(self):
        a = Dataset()
        d = np.random.random((10, 3))
        a['foo'] = (('time', 'x',), d)
        self.assertTrue('foo' in a.variables)
        self.assertTrue('foo' in a)
        a['bar'] = (('time', 'x',), d)
        # order of creation is preserved
        self.assertEqual(list(a), ['foo', 'bar'])
        self.assertArrayEqual(a['foo'].values, d)
        # try to add variable with dim (10,3) with data that's (3,10)
        with self.assertRaises(ValueError):
            a['qux'] = (('time', 'x'), d.T)

    def test_modify_inplace(self):
        a = Dataset()
        vec = np.random.random((10,))
        attributes = {'foo': 'bar'}
        a['x'] = ('x', vec, attributes)
        self.assertTrue('x' in a.coords)
        self.assertIsInstance(a.coords['x'].to_index(), pd.Index)
        self.assertVariableIdentical(a.coords['x'].variable, a.variables['x'])
        b = Dataset()
        b['x'] = ('x', vec, attributes)
        self.assertVariableIdentical(a['x'], b['x'])
        self.assertEqual(a.dims, b.dims)
        # this should work
        a['x'] = ('x', vec[:5])
        a['z'] = ('x', np.arange(5))
        with self.assertRaises(ValueError):
            # now it shouldn't, since there is a conflicting length
            a['x'] = ('x', vec[:4])
        arr = np.random.random((10, 1,))
        scal = np.array(0)
        with self.assertRaises(ValueError):
            a['y'] = ('y', arr)
        with self.assertRaises(ValueError):
            a['y'] = ('y', scal)
        self.assertTrue('y' not in a.dims)

    def test_coords_properties(self):
        # use an OrderedDict for coordinates to ensure order across python
        # versions
        # use int64 for repr consistency on windows
        data = Dataset(OrderedDict([('x', ('x', np.array([-1, -2], 'int64'))),
                                    ('y', ('y', np.array([0, 1, 2], 'int64'))),
                                    ('foo', (['x', 'y'],
                                             np.random.randn(2, 3)))]),
                       OrderedDict([('a', ('x', np.array([4, 5], 'int64'))),
                                    ('b', np.int64(-10))]))

        self.assertEqual(4, len(data.coords))

        self.assertItemsEqual(['x', 'y', 'a', 'b'], list(data.coords))

        self.assertVariableIdentical(data.coords['x'].variable, data['x'].variable)
        self.assertVariableIdentical(data.coords['y'].variable, data['y'].variable)

        self.assertIn('x', data.coords)
        self.assertIn('a', data.coords)
        self.assertNotIn(0, data.coords)
        self.assertNotIn('foo', data.coords)

        with self.assertRaises(KeyError):
            data.coords['foo']
        with self.assertRaises(KeyError):
            data.coords[0]

        expected = dedent("""\
        Coordinates:
          * x        (x) int64 -1 -2
          * y        (y) int64 0 1 2
            a        (x) int64 4 5
            b        int64 -10""")
        actual = repr(data.coords)
        self.assertEqual(expected, actual)

        self.assertEqual({'x': 2, 'y': 3}, data.coords.dims)

    def test_coords_modify(self):
        data = Dataset({'x': ('x', [-1, -2]),
                        'y': ('y', [0, 1, 2]),
                        'foo': (['x', 'y'], np.random.randn(2, 3))},
                       {'a': ('x', [4, 5]), 'b': -10})

        actual = data.copy(deep=True)
        actual.coords['x'] = ('x', ['a', 'b'])
        self.assertArrayEqual(actual['x'], ['a', 'b'])

        actual = data.copy(deep=True)
        actual.coords['z'] = ('z', ['a', 'b'])
        self.assertArrayEqual(actual['z'], ['a', 'b'])

        actual = data.copy(deep=True)
        with self.assertRaisesRegexp(ValueError, 'conflicting sizes'):
            actual.coords['x'] = ('x', [-1])
        self.assertDatasetIdentical(actual, data)  # should not be modified

        actual = data.copy()
        del actual.coords['b']
        expected = data.reset_coords('b', drop=True)
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaises(KeyError):
            del data.coords['not_found']

        with self.assertRaises(KeyError):
            del data.coords['foo']

        actual = data.copy(deep=True)
        actual.coords.update({'c': 11})
        expected = data.merge({'c': 11}).set_coords('c')
        self.assertDatasetIdentical(expected, actual)

    def test_coords_setitem_with_new_dimension(self):
        actual = Dataset()
        actual.coords['foo'] = ('x', [1, 2, 3])
        expected = Dataset(coords={'foo': ('x', [1, 2, 3])})
        self.assertDatasetIdentical(expected, actual)

    def test_coords_setitem_multiindex(self):
        data = create_test_multiindex()
        with self.assertRaisesRegexp(ValueError, 'conflicting MultiIndex'):
            data.coords['level_1'] = range(4)

    def test_coords_set(self):
        one_coord = Dataset({'x': ('x', [0]),
                             'yy': ('x', [1]),
                             'zzz': ('x', [2])})
        two_coords = Dataset({'zzz': ('x', [2])},
                             {'x': ('x', [0]),
                              'yy': ('x', [1])})
        all_coords = Dataset(coords={'x': ('x', [0]),
                                     'yy': ('x', [1]),
                                     'zzz': ('x', [2])})

        actual = one_coord.set_coords('x')
        self.assertDatasetIdentical(one_coord, actual)
        actual = one_coord.set_coords(['x'])
        self.assertDatasetIdentical(one_coord, actual)

        actual = one_coord.set_coords('yy')
        self.assertDatasetIdentical(two_coords, actual)

        actual = one_coord.set_coords(['yy', 'zzz'])
        self.assertDatasetIdentical(all_coords, actual)

        actual = one_coord.reset_coords()
        self.assertDatasetIdentical(one_coord, actual)
        actual = two_coords.reset_coords()
        self.assertDatasetIdentical(one_coord, actual)
        actual = all_coords.reset_coords()
        self.assertDatasetIdentical(one_coord, actual)

        actual = all_coords.reset_coords(['yy', 'zzz'])
        self.assertDatasetIdentical(one_coord, actual)
        actual = all_coords.reset_coords('zzz')
        self.assertDatasetIdentical(two_coords, actual)

        with self.assertRaisesRegexp(ValueError, 'cannot remove index'):
            one_coord.reset_coords('x')

        actual = all_coords.reset_coords('zzz', drop=True)
        expected = all_coords.drop('zzz')
        self.assertDatasetIdentical(expected, actual)
        expected = two_coords.drop('zzz')
        self.assertDatasetIdentical(expected, actual)

    def test_coords_to_dataset(self):
        orig = Dataset({'foo': ('y', [-1, 0, 1])}, {'x': 10, 'y': [2, 3, 4]})
        expected = Dataset(coords={'x': 10, 'y': [2, 3, 4]})
        actual = orig.coords.to_dataset()
        self.assertDatasetIdentical(expected, actual)

    def test_coords_merge(self):
        orig_coords = Dataset(coords={'a': ('x', [1, 2]), 'x': [0, 1]}).coords
        other_coords = Dataset(coords={'b': ('x', ['a', 'b']),
                                       'x': [0, 1]}).coords
        expected = Dataset(coords={'a': ('x', [1, 2]),
                                   'b': ('x', ['a', 'b']),
                                   'x': [0, 1]})
        actual = orig_coords.merge(other_coords)
        self.assertDatasetIdentical(expected, actual)
        actual = other_coords.merge(orig_coords)
        self.assertDatasetIdentical(expected, actual)

        other_coords = Dataset(coords={'x': ('x', ['a'])}).coords
        with self.assertRaises(MergeError):
            orig_coords.merge(other_coords)
        other_coords = Dataset(coords={'x': ('x', ['a', 'b'])}).coords
        with self.assertRaises(MergeError):
            orig_coords.merge(other_coords)
        other_coords = Dataset(coords={'x': ('x', ['a', 'b', 'c'])}).coords
        with self.assertRaises(MergeError):
            orig_coords.merge(other_coords)

        other_coords = Dataset(coords={'a': ('x', [8, 9])}).coords
        expected = Dataset(coords={'x': range(2)})
        actual = orig_coords.merge(other_coords)
        self.assertDatasetIdentical(expected, actual)
        actual = other_coords.merge(orig_coords)
        self.assertDatasetIdentical(expected, actual)

        other_coords = Dataset(coords={'x': np.nan}).coords
        actual = orig_coords.merge(other_coords)
        self.assertDatasetIdentical(orig_coords.to_dataset(), actual)
        actual = other_coords.merge(orig_coords)
        self.assertDatasetIdentical(orig_coords.to_dataset(), actual)

    def test_coords_merge_mismatched_shape(self):
        orig_coords = Dataset(coords={'a': ('x', [1, 1])}).coords
        other_coords = Dataset(coords={'a': 1}).coords
        expected = orig_coords.to_dataset()
        actual = orig_coords.merge(other_coords)
        self.assertDatasetIdentical(expected, actual)

        other_coords = Dataset(coords={'a': ('y', [1])}).coords
        expected = Dataset(coords={'a': (['x', 'y'], [[1], [1]])})
        actual = orig_coords.merge(other_coords)
        self.assertDatasetIdentical(expected, actual)

        actual = other_coords.merge(orig_coords)
        self.assertDatasetIdentical(expected.T, actual)

        orig_coords = Dataset(coords={'a': ('x', [np.nan])}).coords
        other_coords = Dataset(coords={'a': np.nan}).coords
        expected = orig_coords.to_dataset()
        actual = orig_coords.merge(other_coords)
        self.assertDatasetIdentical(expected, actual)

    def test_data_vars_properties(self):
        ds = Dataset()
        ds['foo'] = (('x',), [1.0])
        ds['bar'] = 2.0

        self.assertEqual(set(ds.data_vars), {'foo', 'bar'})
        self.assertIn('foo', ds.data_vars)
        self.assertNotIn('x', ds.data_vars)
        self.assertDataArrayIdentical(ds['foo'], ds.data_vars['foo'])

        expected = dedent("""\
        Data variables:
            foo      (x) float64 1.0
            bar      float64 2.0""")
        actual = repr(ds.data_vars)
        self.assertEqual(expected, actual)

    def test_equals_and_identical(self):
        data = create_test_data(seed=42)
        self.assertTrue(data.equals(data))
        self.assertTrue(data.identical(data))

        data2 = create_test_data(seed=42)
        data2.attrs['foobar'] = 'baz'
        self.assertTrue(data.equals(data2))
        self.assertFalse(data.identical(data2))

        del data2['time']
        self.assertFalse(data.equals(data2))

        data = create_test_data(seed=42).rename({'var1': None})
        self.assertTrue(data.equals(data))
        self.assertTrue(data.identical(data))

        data2 = data.reset_coords()
        self.assertFalse(data2.equals(data))
        self.assertFalse(data2.identical(data))

    def test_equals_failures(self):
        data = create_test_data()
        self.assertFalse(data.equals('foo'))
        self.assertFalse(data.identical(123))
        self.assertFalse(data.broadcast_equals({1: 2}))

    def test_broadcast_equals(self):
        data1 = Dataset(coords={'x': 0})
        data2 = Dataset(coords={'x': [0]})
        self.assertTrue(data1.broadcast_equals(data2))
        self.assertFalse(data1.equals(data2))
        self.assertFalse(data1.identical(data2))

    def test_attrs(self):
        data = create_test_data(seed=42)
        data.attrs = {'foobar': 'baz'}
        self.assertTrue(data.attrs['foobar'], 'baz')
        self.assertIsInstance(data.attrs, OrderedDict)

    @requires_dask
    def test_chunk(self):
        data = create_test_data()
        for v in data.variables.values():
            self.assertIsInstance(v.data, np.ndarray)
        self.assertEqual(data.chunks, {})

        reblocked = data.chunk()
        for k, v in reblocked.variables.items():
            if k in reblocked.dims:
                self.assertIsInstance(v.data, np.ndarray)
            else:
                self.assertIsInstance(v.data, da.Array)

        expected_chunks = {'dim1': (8,), 'dim2': (9,), 'dim3': (10,)}
        self.assertEqual(reblocked.chunks, expected_chunks)

        reblocked = data.chunk({'time': 5, 'dim1': 5, 'dim2': 5, 'dim3': 5})
        # time is not a dim in any of the data_vars, so it
        # doesn't get chunked
        expected_chunks = {'dim1': (5, 3), 'dim2': (5, 4), 'dim3': (5, 5)}
        self.assertEqual(reblocked.chunks, expected_chunks)

        reblocked = data.chunk(expected_chunks)
        self.assertEqual(reblocked.chunks, expected_chunks)

        # reblock on already blocked data
        reblocked = reblocked.chunk(expected_chunks)
        self.assertEqual(reblocked.chunks, expected_chunks)
        self.assertDatasetIdentical(reblocked, data)

        with self.assertRaisesRegexp(ValueError, 'some chunks'):
            data.chunk({'foo': 10})

    @requires_dask
    def test_dask_is_lazy(self):
        store = InaccessibleVariableDataStore()
        create_test_data().dump_to_store(store)
        ds = open_dataset(store).chunk()

        with self.assertRaises(UnexpectedDataAccess):
            ds.load()
        with self.assertRaises(UnexpectedDataAccess):
            ds['var1'].values

        # these should not raise UnexpectedDataAccess:
        ds.var1.data
        ds.isel(time=10)
        ds.isel(time=slice(10), dim1=[0]).isel(dim1=0, dim2=-1)
        ds.transpose()
        ds.mean()
        ds.fillna(0)
        ds.rename({'dim1': 'foobar'})
        ds.set_coords('var1')
        ds.drop('var1')

    def test_isel(self):
        data = create_test_data()
        slicers = {'dim1': slice(None, None, 2), 'dim2': slice(0, 2)}
        ret = data.isel(**slicers)

        # Verify that only the specified dimension was altered
        self.assertItemsEqual(data.dims, ret.dims)
        for d in data.dims:
            if d in slicers:
                self.assertEqual(ret.dims[d],
                                 np.arange(data.dims[d])[slicers[d]].size)
            else:
                self.assertEqual(data.dims[d], ret.dims[d])
        # Verify that the data is what we expect
        for v in data:
            self.assertEqual(data[v].dims, ret[v].dims)
            self.assertEqual(data[v].attrs, ret[v].attrs)
            slice_list = [slice(None)] * data[v].values.ndim
            for d, s in iteritems(slicers):
                if d in data[v].dims:
                    inds = np.nonzero(np.array(data[v].dims) == d)[0]
                    for ind in inds:
                        slice_list[ind] = s
            expected = data[v].values[slice_list]
            actual = ret[v].values
            np.testing.assert_array_equal(expected, actual)

        with self.assertRaises(ValueError):
            data.isel(not_a_dim=slice(0, 2))

        ret = data.isel(dim1=0)
        self.assertEqual({'time': 20, 'dim2': 9, 'dim3': 10}, ret.dims)
        self.assertItemsEqual(data.data_vars, ret.data_vars)
        self.assertItemsEqual(data.coords, ret.coords)
        self.assertItemsEqual(data.indexes, ret.indexes)

        ret = data.isel(time=slice(2), dim1=0, dim2=slice(5))
        self.assertEqual({'time': 2, 'dim2': 5, 'dim3': 10}, ret.dims)
        self.assertItemsEqual(data.data_vars, ret.data_vars)
        self.assertItemsEqual(data.coords, ret.coords)
        self.assertItemsEqual(data.indexes, ret.indexes)

        ret = data.isel(time=0, dim1=0, dim2=slice(5))
        self.assertItemsEqual({'dim2': 5, 'dim3': 10}, ret.dims)
        self.assertItemsEqual(data.data_vars, ret.data_vars)
        self.assertItemsEqual(data.coords, ret.coords)
        self.assertItemsEqual(data.indexes, list(ret.indexes) + ['time'])

    def test_sel(self):
        data = create_test_data()
        int_slicers = {'dim1': slice(None, None, 2),
                       'dim2': slice(2),
                       'dim3': slice(3)}
        loc_slicers = {'dim1': slice(None, None, 2),
                       'dim2': slice(0, 0.5),
                       'dim3': slice('a', 'c')}
        self.assertDatasetEqual(data.isel(**int_slicers),
                                data.sel(**loc_slicers))
        data['time'] = ('time', pd.date_range('2000-01-01', periods=20))
        self.assertDatasetEqual(data.isel(time=0),
                                data.sel(time='2000-01-01'))
        self.assertDatasetEqual(data.isel(time=slice(10)),
                                data.sel(time=slice('2000-01-01',
                                                    '2000-01-10')))
        self.assertDatasetEqual(data, data.sel(time=slice('1999', '2005')))
        times = pd.date_range('2000-01-01', periods=3)
        self.assertDatasetEqual(data.isel(time=slice(3)),
                                data.sel(time=times))
        self.assertDatasetEqual(data.isel(time=slice(3)),
                                data.sel(time=(data['time.dayofyear'] <= 3)))

        td = pd.to_timedelta(np.arange(3), unit='days')
        data = Dataset({'x': ('td', np.arange(3)), 'td': td})
        self.assertDatasetEqual(data, data.sel(td=td))
        self.assertDatasetEqual(data, data.sel(td=slice('3 days')))
        self.assertDatasetEqual(data.isel(td=0),
                                data.sel(td=pd.Timedelta('0 days')))
        self.assertDatasetEqual(data.isel(td=0),
                                data.sel(td=pd.Timedelta('0h')))
        self.assertDatasetEqual(data.isel(td=slice(1, 3)),
                                data.sel(td=slice('1 days', '2 days')))

    def test_sel_drop(self):
        data = Dataset({'foo': ('x', [1, 2, 3])}, {'x': [0, 1, 2]})
        expected = Dataset({'foo': 1})
        selected = data.sel(x=0, drop=True)
        self.assertDatasetIdentical(expected, selected)

        expected = Dataset({'foo': 1}, {'x': 0})
        selected = data.sel(x=0, drop=False)
        self.assertDatasetIdentical(expected, selected)

        data = Dataset({'foo': ('x', [1, 2, 3])})
        expected = Dataset({'foo': 1})
        selected = data.sel(x=0, drop=True)
        self.assertDatasetIdentical(expected, selected)

    def test_isel_drop(self):
        data = Dataset({'foo': ('x', [1, 2, 3])}, {'x': [0, 1, 2]})
        expected = Dataset({'foo': 1})
        selected = data.isel(x=0, drop=True)
        self.assertDatasetIdentical(expected, selected)

        expected = Dataset({'foo': 1}, {'x': 0})
        selected = data.isel(x=0, drop=False)
        self.assertDatasetIdentical(expected, selected)

    def test_isel_points(self):
        data = create_test_data()

        pdim1 = [1, 2, 3]
        pdim2 = [4, 5, 1]
        pdim3 = [1, 2, 3]
        actual = data.isel_points(dim1=pdim1, dim2=pdim2, dim3=pdim3,
                                  dim='test_coord')
        assert 'test_coord' in actual.dims
        assert actual.coords['test_coord'].shape == (len(pdim1), )

        actual = data.isel_points(dim1=pdim1, dim2=pdim2)
        assert 'points' in actual.dims
        assert 'dim3' in actual.dims
        assert 'dim3' not in actual.data_vars
        np.testing.assert_array_equal(data['dim2'][pdim2], actual['dim2'])

        # test that the order of the indexers doesn't matter
        self.assertDatasetIdentical(data.isel_points(dim1=pdim1, dim2=pdim2),
                                    data.isel_points(dim2=pdim2, dim1=pdim1))

        # make sure we're raising errors in the right places
        with self.assertRaisesRegexp(ValueError,
                                     'All indexers must be the same length'):
            data.isel_points(dim1=[1, 2], dim2=[1, 2, 3])
        with self.assertRaisesRegexp(ValueError,
                                     'dimension bad_key does not exist'):
            data.isel_points(bad_key=[1, 2])
        with self.assertRaisesRegexp(TypeError, 'Indexers must be integers'):
            data.isel_points(dim1=[1.5, 2.2])
        with self.assertRaisesRegexp(TypeError, 'Indexers must be integers'):
            data.isel_points(dim1=[1, 2, 3], dim2=slice(3))
        with self.assertRaisesRegexp(ValueError,
                                     'Indexers must be 1 dimensional'):
            data.isel_points(dim1=1, dim2=2)
        with self.assertRaisesRegexp(ValueError,
                                     'Existing dimension names are not valid'):
            data.isel_points(dim1=[1, 2], dim2=[1, 2], dim='dim2')

        # test to be sure we keep around variables that were not indexed
        ds = Dataset({'x': [1, 2, 3, 4], 'y': 0})
        actual = ds.isel_points(x=[0, 1, 2])
        self.assertDataArrayIdentical(ds['y'], actual['y'])

        # tests using index or DataArray as a dim
        stations = Dataset()
        stations['station'] = ('station', ['A', 'B', 'C'])
        stations['dim1s'] = ('station', [1, 2, 3])
        stations['dim2s'] = ('station', [4, 5, 1])

        actual = data.isel_points(dim1=stations['dim1s'],
                                  dim2=stations['dim2s'],
                                  dim=stations['station'])
        assert 'station' in actual.coords
        assert 'station' in actual.dims
        self.assertDataArrayIdentical(actual['station'].drop(['dim2']),
                                      stations['station'])

        # make sure we get the default 'points' coordinate when a list is passed
        actual = data.isel_points(dim1=stations['dim1s'],
                                  dim2=stations['dim2s'],
                                  dim=['A', 'B', 'C'])
        assert 'points' in actual.coords
        assert actual.coords['points'].values.tolist() == ['A', 'B', 'C']

        # test index
        actual = data.isel_points(dim1=stations['dim1s'].values,
                                  dim2=stations['dim2s'].values,
                                  dim=pd.Index(['A', 'B', 'C'], name='letters'))
        assert 'letters' in actual.coords

        # can pass a numpy array
        data.isel_points(dim1=stations['dim1s'],
                         dim2=stations['dim2s'],
                         dim=np.array([4, 5, 6]))

    def test_sel_points(self):
        data = create_test_data()

        # add in a range() index
        data['dim1'] = data.dim1

        pdim1 = [1, 2, 3]
        pdim2 = [4, 5, 1]
        pdim3 = [1, 2, 3]
        expected = data.isel_points(dim1=pdim1, dim2=pdim2, dim3=pdim3,
                                    dim='test_coord')
        actual = data.sel_points(dim1=data.dim1[pdim1], dim2=data.dim2[pdim2],
                                 dim3=data.dim3[pdim3], dim='test_coord')
        self.assertDatasetIdentical(expected, actual)

        data = Dataset({'foo': (('x', 'y'), np.arange(9).reshape(3, 3))})
        expected = Dataset({'foo': ('points', [0, 4, 8])}
                            )
        actual = data.sel_points(x=[0, 1, 2], y=[0, 1, 2])
        self.assertDatasetIdentical(expected, actual)

        data.coords.update({'x': [0, 1, 2], 'y': [0, 1, 2]})
        expected.coords.update({'x': ('points', [0, 1, 2]),
                                'y': ('points', [0, 1, 2])
                                })
        actual = data.sel_points(x=[0.1, 1.1, 2.5], y=[0, 1.2, 2.0],
                                 method='pad')
        self.assertDatasetIdentical(expected, actual)

        if pd.__version__ >= '0.17':
            with self.assertRaises(KeyError):
                data.sel_points(x=[2.5], y=[2.0], method='pad', tolerance=1e-3)

    def test_sel_method(self):
        data = create_test_data()

        if pd.__version__ >= '0.16':
            expected = data.sel(dim2=1)
            actual = data.sel(dim2=0.95, method='nearest')
            self.assertDatasetIdentical(expected, actual)

        if pd.__version__ >= '0.17':
            actual = data.sel(dim2=0.95, method='nearest', tolerance=1)
            self.assertDatasetIdentical(expected, actual)

            with self.assertRaises(KeyError):
                actual = data.sel(dim2=np.pi, method='nearest', tolerance=0)

        expected = data.sel(dim2=[1.5])
        actual = data.sel(dim2=[1.45], method='backfill')
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaisesRegexp(NotImplementedError, 'slice objects'):
            data.sel(dim2=slice(1, 3), method='ffill')

        with self.assertRaisesRegexp(TypeError, '``method``'):
            # this should not pass silently
            data.sel(data)

        # cannot pass method if there is no associated coordinate
        with self.assertRaisesRegexp(ValueError, 'cannot supply'):
            data.sel(dim1=0, method='nearest')

    def test_loc(self):
        data = create_test_data()
        expected = data.sel(dim3='a')
        actual = data.loc[dict(dim3='a')]
        self.assertDatasetIdentical(expected, actual)
        with self.assertRaisesRegexp(TypeError, 'can only lookup dict'):
            data.loc['a']
        with self.assertRaises(TypeError):
            data.loc[dict(dim3='a')] = 0

    def test_selection_multiindex(self):
        mindex = pd.MultiIndex.from_product([['a', 'b'], [1, 2], [-1, -2]],
                                            names=('one', 'two', 'three'))
        mdata = Dataset(data_vars={'var': ('x', range(8))},
                        coords={'x': mindex})

        def test_sel(lab_indexer, pos_indexer, replaced_idx=False,
                     renamed_dim=None):
            ds = mdata.sel(x=lab_indexer)
            expected_ds = mdata.isel(x=pos_indexer)
            if not replaced_idx:
                self.assertDatasetIdentical(ds, expected_ds)
            else:
                if renamed_dim:
                    self.assertEqual(ds['var'].dims[0], renamed_dim)
                    ds = ds.rename({renamed_dim: 'x'})
                self.assertVariableIdentical(ds['var'].variable,
                                             expected_ds['var'].variable)
                self.assertVariableNotEqual(ds['x'], expected_ds['x'])

        test_sel(('a', 1, -1), 0)
        test_sel(('b', 2, -2), -1)
        test_sel(('a', 1), [0, 1], replaced_idx=True, renamed_dim='three')
        test_sel(('a',), range(4), replaced_idx=True)
        test_sel('a', range(4), replaced_idx=True)
        test_sel([('a', 1, -1), ('b', 2, -2)], [0, 7])
        test_sel(slice('a', 'b'), range(8))
        test_sel(slice(('a', 1), ('b', 1)), range(6))
        test_sel({'one': 'a', 'two': 1, 'three': -1}, 0)
        test_sel({'one': 'a', 'two': 1}, [0, 1], replaced_idx=True,
                 renamed_dim='three')
        test_sel({'one': 'a'}, range(4), replaced_idx=True)

        self.assertDatasetIdentical(mdata.loc[{'x': {'one': 'a'}}],
                                    mdata.sel(x={'one': 'a'}))
        self.assertDatasetIdentical(mdata.loc[{'x': 'a'}],
                                    mdata.sel(x='a'))
        self.assertDatasetIdentical(mdata.loc[{'x': ('a', 1)}],
                                    mdata.sel(x=('a', 1)))
        self.assertDatasetIdentical(mdata.loc[{'x': ('a', 1, -1)}],
                                    mdata.sel(x=('a', 1, -1)))

        self.assertDatasetIdentical(mdata.sel(x={'one': 'a', 'two': 1}),
                                    mdata.sel(one='a', two=1))

    def test_reindex_like(self):
        data = create_test_data()
        data['letters'] = ('dim3', 10 * ['a'])

        expected = data.isel(dim1=slice(10), time=slice(13))
        actual = data.reindex_like(expected)
        self.assertDatasetIdentical(actual, expected)

        expected = data.copy(deep=True)
        expected['dim3'] = ('dim3', list('cdefghijkl'))
        expected['var3'][:-2] = expected['var3'][2:]
        expected['var3'][-2:] = np.nan
        expected['letters'] = expected['letters'].astype(object)
        expected['letters'][-2:] = np.nan
        expected['numbers'] = expected['numbers'].astype(float)
        expected['numbers'][:-2] = expected['numbers'][2:].values
        expected['numbers'][-2:] = np.nan
        actual = data.reindex_like(expected)
        self.assertDatasetIdentical(actual, expected)

    def test_reindex(self):
        data = create_test_data()
        self.assertDatasetIdentical(data, data.reindex())

        expected = data.assign_coords(dim1=data['dim1'])
        actual = data.reindex(dim1=data['dim1'])
        self.assertDatasetIdentical(actual, expected)

        actual = data.reindex(dim1=data['dim1'].values)
        self.assertDatasetIdentical(actual, expected)

        actual = data.reindex(dim1=data['dim1'].to_index())
        self.assertDatasetIdentical(actual, expected)

        with self.assertRaisesRegexp(
                ValueError, 'cannot reindex or align along dimension'):
            data.reindex(dim1=data['dim1'][:5])

        expected = data.isel(dim2=slice(5))
        actual = data.reindex(dim2=data['dim2'][:5])
        self.assertDatasetIdentical(actual, expected)

        # test dict-like argument
        actual = data.reindex({'dim2': data['dim2']})
        expected = data
        self.assertDatasetIdentical(actual, expected)
        with self.assertRaisesRegexp(ValueError, 'cannot specify both'):
            data.reindex({'x': 0}, x=0)
        with self.assertRaisesRegexp(ValueError, 'dictionary'):
            data.reindex('foo')

        # invalid dimension
        with self.assertRaisesRegexp(ValueError, 'invalid reindex dim'):
            data.reindex(invalid=0)

        # out of order
        expected = data.sel(dim2=data['dim2'][:5:-1])
        actual = data.reindex(dim2=data['dim2'][:5:-1])
        self.assertDatasetIdentical(actual, expected)

        # regression test for #279
        expected = Dataset({'x': ('time', np.random.randn(5))},
                           {'time': range(5)})
        time2 = DataArray(np.arange(5), dims="time2")
        actual = expected.reindex(time=time2)
        self.assertDatasetIdentical(actual, expected)

        # another regression test
        ds = Dataset({'foo': (['x', 'y'], np.zeros((3, 4)))},
                     {'x': range(3), 'y': range(4)})
        expected = Dataset({'foo': (['x', 'y'], np.zeros((3, 2)))},
                           {'x': [0, 1, 3], 'y': [0, 1]})
        expected['foo'][-1] = np.nan
        actual = ds.reindex(x=[0, 1, 3], y=[0, 1])
        self.assertDatasetIdentical(expected, actual)

    def test_reindex_variables_copied(self):
        data = create_test_data()
        reindexed_data = data.reindex(copy=False)
        for k in data.variables:
            assert reindexed_data.variables[k] is not data.variables[k]

    def test_reindex_method(self):
        ds = Dataset({'x': ('y', [10, 20]), 'y': [0, 1]})
        y = [-0.5, 0.5, 1.5]
        actual = ds.reindex(y=y, method='backfill')
        expected = Dataset({'x': ('y', [10, 20, np.nan]), 'y': y})
        self.assertDatasetIdentical(expected, actual)

        if pd.__version__ >= '0.17':
            actual = ds.reindex(y=y, method='backfill', tolerance=0.1)
            expected = Dataset({'x': ('y', 3 * [np.nan]), 'y': y})
            self.assertDatasetIdentical(expected, actual)
        else:
            with self.assertRaisesRegexp(TypeError, 'tolerance'):
                ds.reindex(y=y, method='backfill', tolerance=0.1)

        actual = ds.reindex(y=y, method='pad')
        expected = Dataset({'x': ('y', [np.nan, 10, 20]), 'y': y})
        self.assertDatasetIdentical(expected, actual)

        alt = Dataset({'y': y})
        actual = ds.reindex_like(alt, method='pad')
        self.assertDatasetIdentical(expected, actual)

    def test_align(self):
        left = create_test_data()
        right = left.copy(deep=True)
        right['dim3'] = ('dim3', list('cdefghijkl'))
        right['var3'][:-2] = right['var3'][2:]
        right['var3'][-2:] = np.random.randn(*right['var3'][-2:].shape)
        right['numbers'][:-2] = right['numbers'][2:]
        right['numbers'][-2:] = -10

        intersection = list('cdefghij')
        union = list('abcdefghijkl')

        left2, right2 = align(left, right, join='inner')
        self.assertArrayEqual(left2['dim3'], intersection)
        self.assertDatasetIdentical(left2, right2)

        left2, right2 = align(left, right, join='outer')
        self.assertVariableEqual(left2['dim3'].variable, right2['dim3'].variable)
        self.assertArrayEqual(left2['dim3'], union)
        self.assertDatasetIdentical(left2.sel(dim3=intersection),
                                    right2.sel(dim3=intersection))
        self.assertTrue(np.isnan(left2['var3'][-2:]).all())
        self.assertTrue(np.isnan(right2['var3'][:2]).all())

        left2, right2 = align(left, right, join='left')
        self.assertVariableEqual(left2['dim3'].variable, right2['dim3'].variable)
        self.assertVariableEqual(left2['dim3'].variable, left['dim3'].variable)
        self.assertDatasetIdentical(left2.sel(dim3=intersection),
                                    right2.sel(dim3=intersection))
        self.assertTrue(np.isnan(right2['var3'][:2]).all())

        left2, right2 = align(left, right, join='right')
        self.assertVariableEqual(left2['dim3'].variable, right2['dim3'].variable)
        self.assertVariableEqual(left2['dim3'].variable, right['dim3'].variable)
        self.assertDatasetIdentical(left2.sel(dim3=intersection),
                                    right2.sel(dim3=intersection))
        self.assertTrue(np.isnan(left2['var3'][-2:]).all())

        with self.assertRaisesRegexp(ValueError, 'invalid value for join'):
            align(left, right, join='foobar')
        with self.assertRaises(TypeError):
            align(left, right, foo='bar')

    def test_align_exact(self):
        left = xr.Dataset(coords={'x': [0, 1]})
        right = xr.Dataset(coords={'x': [1, 2]})

        left1, left2 = xr.align(left, left, join='exact')
        self.assertDatasetIdentical(left1, left)
        self.assertDatasetIdentical(left2, left)

        with self.assertRaisesRegexp(ValueError, 'indexes .* not equal'):
            xr.align(left, right, join='exact')

    def test_align_exclude(self):
        x = Dataset({'foo': DataArray([[1, 2], [3, 4]], dims=['x', 'y'],
                                      coords={'x': [1, 2], 'y': [3, 4]})})
        y = Dataset({'bar': DataArray([[1, 2], [3, 4]], dims=['x', 'y'],
                                      coords={'x': [1, 3], 'y': [5, 6]})})
        x2, y2 = align(x, y, exclude=['y'], join='outer')

        expected_x2 = Dataset(
            {'foo': DataArray([[1, 2], [3, 4], [np.nan, np.nan]],
                              dims=['x', 'y'],
                              coords={'x': [1, 2, 3], 'y': [3, 4]})})
        expected_y2 = Dataset(
            {'bar': DataArray([[1, 2], [np.nan, np.nan], [3, 4]],
                              dims=['x', 'y'],
                              coords={'x': [1, 2, 3], 'y': [5, 6]})})
        self.assertDatasetIdentical(expected_x2, x2)
        self.assertDatasetIdentical(expected_y2, y2)

    def test_align_nocopy(self):
        x = Dataset({'foo': DataArray([1, 2, 3], coords=[('x', [1, 2, 3])])})
        y = Dataset({'foo': DataArray([1, 2], coords=[('x', [1, 2])])})
        expected_x2 = x
        expected_y2 = Dataset({'foo': DataArray([1, 2, np.nan],
                                                 coords=[('x', [1, 2, 3])])})

        x2, y2 = align(x, y, copy=False, join='outer')
        self.assertDatasetIdentical(expected_x2, x2)
        self.assertDatasetIdentical(expected_y2, y2)
        assert source_ndarray(x['foo'].data) is source_ndarray(x2['foo'].data)

        x2, y2 = align(x, y, copy=True, join='outer')
        self.assertDatasetIdentical(expected_x2, x2)
        self.assertDatasetIdentical(expected_y2, y2)
        assert source_ndarray(x['foo'].data) is not source_ndarray(x2['foo'].data)

    def test_align_indexes(self):
        x = Dataset({'foo': DataArray([1, 2, 3], dims='x',
                    coords=[('x', [1, 2, 3])])})
        x2, = align(x, indexes={'x': [2, 3, 1]})
        expected_x2 = Dataset({'foo': DataArray([2, 3, 1], dims='x',
                              coords={'x': [2, 3, 1]})})
        self.assertDatasetIdentical(expected_x2, x2)

    def test_align_non_unique(self):
        x = Dataset({'foo': ('x', [3, 4, 5]), 'x': [0, 0, 1]})
        x1, x2 = align(x, x)
        assert x1.identical(x) and x2.identical(x)

        y = Dataset({'bar': ('x', [6, 7]), 'x': [0, 1]})
        with self.assertRaisesRegexp(ValueError, 'cannot reindex or align'):
            align(x, y)

    def test_broadcast(self):
        ds = Dataset({'foo': 0, 'bar': ('x', [1]), 'baz': ('y', [2, 3])},
                     {'c': ('x', [4])})
        expected = Dataset({'foo': (('x', 'y'), [[0, 0]]),
                            'bar': (('x', 'y'), [[1, 1]]),
                            'baz': (('x', 'y'), [[2, 3]])},
                            {'c': ('x', [4])})
        actual, = broadcast(ds)
        self.assertDatasetIdentical(expected, actual)

        ds_x = Dataset({'foo': ('x', [1])})
        ds_y = Dataset({'bar': ('y', [2, 3])})
        expected_x = Dataset({'foo': (('x', 'y'), [[1, 1]])})
        expected_y = Dataset({'bar': (('x', 'y'), [[2, 3]])})
        actual_x, actual_y = broadcast(ds_x, ds_y)
        self.assertDatasetIdentical(expected_x, actual_x)
        self.assertDatasetIdentical(expected_y, actual_y)

        array_y = ds_y['bar']
        expected_y = expected_y['bar']
        actual_x, actual_y = broadcast(ds_x, array_y)
        self.assertDatasetIdentical(expected_x, actual_x)
        self.assertDataArrayIdentical(expected_y, actual_y)

    def test_broadcast_nocopy(self):
        # Test that data is not copied if not needed
        x = Dataset({'foo': (('x', 'y'), [[1, 1]])})
        y = Dataset({'bar': ('y', [2, 3])})

        actual_x, = broadcast(x)
        self.assertDatasetIdentical(x, actual_x)
        assert source_ndarray(actual_x['foo'].data) is source_ndarray(x['foo'].data)

        actual_x, actual_y = broadcast(x, y)
        self.assertDatasetIdentical(x, actual_x)
        assert source_ndarray(actual_x['foo'].data) is source_ndarray(x['foo'].data)

    def test_broadcast_exclude(self):
        x = Dataset({
            'foo': DataArray([[1, 2],[3, 4]], dims=['x', 'y'], coords={'x': [1, 2], 'y': [3, 4]}),
            'bar': DataArray(5),
        })
        y = Dataset({
            'foo': DataArray([[1, 2]], dims=['z', 'y'], coords={'z': [1], 'y': [5, 6]}),
        })
        x2, y2 = broadcast(x, y, exclude=['y'])

        expected_x2 = Dataset({
            'foo': DataArray([[[1, 2]], [[3, 4]]], dims=['x', 'z', 'y'], coords={'z': [1], 'x': [1, 2], 'y': [3, 4]}),
            'bar': DataArray([[5], [5]], dims=['x', 'z'], coords={'x': [1, 2], 'z': [1]}),
        })
        expected_y2 = Dataset({
            'foo': DataArray([[[1, 2]], [[1, 2]]], dims=['x', 'z', 'y'], coords={'z': [1], 'x': [1, 2], 'y': [5, 6]}),
        })
        self.assertDatasetIdentical(expected_x2, x2)
        self.assertDatasetIdentical(expected_y2, y2)

    def test_broadcast_misaligned(self):
        x = Dataset({'foo': DataArray([1, 2, 3], coords=[('x', [-1, -2, -3])])})
        y = Dataset({'bar': DataArray([[1, 2], [3, 4]], dims=['y', 'x'],
                                      coords={'y': [1, 2], 'x': [10, -3]})})
        x2, y2 = broadcast(x, y)
        expected_x2 = Dataset(
            {'foo': DataArray([[3, 3], [2, 2], [1, 1], [np.nan, np.nan]],
                              dims=['x', 'y'],
                              coords={'y': [1, 2], 'x': [-3, -2, -1, 10]})})
        expected_y2 = Dataset(
            {'bar': DataArray(
                [[2, 4], [np.nan, np.nan], [np.nan, np.nan], [1, 3]],
                dims=['x', 'y'], coords={'y': [1, 2], 'x': [-3, -2, -1, 10]})})
        self.assertDatasetIdentical(expected_x2, x2)
        self.assertDatasetIdentical(expected_y2, y2)

    def test_variable_indexing(self):
        data = create_test_data()
        v = data['var1']
        d1 = data['dim1']
        d2 = data['dim2']
        self.assertVariableEqual(v, v[d1.values])
        self.assertVariableEqual(v, v[d1])
        self.assertVariableEqual(v[:3], v[d1 < 3])
        self.assertVariableEqual(v[:, 3:], v[:, d2 >= 1.5])
        self.assertVariableEqual(v[:3, 3:], v[d1 < 3, d2 >= 1.5])
        self.assertVariableEqual(v[:3, :2], v[range(3), range(2)])
        self.assertVariableEqual(v[:3, :2], v.loc[d1[:3], d2[:2]])

    def test_drop_variables(self):
        data = create_test_data()

        self.assertDatasetIdentical(data, data.drop([]))

        expected = Dataset(dict((k, data[k]) for k in data if k != 'time'))
        actual = data.drop('time')
        self.assertDatasetIdentical(expected, actual)
        actual = data.drop(['time'])
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaisesRegexp(ValueError, 'cannot be found'):
            data.drop('not_found_here')

    def test_drop_index_labels(self):
        data = Dataset({'A': (['x', 'y'], np.random.randn(2, 3)),
                        'x': ['a', 'b']})

        actual = data.drop(['a'], 'x')
        expected = data.isel(x=[1])
        self.assertDatasetIdentical(expected, actual)

        actual = data.drop(['a', 'b'], 'x')
        expected = data.isel(x=slice(0, 0))
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaises(ValueError):
            # not contained in axis
            data.drop(['c'], dim='x')

        with self.assertRaisesRegexp(
                ValueError, 'does not have coordinate labels'):
            data.drop(1, 'y')

    def test_copy(self):
        data = create_test_data()

        for copied in [data.copy(deep=False), copy(data)]:
            self.assertDatasetIdentical(data, copied)
            # Note: IndexVariable objects with string dtype are always
            # copied because of xarray.core.util.safe_cast_to_index.
            # Limiting the test to data variables.
            for k in data.data_vars:
                v0 = data.variables[k]
                v1 = copied.variables[k]
                assert source_ndarray(v0.data) is source_ndarray(v1.data)
            copied['foo'] = ('z', np.arange(5))
            self.assertNotIn('foo', data)

        for copied in [data.copy(deep=True), deepcopy(data)]:
            self.assertDatasetIdentical(data, copied)
            for k in data:
                v0 = data.variables[k]
                v1 = copied.variables[k]
                self.assertIsNot(v0, v1)

    def test_rename(self):
        data = create_test_data()
        newnames = {'var1': 'renamed_var1', 'dim2': 'renamed_dim2'}
        renamed = data.rename(newnames)

        variables = OrderedDict(data.variables)
        for k, v in iteritems(newnames):
            variables[v] = variables.pop(k)

        for k, v in iteritems(variables):
            dims = list(v.dims)
            for name, newname in iteritems(newnames):
                if name in dims:
                    dims[dims.index(name)] = newname

            self.assertVariableEqual(Variable(dims, v.values, v.attrs),
                                     renamed[k].variable.to_base_variable())
            self.assertEqual(v.encoding, renamed[k].encoding)
            self.assertEqual(type(v), type(renamed.variables[k]))

        self.assertTrue('var1' not in renamed)
        self.assertTrue('dim2' not in renamed)

        with self.assertRaisesRegexp(ValueError, "cannot rename 'not_a_var'"):
            data.rename({'not_a_var': 'nada'})

        with self.assertRaisesRegexp(ValueError, "'var1' conflicts"):
            data.rename({'var2': 'var1'})

        # verify that we can rename a variable without accessing the data
        var1 = data['var1']
        data['var1'] = (var1.dims, InaccessibleArray(var1.values))
        renamed = data.rename(newnames)
        with self.assertRaises(UnexpectedDataAccess):
            renamed['renamed_var1'].values

    def test_rename_old_name(self):
        # regtest for GH1477
        data = create_test_data()

        with self.assertRaisesRegexp(ValueError, "'samecol' conflicts"):
            data.rename({'var1': 'samecol', 'var2': 'samecol'})

        # This shouldn't cause any problems.
        data.rename({'var1': 'var2', 'var2': 'var1'})

    def test_rename_same_name(self):
        data = create_test_data()
        newnames = {'var1': 'var1', 'dim2': 'dim2'}
        renamed = data.rename(newnames)
        self.assertDatasetIdentical(renamed, data)

    def test_rename_inplace(self):
        times = pd.date_range('2000-01-01', periods=3)
        data = Dataset({'z': ('x', [2, 3, 4]), 't': ('t', times)})
        copied = data.copy()
        renamed = data.rename({'x': 'y'})
        data.rename({'x': 'y'}, inplace=True)
        self.assertDatasetIdentical(data, renamed)
        self.assertFalse(data.equals(copied))
        self.assertEquals(data.dims, {'y': 3, 't': 3})
        # check virtual variables
        self.assertArrayEqual(data['t.dayofyear'], [1, 2, 3])

    def test_swap_dims(self):
        original = Dataset({'x': [1, 2, 3], 'y': ('x', list('abc')), 'z': 42})
        expected = Dataset({'z': 42}, {'x': ('y', [1, 2, 3]), 'y': list('abc')})
        actual = original.swap_dims({'x': 'y'})
        self.assertDatasetIdentical(expected, actual)
        self.assertIsInstance(actual.variables['y'], IndexVariable)
        self.assertIsInstance(actual.variables['x'], Variable)

        roundtripped = actual.swap_dims({'y': 'x'})
        self.assertDatasetIdentical(original.set_coords('y'), roundtripped)

        actual = original.copy()
        actual.swap_dims({'x': 'y'}, inplace=True)
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaisesRegexp(ValueError, 'cannot swap'):
            original.swap_dims({'y': 'x'})
        with self.assertRaisesRegexp(ValueError, 'replacement dimension'):
            original.swap_dims({'x': 'z'})

    def test_expand_dims_error(self):
        original = Dataset({'x': ('a', np.random.randn(3)),
                            'y': (['b', 'a'], np.random.randn(4, 3)),
                            'z': ('a', np.random.randn(3))},
                           coords={'a': np.linspace(0, 1, 3),
                                   'b': np.linspace(0, 1, 4),
                                   'c': np.linspace(0, 1, 5)},
                           attrs={'key': 'entry'})

        with self.assertRaisesRegexp(ValueError, 'already exists'):
            original.expand_dims(dim=['x'])

        # Make sure it raises true error also for non-dimensional coordinates
        # which has dimension.
        original.set_coords('z', inplace=True)
        with self.assertRaisesRegexp(ValueError, 'already exists'):
            original.expand_dims(dim=['z'])

    def test_expand_dims(self):
        original = Dataset({'x': ('a', np.random.randn(3)),
                            'y': (['b', 'a'], np.random.randn(4, 3))},
                           coords={'a': np.linspace(0, 1, 3),
                                   'b': np.linspace(0, 1, 4),
                                   'c': np.linspace(0, 1, 5)},
                           attrs={'key': 'entry'})

        actual = original.expand_dims(['z'], [1])
        expected = Dataset({'x': original['x'].expand_dims('z', 1),
                            'y': original['y'].expand_dims('z', 1)},
                           coords={'a': np.linspace(0, 1, 3),
                                   'b': np.linspace(0, 1, 4),
                                   'c': np.linspace(0, 1, 5)},
                           attrs={'key': 'entry'})
        self.assertDatasetIdentical(expected, actual)
        # make sure squeeze restores the original data set.
        roundtripped = actual.squeeze('z')
        self.assertDatasetIdentical(original, roundtripped)

        # another test with a negative axis
        actual = original.expand_dims(['z'], [-1])
        expected = Dataset({'x': original['x'].expand_dims('z', -1),
                            'y': original['y'].expand_dims('z', -1)},
                           coords={'a': np.linspace(0, 1, 3),
                                   'b': np.linspace(0, 1, 4),
                                   'c': np.linspace(0, 1, 5)},
                           attrs={'key': 'entry'})
        self.assertDatasetIdentical(expected, actual)
        # make sure squeeze restores the original data set.
        roundtripped = actual.squeeze('z')
        self.assertDatasetIdentical(original, roundtripped)

    def test_set_index(self):
        expected = create_test_multiindex()
        mindex = expected['x'].to_index()
        indexes = [mindex.get_level_values(n) for n in mindex.names]
        coords = {idx.name: ('x', idx) for idx in indexes}
        ds = Dataset({}, coords=coords)

        obj = ds.set_index(x=mindex.names)
        self.assertDatasetIdentical(obj, expected)

        ds.set_index(x=mindex.names, inplace=True)
        self.assertDatasetIdentical(ds, expected)

    def test_reset_index(self):
        ds = create_test_multiindex()
        mindex = ds['x'].to_index()
        indexes = [mindex.get_level_values(n) for n in mindex.names]
        coords = {idx.name: ('x', idx) for idx in indexes}
        expected = Dataset({}, coords=coords)

        obj = ds.reset_index('x')
        self.assertDatasetIdentical(obj, expected)

        ds.reset_index('x', inplace=True)
        self.assertDatasetIdentical(ds, expected)

    def test_reorder_levels(self):
        ds = create_test_multiindex()
        mindex = ds['x'].to_index()
        midx = mindex.reorder_levels(['level_2', 'level_1'])
        expected = Dataset({}, coords={'x': midx})

        reindexed = ds.reorder_levels(x=['level_2', 'level_1'])
        self.assertDatasetIdentical(reindexed, expected)

        ds.reorder_levels(x=['level_2', 'level_1'], inplace=True)
        self.assertDatasetIdentical(ds, expected)

        ds = Dataset({}, coords={'x': [1, 2]})
        with self.assertRaisesRegexp(ValueError, 'has no MultiIndex'):
            ds.reorder_levels(x=['level_1', 'level_2'])

    def test_stack(self):
        ds = Dataset({'a': ('x', [0, 1]),
                      'b': (('x', 'y'), [[0, 1], [2, 3]]),
                      'y': ['a', 'b']})

        exp_index = pd.MultiIndex.from_product([[0, 1], ['a', 'b']],
                                               names=['x', 'y'])
        expected = Dataset({'a': ('z', [0, 0, 1, 1]),
                            'b': ('z', [0, 1, 2, 3]),
                            'z': exp_index})
        actual = ds.stack(z=['x', 'y'])
        self.assertDatasetIdentical(expected, actual)

        exp_index = pd.MultiIndex.from_product([['a', 'b'], [0, 1]],
                                               names=['y', 'x'])
        expected = Dataset({'a': ('z', [0, 1, 0, 1]),
                            'b': ('z', [0, 2, 1, 3]),
                            'z': exp_index})
        actual = ds.stack(z=['y', 'x'])
        self.assertDatasetIdentical(expected, actual)

    def test_unstack(self):
        index = pd.MultiIndex.from_product([[0, 1], ['a', 'b']],
                                           names=['x', 'y'])
        ds = Dataset({'b': ('z', [0, 1, 2, 3]), 'z': index})
        expected = Dataset({'b': (('x', 'y'), [[0, 1], [2, 3]]),
                            'x': [0, 1],
                            'y': ['a', 'b']})
        actual = ds.unstack('z')
        self.assertDatasetIdentical(actual, expected)

    def test_unstack_errors(self):
        ds = Dataset({'x': [1, 2, 3]})
        with self.assertRaisesRegexp(ValueError, 'invalid dimension'):
            ds.unstack('foo')
        with self.assertRaisesRegexp(ValueError, 'does not have a MultiIndex'):
            ds.unstack('x')

    def test_stack_unstack(self):
        ds = Dataset({'a': ('x', [0, 1]),
                      'b': (('x', 'y'), [[0, 1], [2, 3]]),
                      'x': [0, 1],
                      'y': ['a', 'b']})
        actual = ds.stack(z=['x', 'y']).unstack('z')
        assert actual.broadcast_equals(ds)

        actual = ds[['b']].stack(z=['x', 'y']).unstack('z')
        assert actual.identical(ds[['b']])

    def test_update(self):
        data = create_test_data(seed=0)
        expected = data.copy()
        var2 = Variable('dim1', np.arange(8))
        actual = data.update({'var2': var2})
        expected['var2'] = var2
        self.assertDatasetIdentical(expected, actual)

        actual = data.copy()
        actual_result = actual.update(data, inplace=True)
        self.assertIs(actual_result, actual)
        self.assertDatasetIdentical(expected, actual)

        actual = data.update(data, inplace=False)
        expected = data
        self.assertIsNot(actual, expected)
        self.assertDatasetIdentical(expected, actual)

        other = Dataset(attrs={'new': 'attr'})
        actual = data.copy()
        actual.update(other)
        self.assertDatasetIdentical(expected, actual)

    def test_update_auto_align(self):
        ds = Dataset({'x': ('t', [3, 4])}, {'t': [0, 1]})

        expected = Dataset({'x': ('t', [3, 4]), 'y': ('t', [np.nan, 5])},
                           {'t': [0, 1]})
        actual = ds.copy()
        other = {'y': ('t', [5]), 't': [1]}
        with self.assertRaisesRegexp(ValueError, 'conflicting sizes'):
            actual.update(other)
        actual.update(Dataset(other))
        self.assertDatasetIdentical(expected, actual)

        actual = ds.copy()
        other = Dataset({'y': ('t', [5]), 't': [100]})
        actual.update(other)
        expected = Dataset({'x': ('t', [3, 4]), 'y': ('t', [np.nan] * 2)},
                           {'t': [0, 1]})
        self.assertDatasetIdentical(expected, actual)

    def test_getitem(self):
        data = create_test_data()
        self.assertIsInstance(data['var1'], DataArray)
        self.assertVariableEqual(data['var1'].variable, data.variables['var1'])
        with self.assertRaises(KeyError):
            data['notfound']
        with self.assertRaises(KeyError):
            data[['var1', 'notfound']]

        actual = data[['var1', 'var2']]
        expected = Dataset({'var1': data['var1'], 'var2': data['var2']})
        self.assertDatasetEqual(expected, actual)

        actual = data['numbers']
        expected = DataArray(data['numbers'].variable,
                             {'dim3': data['dim3'],
                              'numbers': data['numbers']},
                             dims='dim3', name='numbers')
        self.assertDataArrayIdentical(expected, actual)

        actual = data[dict(dim1=0)]
        expected = data.isel(dim1=0)
        self.assertDatasetIdentical(expected, actual)

    def test_getitem_hashable(self):
        data = create_test_data()
        data[(3, 4)] = data['var1'] + 1
        expected = data['var1'] + 1
        expected.name = (3, 4)
        self.assertDataArrayIdentical(expected, data[(3, 4)])
        with self.assertRaisesRegexp(KeyError, "('var1', 'var2')"):
            data[('var1', 'var2')]

    def test_virtual_variables_default_coords(self):
        dataset = Dataset({'foo': ('x', range(10))})
        expected = DataArray(range(10), dims='x', name='x')
        actual = dataset['x']
        self.assertDataArrayIdentical(expected, actual)
        self.assertIsInstance(actual.variable, IndexVariable)

        actual = dataset[['x', 'foo']]
        expected = dataset.assign_coords(x=range(10))
        self.assertDatasetIdentical(expected, actual)

    def test_virtual_variables_time(self):
        # access virtual variables
        data = create_test_data()
        expected = DataArray(1 + np.arange(20), coords=[data['time']],
                             dims='time', name='dayofyear')
        self.assertDataArrayIdentical(expected, data['time.dayofyear'])
        self.assertArrayEqual(data['time.month'].values,
                              data.variables['time'].to_index().month)
        self.assertArrayEqual(data['time.season'].values, 'DJF')
        # test virtual variable math
        self.assertArrayEqual(data['time.dayofyear'] + 1, 2 + np.arange(20))
        self.assertArrayEqual(np.sin(data['time.dayofyear']),
                              np.sin(1 + np.arange(20)))
        # ensure they become coordinates
        expected = Dataset({}, {'dayofyear': data['time.dayofyear']})
        actual = data[['time.dayofyear']]
        self.assertDatasetEqual(expected, actual)
        # non-coordinate variables
        ds = Dataset({'t': ('x', pd.date_range('2000-01-01', periods=3))})
        self.assertTrue((ds['t.year'] == 2000).all())

    def test_virtual_variable_same_name(self):
        # regression test for GH367
        times = pd.date_range('2000-01-01', freq='H', periods=5)
        data = Dataset({'time': times})
        actual = data['time.time']
        expected = DataArray(times.time, [('time', times)], name='time')
        self.assertDataArrayIdentical(actual, expected)

    def test_virtual_variable_multiindex(self):
        # access multi-index levels as virtual variables
        data = create_test_multiindex()
        expected = DataArray(['a', 'a', 'b', 'b'], name='level_1',
                             coords=[data['x'].to_index()], dims='x')
        self.assertDataArrayIdentical(expected, data['level_1'])

        # combine multi-index level and datetime
        dr_index = pd.date_range('1/1/2011', periods=4, freq='H')
        mindex = pd.MultiIndex.from_arrays([['a', 'a', 'b', 'b'], dr_index],
                                           names=('level_str', 'level_date'))
        data = Dataset({}, {'x': mindex})
        expected = DataArray(mindex.get_level_values('level_date').hour,
                             name='hour', coords=[mindex], dims='x')
        self.assertDataArrayIdentical(expected, data['level_date.hour'])

        # attribute style access
        self.assertDataArrayIdentical(data.level_str, data['level_str'])

    def test_time_season(self):
        ds = Dataset({'t': pd.date_range('2000-01-01', periods=12, freq='M')})
        expected = ['DJF'] * 2 + ['MAM'] * 3 + ['JJA'] * 3 + ['SON'] * 3 + ['DJF']
        self.assertArrayEqual(expected, ds['t.season'])

    def test_slice_virtual_variable(self):
        data = create_test_data()
        self.assertVariableEqual(data['time.dayofyear'][:10].variable,
                                 Variable(['time'], 1 + np.arange(10)))
        self.assertVariableEqual(data['time.dayofyear'][0].variable, Variable([], 1))

    def test_setitem(self):
        # assign a variable
        var = Variable(['dim1'], np.random.randn(8))
        data1 = create_test_data()
        data1['A'] = var
        data2 = data1.copy()
        data2['A'] = var
        self.assertDatasetIdentical(data1, data2)
        # assign a dataset array
        dv = 2 * data2['A']
        data1['B'] = dv.variable
        data2['B'] = dv
        self.assertDatasetIdentical(data1, data2)
        # can't assign an ND array without dimensions
        with self.assertRaisesRegexp(ValueError,
                                     'without explicit dimension names'):
            data2['C'] = var.values.reshape(2, 4)
        # but can assign a 1D array
        data1['C'] = var.values
        data2['C'] = ('C', var.values)
        self.assertDatasetIdentical(data1, data2)
        # can assign a scalar
        data1['scalar'] = 0
        data2['scalar'] = ([], 0)
        self.assertDatasetIdentical(data1, data2)
        # can't use the same dimension name as a scalar var
        with self.assertRaisesRegexp(ValueError, 'already exists as a scalar'):
            data1['newvar'] = ('scalar', [3, 4, 5])
        # can't resize a used dimension
        with self.assertRaisesRegexp(ValueError, 'arguments without labels'):
            data1['dim1'] = data1['dim1'][:5]
        # override an existing value
        data1['A'] = 3 * data2['A']
        self.assertVariableEqual(data1['A'], 3 * data2['A'])

        with self.assertRaises(NotImplementedError):
            data1[{'x': 0}] = 0

    def test_setitem_pandas(self):

        ds = self.make_example_math_dataset()
        ds['x'] = np.arange(3)
        ds_copy = ds.copy()
        ds_copy['bar'] = ds['bar'].to_pandas()

        self.assertDatasetEqual(ds, ds_copy)

    def test_setitem_auto_align(self):
        ds = Dataset()
        ds['x'] = ('y', range(3))
        ds['y'] = 1 + np.arange(3)
        expected = Dataset({'x': ('y', range(3)), 'y': 1 + np.arange(3)})
        self.assertDatasetIdentical(ds, expected)

        ds['y'] = DataArray(range(3), dims='y')
        expected = Dataset({'x': ('y', range(3))}, {'y': range(3)})
        self.assertDatasetIdentical(ds, expected)

        ds['x'] = DataArray([1, 2], coords=[('y', [0, 1])])
        expected = Dataset({'x': ('y', [1, 2, np.nan])}, {'y': range(3)})
        self.assertDatasetIdentical(ds, expected)

        ds['x'] = 42
        expected = Dataset({'x': 42, 'y': range(3)})
        self.assertDatasetIdentical(ds, expected)

        ds['x'] = DataArray([4, 5, 6, 7], coords=[('y', [0, 1, 2, 3])])
        expected = Dataset({'x': ('y', [4, 5, 6])}, {'y': range(3)})
        self.assertDatasetIdentical(ds, expected)

    def test_setitem_align_new_indexes(self):
        ds = Dataset({'foo': ('x', [1, 2, 3])}, {'x': [0, 1, 2]})
        ds['bar'] = DataArray([2, 3, 4], [('x', [1, 2, 3])])
        expected = Dataset({'foo': ('x', [1, 2, 3]),
                            'bar': ('x', [np.nan, 2, 3])},
                           {'x': [0, 1, 2]})
        self.assertDatasetIdentical(ds, expected)

    def test_assign(self):
        ds = Dataset()
        actual = ds.assign(x = [0, 1, 2], y = 2)
        expected = Dataset({'x': [0, 1, 2], 'y': 2})
        self.assertDatasetIdentical(actual, expected)
        self.assertEqual(list(actual), ['x', 'y'])
        self.assertDatasetIdentical(ds, Dataset())

        actual = actual.assign(y = lambda ds: ds.x ** 2)
        expected = Dataset({'y': ('x', [0, 1, 4]), 'x': [0, 1, 2]})
        self.assertDatasetIdentical(actual, expected)

        actual = actual.assign_coords(z = 2)
        expected = Dataset({'y': ('x', [0, 1, 4])}, {'z': 2, 'x': [0, 1, 2]})
        self.assertDatasetIdentical(actual, expected)

        ds = Dataset({'a': ('x', range(3))}, {'b': ('x', ['A'] * 2 + ['B'])})
        actual = ds.groupby('b').assign(c = lambda ds: 2 * ds.a)
        expected = ds.merge({'c': ('x', [0, 2, 4])})
        self.assertDatasetIdentical(actual, expected)

        actual = ds.groupby('b').assign(c = lambda ds: ds.a.sum())
        expected = ds.merge({'c': ('x', [1, 1, 2])})
        self.assertDatasetIdentical(actual, expected)

        actual = ds.groupby('b').assign_coords(c = lambda ds: ds.a.sum())
        expected = expected.set_coords('c')
        self.assertDatasetIdentical(actual, expected)

    def test_assign_attrs(self):
        expected = Dataset(attrs=dict(a=1, b=2))
        new = Dataset()
        actual = new.assign_attrs(a=1, b=2)
        self.assertDatasetIdentical(actual, expected)
        self.assertEqual(new.attrs, {})

        expected.attrs['c'] = 3
        new_actual = actual.assign_attrs({'c': 3})
        self.assertDatasetIdentical(new_actual, expected)
        self.assertEqual(actual.attrs, dict(a=1, b=2))

    def test_assign_multiindex_level(self):
        data = create_test_multiindex()
        with self.assertRaisesRegexp(ValueError, 'conflicting MultiIndex'):
            data.assign(level_1=range(4))
            data.assign_coords(level_1=range(4))

    def test_setitem_original_non_unique_index(self):
        # regression test for GH943
        original = Dataset({'data': ('x', np.arange(5))},
                           coords={'x': [0, 1, 2, 0, 1]})
        expected = Dataset({'data': ('x', np.arange(5))}, {'x': range(5)})

        actual = original.copy()
        actual['x'] = list(range(5))
        self.assertDatasetIdentical(actual, expected)

        actual = original.copy()
        actual['x'] = ('x', list(range(5)))
        self.assertDatasetIdentical(actual, expected)

        actual = original.copy()
        actual.coords['x'] = list(range(5))
        self.assertDatasetIdentical(actual, expected)

    def test_setitem_both_non_unique_index(self):
        # regression test for GH956
        names = ['joaquin', 'manolo', 'joaquin']
        values = np.random.randint(0, 256, (3, 4, 4))
        array = DataArray(values, dims=['name', 'row', 'column'],
                          coords=[names, range(4), range(4)])
        expected = Dataset({'first': array, 'second': array})
        actual = array.rename('first').to_dataset()
        actual['second'] = array
        self.assertDatasetIdentical(expected, actual)

    def test_setitem_multiindex_level(self):
        data = create_test_multiindex()
        with self.assertRaisesRegexp(ValueError, 'conflicting MultiIndex'):
            data['level_1'] = range(4)

    def test_delitem(self):
        data = create_test_data()
        all_items = set(data)
        self.assertItemsEqual(data, all_items)
        del data['var1']
        self.assertItemsEqual(data, all_items - set(['var1']))
        del data['numbers']
        self.assertItemsEqual(data, all_items - set(['var1', 'numbers']))
        self.assertNotIn('numbers', data.coords)

    def test_squeeze(self):
        data = Dataset({'foo': (['x', 'y', 'z'], [[[1], [2]]])})
        for args in [[], [['x']], [['x', 'z']]]:
            def get_args(v):
                return [set(args[0]) & set(v.dims)] if args else []
            expected = Dataset(dict((k, v.squeeze(*get_args(v)))
                                    for k, v in iteritems(data.variables)))
            expected.set_coords(data.coords, inplace=True)
            self.assertDatasetIdentical(expected, data.squeeze(*args))
        # invalid squeeze
        with self.assertRaisesRegexp(ValueError, 'cannot select a dimension'):
            data.squeeze('y')

    def test_squeeze_drop(self):
        data = Dataset({'foo': ('x', [1])}, {'x': [0]})
        expected = Dataset({'foo': 1})
        selected = data.squeeze(drop=True)
        self.assertDatasetIdentical(expected, selected)

        expected = Dataset({'foo': 1}, {'x': 0})
        selected = data.squeeze(drop=False)
        self.assertDatasetIdentical(expected, selected)

        data = Dataset({'foo': (('x', 'y'), [[1]])}, {'x': [0], 'y': [0]})
        expected = Dataset({'foo': 1})
        selected = data.squeeze(drop=True)
        self.assertDatasetIdentical(expected, selected)

        expected = Dataset({'foo': ('x', [1])}, {'x': [0]})
        selected = data.squeeze(dim='y', drop=True)
        self.assertDatasetIdentical(expected, selected)

        data = Dataset({'foo': (('x',), [])}, {'x': []})
        selected = data.squeeze(drop=True)
        self.assertDatasetIdentical(data, selected)

    def test_groupby(self):
        data = Dataset({'z': (['x', 'y'], np.random.randn(3, 5))},
                       {'x': ('x', list('abc')),
                        'c': ('x', [0, 1, 0]),
                        'y': range(5)})
        groupby = data.groupby('x')
        self.assertEqual(len(groupby), 3)
        expected_groups = {'a': 0, 'b': 1, 'c': 2}
        self.assertEqual(groupby.groups, expected_groups)
        expected_items = [('a', data.isel(x=0)),
                          ('b', data.isel(x=1)),
                          ('c', data.isel(x=2))]
        for actual, expected in zip(groupby, expected_items):
            self.assertEqual(actual[0], expected[0])
            self.assertDatasetEqual(actual[1], expected[1])

        identity = lambda x: x
        for k in ['x', 'c', 'y']:
            actual = data.groupby(k, squeeze=False).apply(identity)
            self.assertDatasetEqual(data, actual)

    def test_groupby_returns_new_type(self):
        data = Dataset({'z': (['x', 'y'], np.random.randn(3, 5))})

        actual = data.groupby('x').apply(lambda ds: ds['z'])
        expected = data['z']
        self.assertDataArrayIdentical(expected, actual)

        actual = data['z'].groupby('x').apply(lambda x: x.to_dataset())
        expected = data
        self.assertDatasetIdentical(expected, actual)

    def test_groupby_iter(self):
        data = create_test_data()
        for n, (t, sub) in enumerate(list(data.groupby('dim1'))[:3]):
            self.assertEqual(data['dim1'][n], t)
            self.assertVariableEqual(data['var1'][n], sub['var1'])
            self.assertVariableEqual(data['var2'][n], sub['var2'])
            self.assertVariableEqual(data['var3'][:, n], sub['var3'])

    def test_groupby_errors(self):
        data = create_test_data()
        with self.assertRaisesRegexp(TypeError, '`group` must be'):
            data.groupby(np.arange(10))
        with self.assertRaisesRegexp(ValueError, 'length does not match'):
            data.groupby(data['dim1'][:3])
        with self.assertRaisesRegexp(TypeError, "`group` must be"):
            data.groupby(data.coords['dim1'].to_index())

    def test_groupby_reduce(self):
        data = Dataset({'xy': (['x', 'y'], np.random.randn(3, 4)),
                        'xonly': ('x', np.random.randn(3)),
                        'yonly': ('y', np.random.randn(4)),
                        'letters': ('y', ['a', 'a', 'b', 'b'])})

        expected = data.mean('y')
        expected['yonly'] = expected['yonly'].variable.set_dims({'x': 3})
        actual = data.groupby('x').mean()
        self.assertDatasetAllClose(expected, actual)

        actual = data.groupby('x').mean('y')
        self.assertDatasetAllClose(expected, actual)

        letters = data['letters']
        expected = Dataset({'xy': data['xy'].groupby(letters).mean(),
                            'xonly': (data['xonly'].mean().variable
                                      .set_dims({'letters': 2})),
                            'yonly': data['yonly'].groupby(letters).mean()})
        actual = data.groupby('letters').mean()
        self.assertDatasetAllClose(expected, actual)

    def test_groupby_math(self):
        reorder_dims = lambda x: x.transpose('dim1', 'dim2', 'dim3', 'time')

        ds = create_test_data()
        ds['dim1'] = ds['dim1']
        for squeeze in [True, False]:
            grouped = ds.groupby('dim1', squeeze=squeeze)

            expected = reorder_dims(ds + ds.coords['dim1'])
            actual = grouped + ds.coords['dim1']
            self.assertDatasetIdentical(expected, reorder_dims(actual))

            actual = ds.coords['dim1'] + grouped
            self.assertDatasetIdentical(expected, reorder_dims(actual))

            ds2 = 2 * ds
            expected = reorder_dims(ds + ds2)
            actual = grouped + ds2
            self.assertDatasetIdentical(expected, reorder_dims(actual))

            actual = ds2 + grouped
            self.assertDatasetIdentical(expected, reorder_dims(actual))

        grouped = ds.groupby('numbers')
        zeros = DataArray([0, 0, 0, 0], [('numbers', range(4))])
        expected = ((ds + Variable('dim3', np.zeros(10)))
                    .transpose('dim3', 'dim1', 'dim2', 'time'))
        actual = grouped + zeros
        self.assertDatasetEqual(expected, actual)

        actual = zeros + grouped
        self.assertDatasetEqual(expected, actual)

        with self.assertRaisesRegexp(ValueError, 'incompat.* grouped binary'):
            grouped + ds
        with self.assertRaisesRegexp(ValueError, 'incompat.* grouped binary'):
            ds + grouped
        with self.assertRaisesRegexp(TypeError, 'only support binary ops'):
            grouped + 1
        with self.assertRaisesRegexp(TypeError, 'only support binary ops'):
            grouped + grouped
        with self.assertRaisesRegexp(TypeError, 'in-place operations'):
            ds += grouped

        ds = Dataset({'x': ('time', np.arange(100)),
                      'time': pd.date_range('2000-01-01', periods=100)})
        with self.assertRaisesRegexp(ValueError, 'incompat.* grouped binary'):
            ds + ds.groupby('time.month')

    def test_groupby_math_virtual(self):
        ds = Dataset({'x': ('t', [1, 2, 3])},
                     {'t': pd.date_range('20100101', periods=3)})
        grouped = ds.groupby('t.day')
        actual = grouped - grouped.mean()
        expected = Dataset({'x': ('t', [0, 0, 0])},
                           ds[['t', 't.day']])
        self.assertDatasetIdentical(actual, expected)

    def test_groupby_nan(self):
        # nan should be excluded from groupby
        ds = Dataset({'foo': ('x', [1, 2, 3, 4])},
                     {'bar': ('x', [1, 1, 2, np.nan])})
        actual = ds.groupby('bar').mean()
        expected = Dataset({'foo': ('bar', [1.5, 3]), 'bar': [1, 2]})
        self.assertDatasetIdentical(actual, expected)

    def test_groupby_order(self):
        # groupby should preserve variables order

        ds = Dataset()
        for vn in ['a', 'b', 'c']:
            ds[vn] = DataArray(np.arange(10), dims=['t'])
        all_vars_ref = list(ds.variables.keys())
        data_vars_ref = list(ds.data_vars.keys())
        ds = ds.groupby('t').mean()
        all_vars = list(ds.variables.keys())
        data_vars = list(ds.data_vars.keys())
        self.assertEqual(data_vars, data_vars_ref)
        # coords are now at the end of the list, so the test below fails
        # self.assertEqual(all_vars, all_vars_ref)

    def test_resample_and_first(self):
        times = pd.date_range('2000-01-01', freq='6H', periods=10)
        ds = Dataset({'foo': (['time', 'x', 'y'], np.random.randn(10, 5, 3)),
                      'bar': ('time', np.random.randn(10), {'meta': 'data'}),
                      'time': times})

        actual = ds.resample('1D', dim='time', how='first', keep_attrs=True)
        expected = ds.isel(time=[0, 4, 8])
        self.assertDatasetIdentical(expected, actual)

        # upsampling
        expected_time = pd.date_range('2000-01-01', freq='3H', periods=19)
        expected = ds.reindex(time=expected_time)
        for how in ['mean', 'sum', 'first', 'last', np.mean]:
            actual = ds.resample('3H', 'time', how=how)
            self.assertDatasetEqual(expected, actual)

    def test_resample_by_mean_with_keep_attrs(self):
        times = pd.date_range('2000-01-01', freq='6H', periods=10)
        ds = Dataset({'foo': (['time', 'x', 'y'], np.random.randn(10, 5, 3)),
                      'bar': ('time', np.random.randn(10), {'meta': 'data'}),
                      'time': times})
        ds.attrs['dsmeta'] = 'dsdata'

        resampled_ds = ds.resample('1D', dim='time', how='mean', keep_attrs=True)
        actual = resampled_ds['bar'].attrs
        expected = ds['bar'].attrs
        self.assertEqual(expected, actual)

        actual = resampled_ds.attrs
        expected = ds.attrs
        self.assertEqual(expected, actual)

    def test_resample_by_mean_discarding_attrs(self):
        times = pd.date_range('2000-01-01', freq='6H', periods=10)
        ds = Dataset({'foo': (['time', 'x', 'y'], np.random.randn(10, 5, 3)),
                      'bar': ('time', np.random.randn(10), {'meta': 'data'}),
                      'time': times})
        ds.attrs['dsmeta'] = 'dsdata'

        resampled_ds = ds.resample('1D', dim='time', how='mean', keep_attrs=False)

        assert resampled_ds['bar'].attrs == {}
        assert resampled_ds.attrs == {}

    def test_resample_by_last_discarding_attrs(self):
        times = pd.date_range('2000-01-01', freq='6H', periods=10)
        ds = Dataset({'foo': (['time', 'x', 'y'], np.random.randn(10, 5, 3)),
                      'bar': ('time', np.random.randn(10), {'meta': 'data'}),
                      'time': times})
        ds.attrs['dsmeta'] = 'dsdata'

        resampled_ds = ds.resample('1D', dim='time', how='last', keep_attrs=False)

        assert resampled_ds['bar'].attrs == {}
        assert resampled_ds.attrs == {}

    def test_to_array(self):
        ds = Dataset(OrderedDict([('a', 1), ('b', ('x', [1, 2, 3]))]),
                     coords={'c': 42}, attrs={'Conventions': 'None'})
        data = [[1, 1, 1], [1, 2, 3]]
        coords = {'c': 42, 'variable': ['a', 'b']}
        dims = ('variable', 'x')
        expected = DataArray(data, coords, dims, attrs=ds.attrs)
        actual = ds.to_array()
        self.assertDataArrayIdentical(expected, actual)

        actual = ds.to_array('abc', name='foo')
        expected = expected.rename({'variable': 'abc'}).rename('foo')
        self.assertDataArrayIdentical(expected, actual)

    def test_to_and_from_dataframe(self):
        x = np.random.randn(10)
        y = np.random.randn(10)
        t = list('abcdefghij')
        ds = Dataset(OrderedDict([('a', ('t', x)),
                                  ('b', ('t', y)),
                                  ('t', ('t', t))]))
        expected = pd.DataFrame(np.array([x, y]).T, columns=['a', 'b'],
                                index=pd.Index(t, name='t'))
        actual = ds.to_dataframe()
        # use the .equals method to check all DataFrame metadata
        assert expected.equals(actual), (expected, actual)

        # verify coords are included
        actual = ds.set_coords('b').to_dataframe()
        assert expected.equals(actual), (expected, actual)

        # check roundtrip
        self.assertDatasetIdentical(ds, Dataset.from_dataframe(actual))

        # test a case with a MultiIndex
        w = np.random.randn(2, 3)
        ds = Dataset({'w': (('x', 'y'), w)})
        ds['y'] = ('y', list('abc'))
        exp_index = pd.MultiIndex.from_arrays(
            [[0, 0, 0, 1, 1, 1], ['a', 'b', 'c', 'a', 'b', 'c']],
            names=['x', 'y'])
        expected = pd.DataFrame(w.reshape(-1), columns=['w'], index=exp_index)
        actual = ds.to_dataframe()
        self.assertTrue(expected.equals(actual))

        # check roundtrip
        self.assertDatasetIdentical(ds.assign_coords(x=[0, 1]),
                                    Dataset.from_dataframe(actual))

        # check pathological cases
        df = pd.DataFrame([1])
        actual = Dataset.from_dataframe(df)
        expected = Dataset({0: ('index', [1])}, {'index': [0]})
        self.assertDatasetIdentical(expected, actual)

        df = pd.DataFrame()
        actual = Dataset.from_dataframe(df)
        expected = Dataset(coords={'index': []})
        self.assertDatasetIdentical(expected, actual)

        # GH697
        df = pd.DataFrame({'A' : []})
        actual = Dataset.from_dataframe(df)
        expected = Dataset({'A': DataArray([], dims=('index',))}, {'index': []})
        self.assertDatasetIdentical(expected, actual)

        # regression test for GH278
        # use int64 to ensure consistent results for the pandas .equals method
        # on windows (which requires the same dtype)
        ds = Dataset({'x': pd.Index(['bar']),
                      'a': ('y', np.array([1], 'int64'))}).isel(x=0)
        # use .loc to ensure consistent results on Python 3
        actual = ds.to_dataframe().loc[:, ['a', 'x']]
        expected = pd.DataFrame([[1, 'bar']], index=pd.Index([0], name='y'),
                                columns=['a', 'x'])
        assert expected.equals(actual), (expected, actual)

        ds = Dataset({'x': np.array([0], 'int64'),
                      'y': np.array([1], 'int64')})
        actual = ds.to_dataframe()
        idx = pd.MultiIndex.from_arrays([[0], [1]], names=['x', 'y'])
        expected = pd.DataFrame([[]], index=idx)
        assert expected.equals(actual), (expected, actual)

    def test_from_dataframe_non_unique_columns(self):
        # regression test for GH449
        df = pd.DataFrame(np.zeros((2, 2)))
        df.columns = ['foo', 'foo']
        with self.assertRaisesRegexp(ValueError, 'non-unique columns'):
            Dataset.from_dataframe(df)

    def test_convert_dataframe_with_many_types_and_multiindex(self):
        # regression test for GH737
        df = pd.DataFrame({'a': list('abc'),
                           'b': list(range(1, 4)),
                           'c': np.arange(3, 6).astype('u1'),
                           'd': np.arange(4.0, 7.0, dtype='float64'),
                           'e': [True, False, True],
                           'f': pd.Categorical(list('abc')),
                           'g': pd.date_range('20130101', periods=3),
                           'h': pd.date_range('20130101',
                                              periods=3,
                                              tz='US/Eastern')})
        df.index = pd.MultiIndex.from_product([['a'], range(3)],
                                              names=['one', 'two'])
        roundtripped = Dataset.from_dataframe(df).to_dataframe()
        # we can't do perfectly, but we should be at least as faithful as
        # np.asarray
        expected = df.apply(np.asarray)
        if pd.__version__ < '0.17':
            # datetime with timezone dtype is not consistent on old pandas
            roundtripped = roundtripped.drop(['h'], axis=1)
            expected = expected.drop(['h'], axis=1)
        assert roundtripped.equals(expected)

    def test_to_and_from_dict(self):
        # <xarray.Dataset>
        # Dimensions:  (t: 10)
        # Coordinates:
        #   * t        (t) <U1 'a' 'b' 'c' 'd' 'e' 'f' 'g' 'h' 'i' 'j'
        # Data variables:
        #     a        (t) float64 0.6916 -1.056 -1.163 0.9792 -0.7865 ...
        #     b        (t) float64 1.32 0.1954 1.91 1.39 0.519 -0.2772 ...
        x = np.random.randn(10)
        y = np.random.randn(10)
        t = list('abcdefghij')
        ds = Dataset(OrderedDict([('a', ('t', x)),
                                  ('b', ('t', y)),
                                  ('t', ('t', t))]))
        expected = {'coords': {'t': {'dims': ('t',),
                                     'data': t,
                                     'attrs': {}}},
                    'attrs': {},
                    'dims': {'t': 10},
                    'data_vars': {'a': {'dims': ('t',),
                                        'data': x.tolist(),
                                        'attrs': {}},
                                  'b': {'dims': ('t',),
                                        'data': y.tolist(),
                                        'attrs': {}}}}

        actual = ds.to_dict()

        # check that they are identical
        self.assertEqual(expected, actual)

        # check roundtrip
        self.assertDatasetIdentical(ds, Dataset.from_dict(actual))

        # verify coords are included roundtrip
        expected = ds.set_coords('b')
        actual = Dataset.from_dict(expected.to_dict())

        self.assertDatasetIdentical(expected, actual)

        # test some incomplete dicts:
        # this one has no attrs field, the dims are strings, and x, y are
        # np.arrays

        d = {'coords': {'t': {'dims': 't', 'data': t}},
             'dims': 't',
             'data_vars': {'a': {'dims': 't', 'data': x},
                           'b': {'dims': 't', 'data': y}}}
        self.assertDatasetIdentical(ds, Dataset.from_dict(d))

        # this is kind of a flattened version with no coords, or data_vars
        d = {'a': {'dims': 't', 'data': x},
             't': {'data': t, 'dims': 't'},
             'b': {'dims': 't', 'data': y}}
        self.assertDatasetIdentical(ds, Dataset.from_dict(d))

        # this one is missing some necessary information
        d = {'a': {'data': x},
             't': {'data': t, 'dims': 't'},
             'b': {'dims': 't', 'data': y}}
        with self.assertRaisesRegexp(ValueError, "cannot convert dict "
                                     "without the key 'dims'"):
            Dataset.from_dict(d)

    def test_to_and_from_dict_with_time_dim(self):
        x = np.random.randn(10, 3)
        y = np.random.randn(10, 3)
        t = pd.date_range('20130101', periods=10)
        lat = [77.7, 83.2, 76]
        ds = Dataset(OrderedDict([('a', (['t', 'lat'], x)),
                                  ('b', (['t', 'lat'], y)),
                                  ('t', ('t', t)),
                                  ('lat', ('lat', lat))]))
        roundtripped = Dataset.from_dict(ds.to_dict())
        self.assertDatasetIdentical(ds, roundtripped)

    def test_to_and_from_dict_with_nan_nat(self):
        x = np.random.randn(10, 3)
        y = np.random.randn(10, 3)
        y[2] = np.nan
        t = pd.Series(pd.date_range('20130101', periods=10))
        t[2] = np.nan

        lat = [77.7, 83.2, 76]
        ds = Dataset(OrderedDict([('a', (['t', 'lat'], x)),
                                  ('b', (['t', 'lat'], y)),
                                  ('t', ('t', t)),
                                  ('lat', ('lat', lat))]))
        roundtripped = Dataset.from_dict(ds.to_dict())
        self.assertDatasetIdentical(ds, roundtripped)

    def test_to_dict_with_numpy_attrs(self):
        # this doesn't need to roundtrip
        x = np.random.randn(10)
        y = np.random.randn(10)
        t = list('abcdefghij')
        attrs = {'created': np.float64(1998),
                 'coords': np.array([37, -110.1, 100]),
                 'maintainer': 'bar'}
        ds = Dataset(OrderedDict([('a', ('t', x, attrs)),
                                  ('b', ('t', y, attrs)),
                                  ('t', ('t', t))]))
        expected_attrs = {'created': np.asscalar(attrs['created']),
                          'coords': attrs['coords'].tolist(),
                          'maintainer': 'bar'}
        actual = ds.to_dict()

        # check that they are identical
        self.assertEqual(expected_attrs, actual['data_vars']['a']['attrs'])

    def test_pickle(self):
        data = create_test_data()
        roundtripped = pickle.loads(pickle.dumps(data))
        self.assertDatasetIdentical(data, roundtripped)
        # regression test for #167:
        self.assertEqual(data.dims, roundtripped.dims)

    def test_lazy_load(self):
        store = InaccessibleVariableDataStore()
        create_test_data().dump_to_store(store)

        for decode_cf in [True, False]:
            ds = open_dataset(store, decode_cf=decode_cf)
            with self.assertRaises(UnexpectedDataAccess):
                ds.load()
            with self.assertRaises(UnexpectedDataAccess):
                ds['var1'].values

            # these should not raise UnexpectedDataAccess:
            ds.isel(time=10)
            ds.isel(time=slice(10), dim1=[0]).isel(dim1=0, dim2=-1)

    def test_dropna(self):
        x = np.random.randn(4, 4)
        x[::2, 0] = np.nan
        y = np.random.randn(4)
        y[-1] = np.nan
        ds = Dataset({'foo': (('a', 'b'), x), 'bar': (('b', y))})

        expected = ds.isel(a=slice(1, None, 2))
        actual = ds.dropna('a')
        self.assertDatasetIdentical(actual, expected)

        expected = ds.isel(b=slice(1, 3))
        actual = ds.dropna('b')
        self.assertDatasetIdentical(actual, expected)

        actual = ds.dropna('b', subset=['foo', 'bar'])
        self.assertDatasetIdentical(actual, expected)

        expected = ds.isel(b=slice(1, None))
        actual = ds.dropna('b', subset=['foo'])
        self.assertDatasetIdentical(actual, expected)

        expected = ds.isel(b=slice(3))
        actual = ds.dropna('b', subset=['bar'])
        self.assertDatasetIdentical(actual, expected)

        actual = ds.dropna('a', subset=[])
        self.assertDatasetIdentical(actual, ds)

        actual = ds.dropna('a', subset=['bar'])
        self.assertDatasetIdentical(actual, ds)

        actual = ds.dropna('a', how='all')
        self.assertDatasetIdentical(actual, ds)

        actual = ds.dropna('b', how='all', subset=['bar'])
        expected = ds.isel(b=[0, 1, 2])
        self.assertDatasetIdentical(actual, expected)

        actual = ds.dropna('b', thresh=1, subset=['bar'])
        self.assertDatasetIdentical(actual, expected)

        actual = ds.dropna('b', thresh=2)
        self.assertDatasetIdentical(actual, ds)

        actual = ds.dropna('b', thresh=4)
        expected = ds.isel(b=[1, 2, 3])
        self.assertDatasetIdentical(actual, expected)

        actual = ds.dropna('a', thresh=3)
        expected = ds.isel(a=[1, 3])
        self.assertDatasetIdentical(actual, ds)

        with self.assertRaisesRegexp(ValueError, 'a single dataset dimension'):
            ds.dropna('foo')
        with self.assertRaisesRegexp(ValueError, 'invalid how'):
            ds.dropna('a', how='somehow')
        with self.assertRaisesRegexp(TypeError, 'must specify how or thresh'):
            ds.dropna('a', how=None)

    def test_fillna(self):
        ds = Dataset({'a': ('x', [np.nan, 1, np.nan, 3])},
                     {'x': [0, 1, 2, 3]})

        # fill with -1
        actual = ds.fillna(-1)
        expected = Dataset({'a': ('x', [-1, 1, -1, 3])}, {'x': [0, 1, 2, 3]})
        self.assertDatasetIdentical(expected, actual)

        actual = ds.fillna({'a': -1})
        self.assertDatasetIdentical(expected, actual)

        other = Dataset({'a': -1})
        actual = ds.fillna(other)
        self.assertDatasetIdentical(expected, actual)

        actual = ds.fillna({'a': other.a})
        self.assertDatasetIdentical(expected, actual)

        # fill with range(4)
        b = DataArray(range(4), coords=[('x', range(4))])
        actual = ds.fillna(b)
        expected = b.rename('a').to_dataset()
        self.assertDatasetIdentical(expected, actual)

        actual = ds.fillna(expected)
        self.assertDatasetIdentical(expected, actual)

        actual = ds.fillna(range(4))
        self.assertDatasetIdentical(expected, actual)

        actual = ds.fillna(b[:3])
        self.assertDatasetIdentical(expected, actual)

        # okay to only include some data variables
        ds['b'] = np.nan
        actual = ds.fillna({'a': -1})
        expected = Dataset({'a': ('x', [-1, 1, -1, 3]), 'b': np.nan},
                           {'x': [0, 1, 2, 3]})
        self.assertDatasetIdentical(expected, actual)

        # but new data variables is not okay
        with self.assertRaisesRegexp(ValueError, 'must be contained'):
            ds.fillna({'x': 0})

        # empty argument should be OK
        result = ds.fillna({})
        self.assertDatasetIdentical(ds, result)

        result = ds.fillna(Dataset(coords={'c': 42}))
        expected = ds.assign_coords(c=42)
        self.assertDatasetIdentical(expected, result)

        # groupby
        expected = Dataset({'a': ('x', range(4))}, {'x': [0, 1, 2, 3]})
        for target in [ds, expected]:
            target.coords['b'] = ('x', [0, 0, 1, 1])
        actual = ds.groupby('b').fillna(DataArray([0, 2], dims='b'))
        self.assertDatasetIdentical(expected, actual)

        actual = ds.groupby('b').fillna(Dataset({'a': ('b', [0, 2])}))
        self.assertDatasetIdentical(expected, actual)

        # attrs with groupby
        ds.attrs['attr'] = 'ds'
        ds.a.attrs['attr'] = 'da'
        actual = ds.groupby('b').fillna(Dataset({'a': ('b', [0, 2])}))
        self.assertEqual(actual.attrs, ds.attrs)
        self.assertEqual(actual.a.name, 'a')
        self.assertEqual(actual.a.attrs, ds.a.attrs)

        da = DataArray(range(5), name='a', attrs={'attr': 'da'})
        actual = da.fillna(1)
        self.assertEqual(actual.name, 'a')
        self.assertEqual(actual.attrs, da.attrs)

        ds = Dataset({'a': da}, attrs={'attr': 'ds'})
        actual = ds.fillna({'a': 1})
        self.assertEqual(actual.attrs, ds.attrs)
        self.assertEqual(actual.a.name, 'a')
        self.assertEqual(actual.a.attrs, ds.a.attrs)

    def test_where(self):
        ds = Dataset({'a': ('x', range(5))})
        expected = Dataset({'a': ('x', [np.nan, np.nan, 2, 3, 4])})
        actual = ds.where(ds > 1)
        self.assertDatasetIdentical(expected, actual)

        actual = ds.where(ds.a > 1)
        self.assertDatasetIdentical(expected, actual)

        actual = ds.where(ds.a.values > 1)
        self.assertDatasetIdentical(expected, actual)

        actual = ds.where(True)
        self.assertDatasetIdentical(ds, actual)

        expected = ds.copy(deep=True)
        expected['a'].values = [np.nan] * 5
        actual = ds.where(False)
        self.assertDatasetIdentical(expected, actual)

        # 2d
        ds = Dataset({'a': (('x', 'y'), [[0, 1], [2, 3]])})
        expected = Dataset({'a': (('x', 'y'), [[np.nan, 1], [2, 3]])})
        actual = ds.where(ds > 0)
        self.assertDatasetIdentical(expected, actual)

        # groupby
        ds = Dataset({'a': ('x', range(5))}, {'c': ('x', [0, 0, 1, 1, 1])})
        cond = Dataset({'a': ('c', [True, False])})
        expected = ds.copy(deep=True)
        expected['a'].values = [0, 1] + [np.nan] * 3
        actual = ds.groupby('c').where(cond)
        self.assertDatasetIdentical(expected, actual)

        # attrs with groupby
        ds.attrs['attr'] = 'ds'
        ds.a.attrs['attr'] = 'da'
        actual = ds.groupby('c').where(cond)
        self.assertEqual(actual.attrs, ds.attrs)
        self.assertEqual(actual.a.name, 'a')
        self.assertEqual(actual.a.attrs, ds.a.attrs)

        # attrs
        da = DataArray(range(5), name='a', attrs={'attr': 'da'})
        actual = da.where(da.values > 1)
        self.assertEqual(actual.name, 'a')
        self.assertEqual(actual.attrs, da.attrs)

        ds = Dataset({'a': da}, attrs={'attr': 'ds'})
        actual = ds.where(ds > 0)
        self.assertEqual(actual.attrs, ds.attrs)
        self.assertEqual(actual.a.name, 'a')
        self.assertEqual(actual.a.attrs, ds.a.attrs)

    def test_where_other(self):
        ds = Dataset({'a': ('x', range(5))}, {'x': range(5)})
        expected = Dataset({'a': ('x', [-1, -1, 2, 3, 4])}, {'x': range(5)})
        actual = ds.where(ds > 1, -1)
        assert_equal(expected, actual)
        assert actual.a.dtype == int

        with raises_regex(ValueError, "cannot set"):
            ds.where(ds > 1, other=0, drop=True)

        with raises_regex(ValueError, "indexes .* are not equal"):
            ds.where(ds > 1, ds.isel(x=slice(3)))

        with raises_regex(ValueError, "exact match required"):
            ds.where(ds > 1, ds.assign(b=2))

    def test_where_drop(self):
        # if drop=True

        # 1d
        # data array case
        array = DataArray(range(5), coords=[range(5)], dims=['x'])
        expected = DataArray(range(5)[2:], coords=[range(5)[2:]], dims=['x'])
        actual = array.where(array > 1, drop=True)
        self.assertDatasetIdentical(expected, actual)

        # dataset case
        ds = Dataset({'a': array})
        expected = Dataset({'a': expected})

        actual = ds.where(ds > 1, drop=True)
        self.assertDatasetIdentical(expected, actual)

        actual = ds.where(ds.a > 1, drop=True)
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaisesRegexp(TypeError, 'must be a'):
            ds.where(np.arange(5) > 1, drop=True)

        # 1d with odd coordinates
        array = DataArray(np.array([2, 7, 1, 8, 3]), coords=[np.array([3, 1, 4, 5, 9])], dims=['x'])
        expected = DataArray(np.array([7, 8, 3]), coords=[np.array([1, 5, 9])], dims=['x'])
        actual = array.where(array > 2, drop=True)
        self.assertDatasetIdentical(expected, actual)

        # 1d multiple variables
        ds = Dataset({'a': (('x'), [0, 1, 2, 3]), 'b': (('x'), [4, 5, 6, 7])})
        expected = Dataset({'a': (('x'), [np.nan, 1, 2, 3]), 'b': (('x'), [4, 5, 6, np.nan])})
        actual = ds.where((ds > 0) & (ds < 7), drop=True)
        self.assertDatasetIdentical(expected, actual)

        # 2d
        ds = Dataset({'a': (('x', 'y'), [[0, 1], [2, 3]])})
        expected = Dataset({'a': (('x', 'y'), [[np.nan, 1], [2, 3]])})
        actual = ds.where(ds > 0, drop=True)
        self.assertDatasetIdentical(expected, actual)

        # 2d with odd coordinates
        ds = Dataset({'a': (('x', 'y'), [[0, 1], [2, 3]])},
                coords={'x': [4, 3], 'y': [1, 2],
                    'z' : (['x','y'], [[np.e, np.pi], [np.pi*np.e, np.pi*3]])})
        expected = Dataset({'a': (('x', 'y'), [[3]])},
                coords={'x': [3], 'y': [2],
                    'z' : (['x','y'], [[np.pi*3]])})
        actual = ds.where(ds > 2, drop=True)
        self.assertDatasetIdentical(expected, actual)

        # 2d multiple variables
        ds = Dataset({'a': (('x', 'y'), [[0, 1], [2, 3]]), 'b': (('x','y'), [[4, 5], [6, 7]])})
        expected = Dataset({'a': (('x', 'y'), [[np.nan, 1], [2, 3]]), 'b': (('x', 'y'), [[4, 5], [6,7]])})
        actual = ds.where(ds > 0, drop=True)
        self.assertDatasetIdentical(expected, actual)

    def test_where_drop_empty(self):
        # regression test for GH1341
        array = DataArray(np.random.rand(100, 10),
                          dims=['nCells', 'nVertLevels'])
        mask = DataArray(np.zeros((100,), dtype='bool'), dims='nCells')
        actual = array.where(mask, drop=True)
        expected = DataArray(np.zeros((0, 10)), dims=['nCells', 'nVertLevels'])
        self.assertDatasetIdentical(expected, actual)

    def test_where_drop_no_indexes(self):
        ds = Dataset({'foo': ('x', [0.0, 1.0])})
        expected = Dataset({'foo': ('x', [1.0])})
        actual = ds.where(ds == 1, drop=True)
        self.assertDatasetIdentical(expected, actual)

    def test_reduce(self):
        data = create_test_data()

        self.assertEqual(len(data.mean().coords), 0)

        actual = data.max()
        expected = Dataset(dict((k, v.max())
                                for k, v in iteritems(data.data_vars)))
        self.assertDatasetEqual(expected, actual)

        self.assertDatasetEqual(data.min(dim=['dim1']),
                                data.min(dim='dim1'))

        for reduct, expected in [('dim2', ['dim1', 'dim3', 'time']),
                                 (['dim2', 'time'], ['dim1', 'dim3']),
                                 (('dim2', 'time'), ['dim1', 'dim3']),
                                 ((), ['dim1', 'dim2', 'dim3', 'time'])]:
            actual = data.min(dim=reduct).dims
            print(reduct, actual, expected)
            self.assertItemsEqual(actual, expected)

        self.assertDatasetEqual(data.mean(dim=[]), data)

    def test_reduce_bad_dim(self):
        data = create_test_data()
        with self.assertRaisesRegexp(ValueError, 'Dataset does not contain'):
            ds = data.mean(dim='bad_dim')

    def test_reduce_cumsum_test_dims(self):
        data = create_test_data()
        for cumfunc in ['cumsum', 'cumprod']:
            with self.assertRaisesRegexp(ValueError, "must supply either single 'dim' or 'axis'"):
                ds = getattr(data, cumfunc)()
            with self.assertRaisesRegexp(ValueError, "must supply either single 'dim' or 'axis'"):
                ds = getattr(data, cumfunc)(dim=['dim1', 'dim2'])
            with self.assertRaisesRegexp(ValueError, 'Dataset does not contain'):
                ds = getattr(data, cumfunc)(dim='bad_dim')

            # ensure dimensions are correct
            for reduct, expected in [('dim1', ['dim1', 'dim2', 'dim3', 'time']),
                                     ('dim2', ['dim1', 'dim2', 'dim3', 'time']),
                                     ('dim3', ['dim1', 'dim2', 'dim3', 'time']),
                                     ('time', ['dim1', 'dim2', 'dim3'])]:
                actual = getattr(data, cumfunc)(dim=reduct).dims
                print(reduct, actual, expected)
                self.assertItemsEqual(actual, expected)

    def test_reduce_non_numeric(self):
        data1 = create_test_data(seed=44)
        data2 = create_test_data(seed=44)
        add_vars = {'var4': ['dim1', 'dim2']}
        for v, dims in sorted(add_vars.items()):
            size = tuple(data1.dims[d] for d in dims)
            data = np.random.random_integers(0, 100, size=size).astype(np.str_)
            data1[v] = (dims, data, {'foo': 'variable'})

        self.assertTrue('var4' not in data1.mean())
        self.assertDatasetEqual(data1.mean(), data2.mean())
        self.assertDatasetEqual(data1.mean(dim='dim1'),
                                data2.mean(dim='dim1'))

    def test_reduce_strings(self):
        expected = Dataset({'x': 'a'})
        ds = Dataset({'x': ('y', ['a', 'b'])})
        actual = ds.min()
        self.assertDatasetIdentical(expected, actual)

        expected = Dataset({'x': 'b'})
        actual = ds.max()
        self.assertDatasetIdentical(expected, actual)

        expected = Dataset({'x': 0})
        actual = ds.argmin()
        self.assertDatasetIdentical(expected, actual)

        expected = Dataset({'x': 1})
        actual = ds.argmax()
        self.assertDatasetIdentical(expected, actual)

        expected = Dataset({'x': b'a'})
        ds = Dataset({'x': ('y', np.array(['a', 'b'], 'S1'))})
        actual = ds.min()
        self.assertDatasetIdentical(expected, actual)

        expected = Dataset({'x': u'a'})
        ds = Dataset({'x': ('y', np.array(['a', 'b'], 'U1'))})
        actual = ds.min()
        self.assertDatasetIdentical(expected, actual)

    def test_reduce_dtypes(self):
        # regression test for GH342
        expected = Dataset({'x': 1})
        actual = Dataset({'x': True}).sum()
        self.assertDatasetIdentical(expected, actual)

        # regression test for GH505
        expected = Dataset({'x': 3})
        actual = Dataset({'x': ('y', np.array([1, 2], 'uint16'))}).sum()
        self.assertDatasetIdentical(expected, actual)

        expected = Dataset({'x': 1 + 1j})
        actual = Dataset({'x': ('y', [1, 1j])}).sum()
        self.assertDatasetIdentical(expected, actual)

    def test_reduce_keep_attrs(self):
        data = create_test_data()
        _attrs = {'attr1': 'value1', 'attr2': 2929}

        attrs = OrderedDict(_attrs)
        data.attrs = attrs

        # Test dropped attrs
        ds = data.mean()
        self.assertEqual(ds.attrs, {})
        for v in ds.data_vars.values():
            self.assertEqual(v.attrs, {})

        # Test kept attrs
        ds = data.mean(keep_attrs=True)
        self.assertEqual(ds.attrs, attrs)
        for k, v in ds.data_vars.items():
            self.assertEqual(v.attrs, data[k].attrs)

    def test_reduce_argmin(self):
        # regression test for #205
        ds = Dataset({'a': ('x', [0, 1])})
        expected = Dataset({'a': ([], 0)})
        actual = ds.argmin()
        self.assertDatasetIdentical(expected, actual)

        actual = ds.argmin('x')
        self.assertDatasetIdentical(expected, actual)

    def test_reduce_scalars(self):
        ds = Dataset({'x': ('a', [2, 2]), 'y': 2, 'z': ('b', [2])})
        expected = Dataset({'x': 0, 'y': 0, 'z': 0})
        actual = ds.var()
        self.assertDatasetIdentical(expected, actual)

    def test_reduce_only_one_axis(self):

        def mean_only_one_axis(x, axis):
            if not isinstance(axis, integer_types):
                raise TypeError('non-integer axis')
            return x.mean(axis)

        ds = Dataset({'a': (['x', 'y'], [[0, 1, 2, 3, 4]])})
        expected = Dataset({'a': ('x', [2])})
        actual = ds.reduce(mean_only_one_axis, 'y')
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaisesRegexp(TypeError, 'non-integer axis'):
            ds.reduce(mean_only_one_axis)

        with self.assertRaisesRegexp(TypeError, 'non-integer axis'):
            ds.reduce(mean_only_one_axis, ['x', 'y'])

    def test_quantile(self):

        ds = create_test_data(seed=123)

        for q in [0.25, [0.50], [0.25, 0.75]]:
            for dim in [None, 'dim1', ['dim1']]:
                ds_quantile = ds.quantile(q, dim=dim)
                assert 'quantile' in ds_quantile
                for var, dar in ds.data_vars.items():
                    assert var in ds_quantile
                    self.assertDataArrayIdentical(
                        ds_quantile[var], dar.quantile(q, dim=dim))
            dim = ['dim1', 'dim2']
            ds_quantile = ds.quantile(q, dim=dim)
            assert 'dim3' in ds_quantile.dims
            assert all(d not in ds_quantile.dims for d in dim)

    def test_count(self):
        ds = Dataset({'x': ('a', [np.nan, 1]), 'y': 0, 'z': np.nan})
        expected = Dataset({'x': 1, 'y': 1, 'z': 0})
        actual = ds.count()
        self.assertDatasetIdentical(expected, actual)

    def test_apply(self):
        data = create_test_data()
        data.attrs['foo'] = 'bar'

        self.assertDatasetIdentical(data.apply(np.mean), data.mean())

        expected = data.mean(keep_attrs=True)
        actual = data.apply(lambda x: x.mean(keep_attrs=True), keep_attrs=True)
        self.assertDatasetIdentical(expected, actual)

        self.assertDatasetIdentical(data.apply(lambda x: x, keep_attrs=True),
                                    data.drop('time'))

        def scale(x, multiple=1):
            return multiple * x

        actual = data.apply(scale, multiple=2)
        self.assertDataArrayEqual(actual['var1'], 2 * data['var1'])
        self.assertDataArrayIdentical(actual['numbers'], data['numbers'])

        actual = data.apply(np.asarray)
        expected = data.drop('time') # time is not used on a data var
        self.assertDatasetEqual(expected, actual)

    def make_example_math_dataset(self):
        variables = OrderedDict(
            [('bar', ('x', np.arange(100, 400, 100))),
             ('foo', (('x', 'y'), 1.0 * np.arange(12).reshape(3, 4)))])
        coords = {'abc': ('x', ['a', 'b', 'c']),
                  'y': 10 * np.arange(4)}
        ds = Dataset(variables, coords)
        ds['foo'][0, 0] = np.nan
        return ds

    def test_dataset_number_math(self):
        ds = self.make_example_math_dataset()

        self.assertDatasetIdentical(ds, +ds)
        self.assertDatasetIdentical(ds, ds + 0)
        self.assertDatasetIdentical(ds, 0 + ds)
        self.assertDatasetIdentical(ds, ds + np.array(0))
        self.assertDatasetIdentical(ds, np.array(0) + ds)

        actual = ds.copy(deep=True)
        actual += 0
        self.assertDatasetIdentical(ds, actual)

    def test_unary_ops(self):
        ds = self.make_example_math_dataset()

        self.assertDatasetIdentical(ds.apply(abs), abs(ds))
        self.assertDatasetIdentical(ds.apply(lambda x: x + 4), ds + 4)

        for func in [lambda x: x.isnull(),
                     lambda x: x.round(),
                     lambda x: x.astype(int)]:
            self.assertDatasetIdentical(ds.apply(func), func(ds))

        self.assertDatasetIdentical(ds.isnull(), ~ds.notnull())

        # don't actually patch these methods in
        with self.assertRaises(AttributeError):
            ds.item
        with self.assertRaises(AttributeError):
            ds.searchsorted

    def test_dataset_array_math(self):
        ds = self.make_example_math_dataset()

        expected = ds.apply(lambda x: x - ds['foo'])
        self.assertDatasetIdentical(expected, ds - ds['foo'])
        self.assertDatasetIdentical(expected, -ds['foo'] + ds)
        self.assertDatasetIdentical(expected, ds - ds['foo'].variable)
        self.assertDatasetIdentical(expected, -ds['foo'].variable + ds)
        actual = ds.copy(deep=True)
        actual -= ds['foo']
        self.assertDatasetIdentical(expected, actual)

        expected = ds.apply(lambda x: x + ds['bar'])
        self.assertDatasetIdentical(expected, ds + ds['bar'])
        actual = ds.copy(deep=True)
        actual += ds['bar']
        self.assertDatasetIdentical(expected, actual)

        expected = Dataset({'bar': ds['bar'] + np.arange(3)})
        self.assertDatasetIdentical(expected, ds[['bar']] + np.arange(3))
        self.assertDatasetIdentical(expected, np.arange(3) + ds[['bar']])

    def test_dataset_dataset_math(self):
        ds = self.make_example_math_dataset()

        self.assertDatasetIdentical(ds, ds + 0 * ds)
        self.assertDatasetIdentical(ds, ds + {'foo': 0, 'bar': 0})

        expected = ds.apply(lambda x: 2 * x)
        self.assertDatasetIdentical(expected, 2 * ds)
        self.assertDatasetIdentical(expected, ds + ds)
        self.assertDatasetIdentical(expected, ds + ds.data_vars)
        self.assertDatasetIdentical(expected, ds + dict(ds.data_vars))

        actual = ds.copy(deep=True)
        expected_id = id(actual)
        actual += ds
        self.assertDatasetIdentical(expected, actual)
        self.assertEqual(expected_id, id(actual))

        self.assertDatasetIdentical(ds == ds, ds.notnull())

        subsampled = ds.isel(y=slice(2))
        expected = 2 * subsampled
        self.assertDatasetIdentical(expected, subsampled + ds)
        self.assertDatasetIdentical(expected, ds + subsampled)

    def test_dataset_math_auto_align(self):
        ds = self.make_example_math_dataset()
        subset = ds.isel(y=[1, 3])
        expected = 2 * subset
        actual = ds + subset
        self.assertDatasetIdentical(expected, actual)

        actual = ds.isel(y=slice(1)) + ds.isel(y=slice(1, None))
        expected = 2 * ds.drop(ds.y, dim='y')
        self.assertDatasetEqual(actual, expected)

        actual = ds + ds[['bar']]
        expected = (2 * ds[['bar']]).merge(ds.coords)
        self.assertDatasetIdentical(expected, actual)

        self.assertDatasetIdentical(ds + Dataset(), ds.coords.to_dataset())
        self.assertDatasetIdentical(Dataset() + Dataset(), Dataset())

        ds2 = Dataset(coords={'bar': 42})
        self.assertDatasetIdentical(ds + ds2, ds.coords.merge(ds2))

        # maybe unary arithmetic with empty datasets should raise instead?
        self.assertDatasetIdentical(Dataset() + 1, Dataset())

        actual = ds.copy(deep=True)
        other = ds.isel(y=slice(2))
        actual += other
        expected = ds + other.reindex_like(ds)
        self.assertDatasetIdentical(expected, actual)

    def test_dataset_math_errors(self):
        ds = self.make_example_math_dataset()

        with self.assertRaises(TypeError):
            ds['foo'] += ds
        with self.assertRaises(TypeError):
            ds['foo'].variable += ds
        with self.assertRaisesRegexp(ValueError, 'must have the same'):
            ds += ds[['bar']]

        # verify we can rollback in-place operations if something goes wrong
        # nb. inplace datetime64 math actually will work with an integer array
        # but not floats thanks to numpy's inconsistent handling
        other = DataArray(np.datetime64('2000-01-01T12'), coords={'c': 2})
        actual = ds.copy(deep=True)
        with self.assertRaises(TypeError):
            actual += other
        self.assertDatasetIdentical(actual, ds)

    def test_dataset_transpose(self):
        ds = Dataset({'a': (('x', 'y'), np.random.randn(3, 4)),
                      'b': (('y', 'x'), np.random.randn(4, 3))})

        actual = ds.transpose()
        expected = ds.apply(lambda x: x.transpose())
        self.assertDatasetIdentical(expected, actual)

        actual = ds.T
        self.assertDatasetIdentical(expected, actual)

        actual = ds.transpose('x', 'y')
        expected = ds.apply(lambda x: x.transpose('x', 'y'))
        self.assertDatasetIdentical(expected, actual)

        ds = create_test_data()
        actual = ds.transpose()
        for k in ds:
            self.assertEqual(actual[k].dims[::-1], ds[k].dims)

        new_order = ('dim2', 'dim3', 'dim1', 'time')
        actual = ds.transpose(*new_order)
        for k in ds:
            expected_dims = tuple(d for d in new_order if d in ds[k].dims)
            self.assertEqual(actual[k].dims, expected_dims)

        with self.assertRaisesRegexp(ValueError, 'arguments to transpose'):
            ds.transpose('dim1', 'dim2', 'dim3')
        with self.assertRaisesRegexp(ValueError, 'arguments to transpose'):
            ds.transpose('dim1', 'dim2', 'dim3', 'time', 'extra_dim')

    def test_dataset_retains_period_index_on_transpose(self):

        ds = create_test_data()
        ds['time'] = pd.period_range('2000-01-01', periods=20)

        transposed = ds.transpose()

        self.assertIsInstance(transposed.time.to_index(), pd.PeriodIndex)

    def test_dataset_diff_n1_simple(self):
        ds = Dataset({'foo': ('x', [5, 5, 6, 6])})
        actual = ds.diff('x')
        expected = Dataset({'foo': ('x', [0, 1, 0])})
        self.assertDatasetEqual(expected, actual)

    def test_dataset_diff_n1_label(self):
        ds = Dataset({'foo': ('x', [5, 5, 6, 6])}, {'x': [0, 1, 2, 3]})
        actual = ds.diff('x', label='lower')
        expected = Dataset({'foo': ('x', [0, 1, 0])}, {'x': [0, 1, 2]})
        self.assertDatasetEqual(expected, actual)

        actual = ds.diff('x', label='upper')
        expected = Dataset({'foo': ('x', [0, 1, 0])}, {'x': [1, 2, 3]})
        self.assertDatasetEqual(expected, actual)

    def test_dataset_diff_n1(self):
        ds = create_test_data(seed=1)
        actual = ds.diff('dim2')
        expected = dict()
        expected['var1'] = DataArray(np.diff(ds['var1'].values, axis=1),
                                     {'dim2': ds['dim2'].values[1:]},
                                     ['dim1', 'dim2'])
        expected['var2'] = DataArray(np.diff(ds['var2'].values, axis=1),
                                     {'dim2': ds['dim2'].values[1:]},
                                     ['dim1', 'dim2'])
        expected['var3'] = ds['var3']
        expected = Dataset(expected, coords={'time': ds['time'].values})
        expected.coords['numbers'] = ('dim3', ds['numbers'].values)
        self.assertDatasetEqual(expected, actual)

    def test_dataset_diff_n2(self):
        ds = create_test_data(seed=1)
        actual = ds.diff('dim2', n=2)
        expected = dict()
        expected['var1'] = DataArray(np.diff(ds['var1'].values, axis=1, n=2),
                                     {'dim2': ds['dim2'].values[2:]},
                                     ['dim1', 'dim2'])
        expected['var2'] = DataArray(np.diff(ds['var2'].values, axis=1, n=2),
                                     {'dim2': ds['dim2'].values[2:]},
                                     ['dim1', 'dim2'])
        expected['var3'] = ds['var3']
        expected = Dataset(expected, coords={'time': ds['time'].values})
        expected.coords['numbers'] = ('dim3', ds['numbers'].values)
        self.assertDatasetEqual(expected, actual)

    def test_dataset_diff_exception_n_neg(self):
        ds = create_test_data(seed=1)
        with self.assertRaisesRegexp(ValueError, 'must be non-negative'):
            ds.diff('dim2', n=-1)

    def test_dataset_diff_exception_label_str(self):
        ds = create_test_data(seed=1)
        with self.assertRaisesRegexp(ValueError, '\'label\' argument has to'):
            ds.diff('dim2', label='raise_me')

    def test_shift(self):
        coords = {'bar': ('x', list('abc')), 'x': [-4, 3, 2]}
        attrs = {'meta': 'data'}
        ds = Dataset({'foo': ('x', [1, 2, 3])}, coords, attrs)
        actual = ds.shift(x=1)
        expected = Dataset({'foo': ('x', [np.nan, 1, 2])}, coords, attrs)
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaisesRegexp(ValueError, 'dimensions'):
            ds.shift(foo=123)

    def test_roll(self):
        coords = {'bar': ('x', list('abc')), 'x': [-4, 3, 2]}
        attrs = {'meta': 'data'}
        ds = Dataset({'foo': ('x', [1, 2, 3])}, coords, attrs)
        actual = ds.roll(x=1)

        ex_coords = {'bar': ('x', list('cab')), 'x': [2, -4, 3]}
        expected = Dataset({'foo': ('x', [3, 1, 2])}, ex_coords, attrs)
        self.assertDatasetIdentical(expected, actual)

        with self.assertRaisesRegexp(ValueError, 'dimensions'):
            ds.roll(foo=123)

    def test_real_and_imag(self):
        attrs = {'foo': 'bar'}
        ds = Dataset({'x': ((), 1 + 2j, attrs)}, attrs=attrs)

        expected_re = Dataset({'x': ((), 1, attrs)}, attrs=attrs)
        self.assertDatasetIdentical(ds.real, expected_re)

        expected_im = Dataset({'x': ((), 2, attrs)}, attrs=attrs)
        self.assertDatasetIdentical(ds.imag, expected_im)

    def test_setattr_raises(self):
        ds = Dataset({}, coords={'scalar': 1}, attrs={'foo': 'bar'})
        with self.assertRaisesRegexp(AttributeError, 'cannot set attr'):
            ds.scalar = 2
        with self.assertRaisesRegexp(AttributeError, 'cannot set attr'):
            ds.foo = 2
        with self.assertRaisesRegexp(AttributeError, 'cannot set attr'):
            ds.other = 2

    def test_filter_by_attrs(self):
        precip = dict(standard_name='convective_precipitation_flux')
        temp0 = dict(standard_name='air_potential_temperature', height='0 m')
        temp10 = dict(standard_name='air_potential_temperature', height='10 m')
        ds = Dataset({'temperature_0': (['t'], [0], temp0),
                      'temperature_10': (['t'], [0], temp10),
                      'precipitation': (['t'], [0], precip)},
                     coords={'time': (['t'], [0], dict(axis='T'))})

        # Test return empty Dataset.
        ds.filter_by_attrs(standard_name='invalid_standard_name')
        new_ds = ds.filter_by_attrs(standard_name='invalid_standard_name')
        self.assertFalse(bool(new_ds.data_vars))

        # Test return one DataArray.
        new_ds = ds.filter_by_attrs(standard_name='convective_precipitation_flux')
        self.assertEqual(new_ds['precipitation'].standard_name, 'convective_precipitation_flux')
        self.assertDatasetEqual(new_ds['precipitation'], ds['precipitation'])

        # Test return more than one DataArray.
        new_ds = ds.filter_by_attrs(standard_name='air_potential_temperature')
        self.assertEqual(len(new_ds.data_vars), 2)
        for var in new_ds.data_vars:
            self.assertEqual(new_ds[var].standard_name, 'air_potential_temperature')

        # Test callable.
        new_ds = ds.filter_by_attrs(height=lambda v: v is not None)
        self.assertEqual(len(new_ds.data_vars), 2)
        for var in new_ds.data_vars:
            self.assertEqual(new_ds[var].standard_name, 'air_potential_temperature')

        new_ds = ds.filter_by_attrs(height='10 m')
        self.assertEqual(len(new_ds.data_vars), 1)
        for var in new_ds.data_vars:
            self.assertEqual(new_ds[var].height, '10 m')

    def test_binary_op_join_setting(self):
        # arithmetic_join applies to data array coordinates
        missing_2 = xr.Dataset({'x': [0, 1]})
        missing_0 = xr.Dataset({'x': [1, 2]})
        with xr.set_options(arithmetic_join='outer'):
            actual = missing_2 + missing_0
        expected = xr.Dataset({'x': [0, 1, 2]})
        self.assertDatasetEqual(actual, expected)

        # arithmetic join also applies to data_vars
        ds1 = xr.Dataset({'foo': 1, 'bar': 2})
        ds2 = xr.Dataset({'bar': 2, 'baz': 3})
        expected = xr.Dataset({'bar': 4})  # default is inner joining
        actual = ds1 + ds2
        self.assertDatasetEqual(actual, expected)

        with xr.set_options(arithmetic_join='outer'):
            expected = xr.Dataset({'foo': np.nan, 'bar': 4, 'baz': np.nan})
            actual = ds1 + ds2
            self.assertDatasetEqual(actual, expected)

        with xr.set_options(arithmetic_join='left'):
            expected = xr.Dataset({'foo': np.nan, 'bar': 4})
            actual = ds1 + ds2
            self.assertDatasetEqual(actual, expected)

        with xr.set_options(arithmetic_join='right'):
            expected = xr.Dataset({'bar': 4, 'baz': np.nan})
            actual = ds1 + ds2
            self.assertDatasetEqual(actual, expected)

    def test_full_like(self):
        # For more thorough tests, see test_variable.py
        # Note: testing data_vars with mismatched dtypes
        ds = Dataset({
            'd1': DataArray([1,2,3], dims=['x'], coords={'x': [10, 20, 30]}),
            'd2': DataArray([1.1, 2.2, 3.3], dims=['y'])
        }, attrs={'foo': 'bar'})
        actual = full_like(ds, 2)

        expect = ds.copy(deep=True)
        expect['d1'].values = [2, 2, 2]
        expect['d2'].values = [2.0, 2.0, 2.0]
        self.assertEqual(expect['d1'].dtype, int)
        self.assertEqual(expect['d2'].dtype, float)
        self.assertDatasetIdentical(expect, actual)

        # override dtype
        actual = full_like(ds, fill_value=True, dtype=bool)
        expect = ds.copy(deep=True)
        expect['d1'].values = [True, True, True]
        expect['d2'].values = [True, True, True]
        self.assertEqual(expect['d1'].dtype, bool)
        self.assertEqual(expect['d2'].dtype, bool)
        self.assertDatasetIdentical(expect, actual)

    def test_combine_first(self):
        dsx0 = DataArray([0, 0], [('x', ['a', 'b'])]).to_dataset(name='dsx0')
        dsx1 = DataArray([1, 1], [('x', ['b', 'c'])]).to_dataset(name='dsx1')

        actual = dsx0.combine_first(dsx1)
        expected = Dataset({'dsx0': ('x', [0, 0, np.nan]),
                            'dsx1': ('x', [np.nan, 1, 1])},
                           coords={'x': ['a', 'b', 'c']})
        self.assertDatasetEqual(actual, expected)
        self.assertDatasetEqual(actual, xr.merge([dsx0, dsx1]))

        # works just like xr.merge([self, other])
        dsy2 = DataArray([2, 2, 2],
                         [('x', ['b', 'c', 'd'])]).to_dataset(name='dsy2')
        actual = dsx0.combine_first(dsy2)
        expected = xr.merge([dsy2, dsx0])
        self.assertDatasetEqual(actual, expected)

    def test_sortby(self):
        ds = Dataset({'A': DataArray([[1, 2], [3, 4], [5, 6]],
                                     [('x', ['c', 'b', 'a']),
                                      ('y', [1, 0])]),
                      'B': DataArray([[5, 6], [7, 8], [9, 10]],
                                     dims=['x', 'y'])})

        sorted1d = Dataset({'A': DataArray([[5, 6], [3, 4], [1, 2]],
                                           [('x', ['a', 'b', 'c']),
                                            ('y', [1, 0])]),
                            'B': DataArray([[9, 10], [7, 8], [5, 6]],
                                           dims=['x', 'y'])})

        sorted2d = Dataset({'A': DataArray([[6, 5], [4, 3], [2, 1]],
                                           [('x', ['a', 'b', 'c']),
                                            ('y', [0, 1])]),
                            'B': DataArray([[10, 9], [8, 7], [6, 5]],
                                           dims=['x', 'y'])})

        expected = sorted1d
        dax = DataArray([100, 99, 98], [('x', ['c', 'b', 'a'])])
        actual = ds.sortby(dax)
        self.assertDatasetEqual(actual, expected)

        # test descending order sort
        actual = ds.sortby(dax, ascending=False)
        self.assertDatasetEqual(actual, ds)

        # test alignment (fills in nan for 'c')
        dax_short = DataArray([98, 97], [('x', ['b', 'a'])])
        actual = ds.sortby(dax_short)
        self.assertDatasetEqual(actual, expected)

        # test 1-D lexsort
        # dax0 is sorted first to give indices of [1, 2, 0]
        # and then dax1 would be used to move index 2 ahead of 1
        dax0 = DataArray([100, 95, 95], [('x', ['c', 'b', 'a'])])
        dax1 = DataArray([0, 1, 0], [('x', ['c', 'b', 'a'])])
        actual = ds.sortby([dax0, dax1])  # lexsort underneath gives [2, 1, 0]
        self.assertDatasetEqual(actual, expected)

        expected = sorted2d
        # test multi-dim sort by 1D dataarray values
        day = DataArray([90, 80], [('y', [1, 0])])
        actual = ds.sortby([day, dax])
        self.assertDatasetEqual(actual, expected)

        # test exception-raising
        with pytest.raises(KeyError) as excinfo:
            actual = ds.sortby('z')

        with pytest.raises(ValueError) as excinfo:
            actual = ds.sortby(ds['A'])
        assert "DataArray is not 1-D" in str(excinfo.value)

        if LooseVersion(np.__version__) < LooseVersion('1.11.0'):
            pytest.skip('numpy 1.11.0 or later to support object data-type.')

        expected = sorted1d
        actual = ds.sortby('x')
        self.assertDatasetEqual(actual, expected)

        # test pandas.MultiIndex
        indices = (('b', 1), ('b', 0), ('a', 1), ('a', 0))
        midx = pd.MultiIndex.from_tuples(indices, names=['one', 'two'])
        ds_midx = Dataset({'A': DataArray([[1, 2], [3, 4], [5, 6], [7, 8]],
                                          [('x', midx), ('y', [1, 0])]),
                           'B': DataArray([[5, 6], [7, 8], [9, 10], [11, 12]],
                                          dims=['x', 'y'])})
        actual = ds_midx.sortby('x')
        midx_reversed = pd.MultiIndex.from_tuples(tuple(reversed(indices)),
                                                  names=['one', 'two'])
        expected = Dataset({'A': DataArray([[7, 8], [5, 6], [3, 4], [1, 2]],
                                           [('x', midx_reversed),
                                            ('y', [1, 0])]),
                            'B': DataArray([[11, 12], [9, 10], [7, 8], [5, 6]],
                                           dims=['x', 'y'])})
        self.assertDatasetEqual(actual, expected)

        # multi-dim sort by coordinate objects
        expected = sorted2d
        actual = ds.sortby(['x', 'y'])
        self.assertDatasetEqual(actual, expected)

        # test descending order sort
        actual = ds.sortby(['x', 'y'], ascending=False)
        self.assertDatasetEqual(actual, ds)


# Py.test tests


@pytest.fixture()
def data_set(seed=None):
    return create_test_data(seed)


def test_dir_expected_attrs(data_set):

    some_expected_attrs = {'pipe', 'mean', 'isnull', 'var1',
                           'dim2', 'numbers'}
    result = dir(data_set)
    assert set(result) >= some_expected_attrs

def test_dir_non_string(data_set):
    # add a numbered key to ensure this doesn't break dir
    data_set[5] = 'foo'
    result = dir(data_set)
    assert not (5 in result)

def test_dir_unicode(data_set):
    data_set[u'unicode'] = 'uni'
    result = dir(data_set)
    assert u'unicode' in result


@pytest.fixture(params=[1])
def ds(request):
    if request.param == 1:
        return Dataset({'z1': (['y', 'x'], np.random.randn(2, 8)),
                        'z2': (['time', 'y'], np.random.randn(10, 2))},
                       {'x': ('x', np.linspace(0, 1.0, 8)),
                        'time': ('time', np.linspace(0, 1.0, 10)),
                        'c': ('y', ['a', 'b']),
                        'y': range(2)})

    if request.param == 2:
        return Dataset({'z1': (['time', 'y'], np.random.randn(10, 2)),
                        'z2': (['time'], np.random.randn(10)),
                        'z3': (['x', 'time'], np.random.randn(8, 10))},
                       {'x': ('x', np.linspace(0, 1.0, 8)),
                        'time': ('time', np.linspace(0, 1.0, 10)),
                        'c': ('y', ['a', 'b']),
                        'y': range(2)})


def test_rolling_properties(ds):
    pytest.importorskip('bottleneck', minversion='1.0')

    # catching invalid args
    with pytest.raises(ValueError) as exception:
        ds.rolling(time=7, x=2)
    assert 'exactly one dim/window should' in str(exception)
    with pytest.raises(ValueError) as exception:
        ds.rolling(time=-2)
    assert 'window must be > 0' in str(exception)
    with pytest.raises(ValueError) as exception:
        ds.rolling(time=2, min_periods=0)
    assert 'min_periods must be greater than zero' in str(exception)
    with pytest.raises(KeyError) as exception:
        ds.rolling(time2=2)
    assert 'time2' in str(exception)

@pytest.mark.parametrize('name',
                         ('sum', 'mean', 'std', 'var', 'min', 'max', 'median'))
@pytest.mark.parametrize('center', (True, False, None))
@pytest.mark.parametrize('min_periods', (1, None))
@pytest.mark.parametrize('key', ('z1', 'z2'))
def test_rolling_wrapped_bottleneck(ds, name, center, min_periods, key):
    pytest.importorskip('bottleneck')
    import bottleneck as bn

    # skip if median and min_periods
    if (min_periods == 1) and (name == 'median'):
        pytest.skip()

    # Test all bottleneck functions
    rolling_obj = ds.rolling(time=7, min_periods=min_periods)

    func_name = 'move_{0}'.format(name)
    actual = getattr(rolling_obj, name)()
    if key is 'z1':  # z1 does not depend on 'Time' axis. Stored as it is.
        expected = ds[key]
    elif key is 'z2':
        expected = getattr(bn, func_name)(ds[key].values, window=7, axis=0,
                                          min_count=min_periods)
    assert_array_equal(actual[key].values, expected)

    # Test center
    rolling_obj = ds.rolling(time=7, center=center)
    actual = getattr(rolling_obj, name)()['time']
    assert_equal(actual, ds['time'])


def test_rolling_invalid_args(ds):
    pytest.importorskip('bottleneck', minversion="1.0")
    import bottleneck as bn
    if LooseVersion(bn.__version__) >= LooseVersion('1.1'):
        pytest.skip('rolling median accepts min_periods for bottleneck 1.1')
    with pytest.raises(ValueError) as exception:
        da.rolling(time=7, min_periods=1).median()
    assert 'Rolling.median does not' in str(exception)


@pytest.mark.parametrize('center', (True, False))
@pytest.mark.parametrize('min_periods', (None, 1, 2, 3))
@pytest.mark.parametrize('window', (1, 2, 3, 4))
def test_rolling_pandas_compat(center, window, min_periods):
    df = pd.DataFrame({'x': np.random.randn(20), 'y': np.random.randn(20),
                       'time': np.linspace(0, 1, 20)})
    ds = Dataset.from_dataframe(df)

    if min_periods is not None and window < min_periods:
        min_periods = window

    df_rolling = df.rolling(window, center=center,
                            min_periods=min_periods).mean()
    ds_rolling = ds.rolling(index=window, center=center,
                            min_periods=min_periods).mean()
    # pandas does some fancy stuff in the last position,
    # we're not going to do that yet!
    np.testing.assert_allclose(df_rolling['x'].values[:-1],
                               ds_rolling['x'].values[:-1])
    np.testing.assert_allclose(df_rolling.index,
                               ds_rolling['index'])


@pytest.mark.slow
@pytest.mark.parametrize('ds', (1, 2), indirect=True)
@pytest.mark.parametrize('center', (True, False))
@pytest.mark.parametrize('min_periods', (None, 1, 2, 3))
@pytest.mark.parametrize('window', (1, 2, 3, 4))
@pytest.mark.parametrize('name',
                         ('sum', 'mean', 'std', 'var', 'min', 'max', 'median'))
def test_rolling_reduce(ds, center, min_periods, window, name):

    if min_periods is not None and window < min_periods:
        min_periods = window

    # std with window == 1 seems unstable in bottleneck
    if name == 'std' and window == 1:
        window = 2
    if name == 'median':
        min_periods = None

    rolling_obj = ds.rolling(time=window, center=center,
                             min_periods=min_periods)

    # add nan prefix to numpy methods to get similar behavior as bottleneck
    actual = rolling_obj.reduce(getattr(np, 'nan%s' % name))
    expected = getattr(rolling_obj, name)()
    assert_allclose(actual, expected)
    assert ds.dims == actual.dims
    # make sure the order of data_var are not changed.
    assert list(ds.data_vars.keys()) == list(actual.data_vars.keys())

    # Make sure the dimension order is restored
    for key, src_var in ds.data_vars.items():
        assert src_var.dims == actual[key].dims
