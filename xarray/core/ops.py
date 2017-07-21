"""Define core operations for xarray objects.

TODO(shoyer): rewrite this module, making use of xarray.core.computation,
NumPy's __array_ufunc__ and mixin classes instead of the unintuitive "inject"
functions.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import operator
from distutils.version import LooseVersion

import numpy as np
import pandas as pd

from . import duck_array_ops
from .pycompat import PY3
from .nputils import array_eq, array_ne

try:
    import bottleneck as bn
    has_bottleneck = True
except ImportError:
    # use numpy methods instead
    bn = np
    has_bottleneck = False


UNARY_OPS = ['neg', 'pos', 'abs', 'invert']
CMP_BINARY_OPS = ['lt', 'le', 'ge', 'gt']
NUM_BINARY_OPS = ['add', 'sub', 'mul', 'truediv', 'floordiv', 'mod',
                  'pow', 'and', 'xor', 'or']
if not PY3:
    NUM_BINARY_OPS.append('div')

# methods which pass on the numpy return value unchanged
# be careful not to list methods that we would want to wrap later
NUMPY_SAME_METHODS = ['item', 'searchsorted']
# methods which don't modify the data shape, so the result should still be
# wrapped in an Variable/DataArray
NUMPY_UNARY_METHODS = ['astype', 'argsort', 'clip', 'conj', 'conjugate']
PANDAS_UNARY_FUNCTIONS = ['isnull', 'notnull']
# methods which remove an axis
REDUCE_METHODS = ['all', 'any']
NAN_REDUCE_METHODS = ['argmax', 'argmin', 'max', 'min', 'mean', 'prod', 'sum',
                      'std', 'var', 'median']
NAN_CUM_METHODS = ['cumsum', 'cumprod']
BOTTLENECK_ROLLING_METHODS = {'move_sum': 'sum', 'move_mean': 'mean',
                              'move_std': 'std', 'move_min': 'min',
                              'move_max': 'max', 'move_var': 'var',
                              'move_argmin': 'argmin', 'move_argmax': 'argmax'}
# TODO: wrap take, dot, sort


_CUM_DOCSTRING_TEMPLATE = """\
Apply `{name}` along some dimension of {cls}.

Parameters
----------
{extra_args}
skipna : bool, optional
    If True, skip missing values (as marked by NaN). By default, only
    skips missing values for float dtypes; other dtypes either do not
    have a sentinel missing value (int) or skipna=True has not been
    implemented (object, datetime64 or timedelta64).
keep_attrs : bool, optional
    If True, the attributes (`attrs`) will be copied from the original
    object to the new one.  If False (default), the new object will be
    returned without attributes.
**kwargs : dict
    Additional keyword arguments passed on to `{name}`.

Returns
-------
cumvalue : {cls}
    New {cls} object with `{name}` applied to its data along the
    indicated dimension.
"""

_REDUCE_DOCSTRING_TEMPLATE = """\
Reduce this {cls}'s data by applying `{name}` along some dimension(s).

Parameters
----------
{extra_args}
skipna : bool, optional
    If True, skip missing values (as marked by NaN). By default, only
    skips missing values for float dtypes; other dtypes either do not
    have a sentinel missing value (int) or skipna=True has not been
    implemented (object, datetime64 or timedelta64).
keep_attrs : bool, optional
    If True, the attributes (`attrs`) will be copied from the original
    object to the new one.  If False (default), the new object will be
    returned without attributes.
**kwargs : dict
    Additional keyword arguments passed on to the appropriate array
    function for calculating `{name}` on this object's data.

Returns
-------
reduced : {cls}
    New {cls} object with `{name}` applied to its data and the
    indicated dimension(s) removed.
"""

_ROLLING_REDUCE_DOCSTRING_TEMPLATE = """\
Reduce this {da_or_ds}'s data windows by applying `{name}` along its dimension.

Parameters
----------
**kwargs : dict
    Additional keyword arguments passed on to `{name}`.

Returns
-------
reduced : {da_or_ds}
    New {da_or_ds} object with `{name}` applied along its rolling dimnension.
"""


def fillna(data, other, join="left", dataset_join="left"):
    """Fill missing values in this object with data from the other object.
    Follows normal broadcasting and alignment rules.

    Parameters
    ----------
    join : {'outer', 'inner', 'left', 'right'}, optional
        Method for joining the indexes of the passed objects along each
        dimension
        - 'outer': use the union of object indexes
        - 'inner': use the intersection of object indexes
        - 'left': use indexes from the first object with each dimension
        - 'right': use indexes from the last object with each dimension
        - 'exact': raise `ValueError` instead of aligning when indexes to be
          aligned are not equal
    dataset_join : {'outer', 'inner', 'left', 'right'}, optional
        Method for joining variables of Dataset objects with mismatched
        data variables.
        - 'outer': take variables from both Dataset objects
        - 'inner': take only overlapped variables
        - 'left': take only variables from the first object
        - 'right': take only variables from the last object
    """
    from .computation import apply_ufunc

    def _fillna(data, other):
        return duck_array_ops.where(duck_array_ops.isnull(data), other, data)
    return apply_ufunc(_fillna, data, other, join=join, dask_array="allowed",
                       dataset_join=dataset_join,
                       dataset_fill_value=np.nan,
                       keep_attrs=True)


def _call_possibly_missing_method(arg, name, args, kwargs):
    try:
        method = getattr(arg, name)
    except AttributeError:
        duck_array_ops.fail_on_dask_array_input(arg, func_name=name)
        if hasattr(arg, 'data'):
            duck_array_ops.fail_on_dask_array_input(arg.data, func_name=name)
        raise
    else:
        return method(*args, **kwargs)


def _values_method_wrapper(name):
    def func(self, *args, **kwargs):
        return _call_possibly_missing_method(self.data, name, args, kwargs)
    func.__name__ = name
    func.__doc__ = getattr(np.ndarray, name).__doc__
    return func


def _method_wrapper(name):
    def func(self, *args, **kwargs):
        return _call_possibly_missing_method(self, name, args, kwargs)
    func.__name__ = name
    func.__doc__ = getattr(np.ndarray, name).__doc__
    return func


def _func_slash_method_wrapper(f, name=None):
    # try to wrap a method, but if not found use the function
    # this is useful when patching in a function as both a DataArray and
    # Dataset method
    if name is None:
        name = f.__name__

    def func(self, *args, **kwargs):
        try:
            return getattr(self, name)(*args, **kwargs)
        except AttributeError:
            return f(self, *args, **kwargs)
    func.__name__ = name
    func.__doc__ = f.__doc__
    return func


def rolling_count(rolling):

    not_null = rolling.obj.notnull()
    instance_attr_dict = {'center': rolling.center,
                          'min_periods': rolling.min_periods,
                          rolling.dim: rolling.window}
    rolling_count = not_null.rolling(**instance_attr_dict).sum()

    if rolling.min_periods is None:
        return rolling_count

    # otherwise we need to filter out points where there aren't enough periods
    # but not_null is False, and so the NaNs don't flow through
    # array with points where there are enough values given min_periods
    enough_periods = rolling_count >= rolling.min_periods

    return rolling_count.where(enough_periods)

def inject_reduce_methods(cls):
    methods = ([(name, getattr(duck_array_ops, 'array_%s' % name), False)
                for name in REDUCE_METHODS] +
               [(name, getattr(duck_array_ops, name), True)
                for name in NAN_REDUCE_METHODS] +
               [('count', duck_array_ops.count, False)])
    for name, f, include_skipna in methods:
        numeric_only = getattr(f, 'numeric_only', False)
        func = cls._reduce_method(f, include_skipna, numeric_only)
        func.__name__ = name
        func.__doc__ = _REDUCE_DOCSTRING_TEMPLATE.format(
            name=name, cls=cls.__name__,
            extra_args=cls._reduce_extra_args_docstring.format(name=name))
        setattr(cls, name, func)


def inject_cum_methods(cls):
    methods = ([(name, getattr(duck_array_ops, name), True)
               for name in NAN_CUM_METHODS])
    for name, f, include_skipna in methods:
        numeric_only = getattr(f, 'numeric_only', False)
        func = cls._reduce_method(f, include_skipna, numeric_only)
        func.__name__ = name
        func.__doc__ = _CUM_DOCSTRING_TEMPLATE.format(
            name=name, cls=cls.__name__,
            extra_args=cls._cum_extra_args_docstring.format(name=name))
        setattr(cls, name, func)


def op_str(name):
    return '__%s__' % name


def get_op(name):
    return getattr(operator, op_str(name))


NON_INPLACE_OP = dict((get_op('i' + name), get_op(name))
                      for name in NUM_BINARY_OPS)


def inplace_to_noninplace_op(f):
    return NON_INPLACE_OP[f]


def inject_binary_ops(cls, inplace=False):
    for name in CMP_BINARY_OPS + NUM_BINARY_OPS:
        setattr(cls, op_str(name), cls._binary_op(get_op(name)))

    for name, f in [('eq', array_eq), ('ne', array_ne)]:
        setattr(cls, op_str(name), cls._binary_op(f))

    # patch in where
    f = _func_slash_method_wrapper(duck_array_ops.where_method, 'where')
    setattr(cls, '_where', cls._binary_op(f))

    for name in NUM_BINARY_OPS:
        # only numeric operations have in-place and reflexive variants
        setattr(cls, op_str('r' + name),
                cls._binary_op(get_op(name), reflexive=True))
        if inplace:
            setattr(cls, op_str('i' + name),
                    cls._inplace_binary_op(get_op('i' + name)))


def inject_all_ops_and_reduce_methods(cls, priority=50, array_only=True):
    # prioritize our operations over those of numpy.ndarray (priority=1)
    # and numpy.matrix (priority=10)
    cls.__array_priority__ = priority

    # patch in standard special operations
    for name in UNARY_OPS:
        setattr(cls, op_str(name), cls._unary_op(get_op(name)))
    inject_binary_ops(cls, inplace=True)

    # patch in numpy/pandas methods
    for name in NUMPY_UNARY_METHODS:
        setattr(cls, name, cls._unary_op(_method_wrapper(name)))

    for name in PANDAS_UNARY_FUNCTIONS:
        f = _func_slash_method_wrapper(getattr(pd, name))
        setattr(cls, name, cls._unary_op(f))

    f = _func_slash_method_wrapper(duck_array_ops.around, name='round')
    setattr(cls, 'round', cls._unary_op(f))

    if array_only:
        # these methods don't return arrays of the same shape as the input, so
        # don't try to patch these in for Dataset objects
        for name in NUMPY_SAME_METHODS:
            setattr(cls, name, _values_method_wrapper(name))

    inject_reduce_methods(cls)
    inject_cum_methods(cls)


def inject_bottleneck_rolling_methods(cls):
    # standard numpy reduce methods
    methods = [(name, getattr(duck_array_ops, name))
               for name in NAN_REDUCE_METHODS]
    for name, f in methods:
        func = cls._reduce_method(f)
        func.__name__ = name
        func.__doc__ = _ROLLING_REDUCE_DOCSTRING_TEMPLATE.format(
            name=func.__name__, da_or_ds='DataArray')
        setattr(cls, name, func)

    # bottleneck doesn't offer rolling_count, so we construct it ourselves
    func = rolling_count
    func.__name__ = 'count'
    func.__doc__ = _ROLLING_REDUCE_DOCSTRING_TEMPLATE.format(
        name=func.__name__, da_or_ds='DataArray')
    setattr(cls, 'count', func)

    # bottleneck rolling methods
    if has_bottleneck:
        # TODO: Bump the required version of bottlneck to 1.1 and remove all
        # these version checks (see GH#1278)
        bn_version = LooseVersion(bn.__version__)
        bn_min_version = LooseVersion('1.0')
        bn_version_1_1 = LooseVersion('1.1')
        if bn_version < bn_min_version:
            return

        for bn_name, method_name in BOTTLENECK_ROLLING_METHODS.items():
            try:
                f = getattr(bn, bn_name)
                func = cls._bottleneck_reduce(f)
                func.__name__ = method_name
                func.__doc__ = _ROLLING_REDUCE_DOCSTRING_TEMPLATE.format(
                    name=func.__name__, da_or_ds='DataArray')
                setattr(cls, method_name, func)
            except AttributeError as e:
                # skip functions not in Bottleneck 1.0
                if ((bn_version < bn_version_1_1) and
                        (bn_name not in ['move_var', 'move_argmin',
                                         'move_argmax', 'move_rank'])):
                    raise e

        # bottleneck rolling methods without min_count (bn.__version__ < 1.1)
        f = getattr(bn, 'move_median')
        if bn_version >= bn_version_1_1:
            func = cls._bottleneck_reduce(f)
        else:
            func = cls._bottleneck_reduce_without_min_count(f)
        func.__name__ = 'median'
        func.__doc__ = _ROLLING_REDUCE_DOCSTRING_TEMPLATE.format(
            name=func.__name__, da_or_ds='DataArray')
        setattr(cls, 'median', func)


def inject_datasetrolling_methods(cls):
    # standard numpy reduce methods
    methods = [(name, getattr(duck_array_ops, name))
               for name in NAN_REDUCE_METHODS]
    for name, f in methods:
        func = cls._reduce_method(f)
        func.__name__ = name
        func.__doc__ = _ROLLING_REDUCE_DOCSTRING_TEMPLATE.format(
            name=func.__name__, da_or_ds='Dataset')
        setattr(cls, name, func)
    # bottleneck doesn't offer rolling_count, so we construct it ourselves
    func = rolling_count
    func.__name__ = 'count'
    func.__doc__ = _ROLLING_REDUCE_DOCSTRING_TEMPLATE.format(
        name=func.__name__, da_or_ds='Dataset')
    setattr(cls, 'count', func)
