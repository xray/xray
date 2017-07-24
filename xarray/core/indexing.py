from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from datetime import timedelta
from collections import defaultdict
import numpy as np
import pandas as pd

from . import utils
from .pycompat import (iteritems, range, integer_types, dask_array_type,
                       suppress)
from .utils import is_full_slice, is_dict_like


def expanded_indexer(key, ndim):
    """Given a key for indexing an ndarray, return an equivalent key which is a
    tuple with length equal to the number of dimensions.

    The expansion is done by replacing all `Ellipsis` items with the right
    number of full slices and then padding the key with full slices so that it
    reaches the appropriate dimensionality.
    """
    if not isinstance(key, tuple):
        # numpy treats non-tuple keys equivalent to tuples of length 1
        key = (key,)
    new_key = []
    # handling Ellipsis right is a little tricky, see:
    # http://docs.scipy.org/doc/numpy/reference/arrays.indexing.html#advanced-indexing
    found_ellipsis = False
    for k in key:
        if k is Ellipsis:
            if not found_ellipsis:
                new_key.extend((ndim + 1 - len(key)) * [slice(None)])
                found_ellipsis = True
            else:
                new_key.append(slice(None))
        else:
            new_key.append(k)
    if len(new_key) > ndim:
        raise IndexError('too many indices')
    new_key.extend((ndim - len(new_key)) * [slice(None)])
    return tuple(new_key)


def canonicalize_indexer(key, ndim):
    """Given an indexer for orthogonal array indexing, return an indexer that
    is a tuple composed entirely of slices, integer ndarrays and native python
    ints.
    """
    def canonicalize(indexer):
        if not isinstance(indexer, slice):
            indexer = np.asarray(indexer)
            if indexer.ndim == 0:
                indexer = int(np.asscalar(indexer))
            else:
                if indexer.ndim != 1:
                    raise ValueError('orthogonal array indexing only supports '
                                     '1d arrays')
                if indexer.dtype.kind == 'b':
                    indexer, = np.nonzero(indexer)
                elif indexer.dtype.kind != 'i':
                    raise ValueError('invalid subkey %r for integer based '
                                     'array indexing; all subkeys must be '
                                     'slices, integers or sequences of '
                                     'integers or Booleans' % indexer)
        return indexer

    return tuple(canonicalize(k) for k in expanded_indexer(key, ndim))


def _expand_slice(slice_, size):
    return np.arange(*slice_.indices(size))


def maybe_convert_to_slice(indexer, size):
    """Convert an indexer into an equivalent slice object, if possible.

    Arguments
    ---------
    indexer : int, slice or np.ndarray
        If a numpy array, must have integer dtype.
    size : integer
        Integer size of the dimension to be indexed.
    """
    if indexer.ndim != 1 or not isinstance(indexer, np.ndarray):
        return indexer

    if indexer.size == 0:
        return slice(0, 0)

    if indexer.min() < -size or indexer.max() >= size:
        raise IndexError(
            'indexer has elements out of bounds for axis of size {}: {}'
            .format(size, indexer))

    indexer = np.where(indexer < 0, indexer + size, indexer)
    if indexer.size == 1:
        i = int(indexer[0])
        return slice(i, i + 1)

    start = int(indexer[0])
    step = int(indexer[1] - start)
    stop = start + step * indexer.size
    guess = slice(start, stop, step)
    if np.array_equal(_expand_slice(guess, size), indexer):
        return guess
    return indexer


# TODO should be deprecated
def orthogonal_indexer(key, shape):
    """Given a key for orthogonal array indexing, returns an equivalent key
    suitable for indexing a numpy.ndarray with fancy indexing.
    """
    # replace Ellipsis objects with slices
    key = list(canonicalize_indexer(key, len(shape)))
    # replace 1d arrays and slices with broadcast compatible arrays
    # note: we treat integers separately (instead of turning them into 1d
    # arrays) because integers (and only integers) collapse axes when used with
    # __getitem__
    non_int_keys = [n for n, k in enumerate(key)
                    if not isinstance(k, integer_types)]

    def full_slices_unselected(n_list):
        def all_full_slices(key_index):
            return all(is_full_slice(key[n]) for n in key_index)
        if not n_list:
            return n_list
        elif all_full_slices(range(n_list[0] + 1)):
            return full_slices_unselected(n_list[1:])
        elif all_full_slices(range(n_list[-1], len(key))):
            return full_slices_unselected(n_list[:-1])
        else:
            return n_list

    # However, testing suggests it is OK to keep contiguous sequences of full
    # slices at the start or the end of the key. Keeping slices around (when
    # possible) instead of converting slices to arrays significantly speeds up
    # indexing.
    # (Honestly, I don't understand when it's not OK to keep slices even in
    # between integer indices if as array is somewhere in the key, but such are
    # the admittedly mind-boggling ways of numpy's advanced indexing.)
    array_keys = full_slices_unselected(non_int_keys)

    def maybe_expand_slice(k, length):
        return _expand_slice(k, length) if isinstance(k, slice) else k

    array_indexers = np.ix_(*(maybe_expand_slice(key[n], shape[n])
                              for n in array_keys))
    for i, n in enumerate(array_keys):
        key[n] = array_indexers[i]
    return tuple(key)


def _try_get_item(x):
    try:
        return x.item()
    except AttributeError:
        return x


def _asarray_tuplesafe(values):
    """
    Convert values into a numpy array of at most 1-dimension, while preserving
    tuples.

    Adapted from pandas.core.common._asarray_tuplesafe
    """
    if isinstance(values, tuple):
        result = utils.to_0d_object_array(values)
    else:
        result = np.asarray(values)
        if result.ndim == 2:
            result = np.empty(len(values), dtype=object)
            result[:] = values

    return result


def _is_nested_tuple(possible_tuple):
    return (isinstance(possible_tuple, tuple)
            and any(isinstance(value, (tuple, list, slice))
                    for value in possible_tuple))


def _index_method_kwargs(method, tolerance):
    # backwards compatibility for pandas<0.16 (method) or pandas<0.17
    # (tolerance)
    kwargs = {}
    if method is not None:
        kwargs['method'] = method
    if tolerance is not None:
        kwargs['tolerance'] = tolerance
    return kwargs


def get_loc(index, label, method=None, tolerance=None):
    kwargs = _index_method_kwargs(method, tolerance)
    return index.get_loc(label, **kwargs)


def get_indexer(index, labels, method=None, tolerance=None):
    kwargs = _index_method_kwargs(method, tolerance)
    return index.get_indexer(labels, **kwargs)


def convert_label_indexer(index, label, index_name='', method=None,
                          tolerance=None):
    """Given a pandas.Index and labels (e.g., from __getitem__) for one
    dimension, return an indexer suitable for indexing an ndarray along that
    dimension. If `index` is a pandas.MultiIndex and depending on `label`,
    return a new pandas.Index or pandas.MultiIndex (otherwise return None).
    """
    new_index = None

    if isinstance(label, slice):
        if method is not None or tolerance is not None:
            raise NotImplementedError(
                'cannot use ``method`` argument if any indexers are '
                'slice objects')
        indexer = index.slice_indexer(_try_get_item(label.start),
                                      _try_get_item(label.stop),
                                      _try_get_item(label.step))
        if not isinstance(indexer, slice):
            # unlike pandas, in xarray we never want to silently convert a slice
            # indexer into an array indexer
            raise KeyError('cannot represent labeled-based slice indexer for '
                           'dimension %r with a slice over integer positions; '
                           'the index is unsorted or non-unique' % index_name)

    elif is_dict_like(label):
        is_nested_vals = _is_nested_tuple(tuple(label.values()))
        if not isinstance(index, pd.MultiIndex):
            raise ValueError('cannot use a dict-like object for selection on a '
                             'dimension that does not have a MultiIndex')
        elif len(label) == index.nlevels and not is_nested_vals:
            indexer = index.get_loc(tuple((label[k] for k in index.names)))
        else:
            indexer, new_index = index.get_loc_level(tuple(label.values()),
                                                     level=tuple(label.keys()))

    elif isinstance(label, tuple) and isinstance(index, pd.MultiIndex):
        if _is_nested_tuple(label):
            indexer = index.get_locs(label)
        elif len(label) == index.nlevels:
            indexer = index.get_loc(label)
        else:
            indexer, new_index = index.get_loc_level(
                label, level=list(range(len(label)))
            )

    else:
        label = _asarray_tuplesafe(label)
        if label.ndim == 0:
            if isinstance(index, pd.MultiIndex):
                indexer, new_index = index.get_loc_level(label.item(), level=0)
            else:
                indexer = get_loc(index, label.item(), method, tolerance)
        elif label.dtype.kind == 'b':
            indexer, = np.nonzero(label)
        else:
            indexer = get_indexer(index, label, method, tolerance)
            if np.any(indexer < 0):
                raise KeyError('not all values found in index %r'
                               % index_name)
    return indexer, new_index


def get_dim_indexers(data_obj, indexers):
    """Given a xarray data object and label based indexers, return a mapping
    of label indexers with only dimension names as keys.

    It groups multiple level indexers given on a multi-index dimension
    into a single, dictionary indexer for that dimension (Raise a ValueError
    if it is not possible).
    """
    invalid = [k for k in indexers
               if k not in data_obj.dims and k not in data_obj._level_coords]
    if invalid:
        raise ValueError("dimensions or multi-index levels %r do not exist"
                         % invalid)

    level_indexers = defaultdict(dict)
    dim_indexers = {}
    for key, label in iteritems(indexers):
        dim, = data_obj[key].dims
        if key != dim:
            # assume here multi-index level indexer
            level_indexers[dim][key] = label
        else:
            dim_indexers[key] = label

    for dim, level_labels in iteritems(level_indexers):
        if dim_indexers.get(dim, False):
            raise ValueError("cannot combine multi-index level indexers "
                             "with an indexer for dimension %s" % dim)
        dim_indexers[dim] = level_labels

    return dim_indexers


def remap_label_indexers(data_obj, indexers, method=None, tolerance=None):
    """Given an xarray data object and label based indexers, return a mapping
    of equivalent location based indexers. Also return a mapping of updated
    pandas index objects (in case of multi-index level drop).
    """
    if method is not None and not isinstance(method, str):
        raise TypeError('``method`` must be a string')

    pos_indexers = {}
    new_indexes = {}

    dim_indexers = get_dim_indexers(data_obj, indexers)
    for dim, label in iteritems(dim_indexers):
        try:
            index = data_obj.indexes[dim]
        except KeyError:
            # no index for this dimension: reuse the provided labels
            if method is not None or tolerance is not None:
                raise ValueError('cannot supply ``method`` or ``tolerance`` '
                                 'when the indexed dimension does not have '
                                 'an associated coordinate.')
            pos_indexers[dim] = label
        else:
            idxr, new_idx = convert_label_indexer(index, label,
                                                  dim, method, tolerance)
            pos_indexers[dim] = idxr
            if new_idx is not None:
                new_indexes[dim] = new_idx

    return pos_indexers, new_indexes


def slice_slice(old_slice, applied_slice, size):
    """Given a slice and the size of the dimension to which it will be applied,
    index it with another slice to return a new slice equivalent to applying
    the slices sequentially
    """
    step = (old_slice.step or 1) * (applied_slice.step or 1)

    # For now, use the hack of turning old_slice into an ndarray to reconstruct
    # the slice start and stop. This is not entirely ideal, but it is still
    # definitely better than leaving the indexer as an array.
    items = _expand_slice(old_slice, size)[applied_slice]
    if len(items) > 0:
        start = items[0]
        stop = items[-1] + step
        if stop < 0:
            stop = None
    else:
        start = 0
        stop = 0
    return slice(start, stop, step)


def _index_indexer_1d(old_indexer, applied_indexer, size):
    assert isinstance(applied_indexer, integer_types + (slice, np.ndarray))
    if isinstance(applied_indexer, slice) and applied_indexer == slice(None):
        # shortcut for the usual case
        return old_indexer
    if isinstance(old_indexer, slice):
        if isinstance(applied_indexer, slice):
            indexer = slice_slice(old_indexer, applied_indexer, size)
        else:
            indexer = _expand_slice(old_indexer, size)[applied_indexer]
    else:
        indexer = old_indexer[applied_indexer]
    return indexer


class IndexableArrayAdapter(object):
    """ Base class for array adapters subject for orthogonal-indexing or
    broadcasted-indexing.

    indexing_type: One of `orthogonal` or `broadcast`
    """
    def __init__(self, indexing_type='orthogonal'):
        assert indexing_type in ['orthogonal', 'broadcast']
        self._indexing_type = indexing_type

    @property
    def indexing_type(self):
        return self._indexing_type


def indexing_type_of(array):
    if isinstance(array, np.ndarray):
        return 'broadcast'
    else:
        return getattr(array, 'indexing_type', 'orthogonal')


class LazilyIndexedArray(IndexableArrayAdapter, utils.NDArrayMixin):
    """Wrap an array that handles orthogonal indexing to make indexing lazy

    This is array is indexed by broadcasted-indexing. For using broadcasted
    indexers, use LazilyIndexedArray.
    """
    def __init__(self, array, key=None):
        """
        Parameters
        ----------
        array : array_like
            Array like object to index.
        key : tuple, optional
            Array indexer. If provided, it is assumed to already be in
            canonical expanded form.
        """
        super(LazilyIndexedArray, self).__init__(indexing_type='broadcast')
        # We need to ensure that self.array is not LazilyIndexedArray,
        # because LazilyIndexedArray is not orthogonaly indexable
        if isinstance(array, type(self)):
            self.array = array.array
            self.key = array.key
            if key is not None:
                self.key = self._updated_key(key)

        else:
            if key is None:
                key = (slice(None),) * array.ndim
            self.array = array
            self.key = key

    def _updated_key(self, new_key):
        new_key = iter(new_key)
        key = []
        for size, k in zip(self.array.shape, self.key):
            if isinstance(k, integer_types):
                key.append(k)
            else:
                key.append(_index_indexer_1d(k, next(new_key), size))
        return tuple(key)

    @property
    def shape(self):
        shape = []
        for size, k in zip(self.array.shape, self.key):
            if isinstance(k, slice):
                shape.append(len(range(*k.indices(size))))
            elif isinstance(k, np.ndarray):
                shape.append(k.size)
        return tuple(shape)

    def __array__(self, dtype=None):
        if indexing_type_of(self.array) == 'broadcast':
            # manual orthogonal indexing.
            value = np.asarray(self.array, dtype=None)
            for axis, subkey in reversed(list(enumerate(self.key))):
                value = value[(slice(None),) * axis + (subkey,)]
            return value
        else:
            return np.asarray(self.array[self.key], dtype=None)

    def __getitem__(self, key):
        key = expanded_indexer(key, self.ndim)
        key = unbroadcast_indexes(key, self.shape)
        return type(self)(self.array, self._updated_key(key))

    def __setitem__(self, key, value):
        key = expanded_indexer(key, self.ndim)
        key = unbroadcast_indexes(key, self.shape)
        key = self._updated_key(key)

        if indexing_type_of(self.array) == 'broadcast':
            # TODO Should prepare LazilyIndexedArray for
            # BroadcastIndexableAdapter
            raise NotImplementedError('LaziyIndexedArray wrapps '
                                      'OrthogonalIndexableAdapter.')
        self.array[key] = value

    def __repr__(self):
        return ('%s(array=%r, key=%r)' %
                (type(self).__name__, self.array, self.key))


def _wrap_numpy_scalars(array):
    """Wrap NumPy scalars in 0d arrays."""
    if np.isscalar(array):
        return np.array(array)
    else:
        return array


class CopyOnWriteArray(IndexableArrayAdapter, utils.NDArrayMixin):
    def __init__(self, array):
        super(CopyOnWriteArray, self).__init__(indexing_type_of(array))
        self.array = array
        self._copied = False

    def _ensure_copied(self):
        if not self._copied:
            self.array = np.array(self.array)
            self._copied = True

    def __array__(self, dtype=None):
        return np.asarray(self.array, dtype=dtype)

    def __getitem__(self, key):
        return type(self)(_wrap_numpy_scalars(self.array[key]))

    def __setitem__(self, key, value):
        self._ensure_copied()
        self.array[key] = value


class MemoryCachedArray(IndexableArrayAdapter, utils.NDArrayMixin):
    def __init__(self, array):
        super(MemoryCachedArray, self).__init__(indexing_type_of(array))
        self.array = _wrap_numpy_scalars(array)

    def _ensure_cached(self):
        if not isinstance(self.array, np.ndarray):
            self.array = np.asarray(self.array)

    def __array__(self, dtype=None):
        self._ensure_cached()
        return np.asarray(self.array, dtype=dtype)

    def __getitem__(self, key):
        return type(self)(_wrap_numpy_scalars(self.array[key]))

    def __setitem__(self, key, value):
        self.array[key] = value


def unbroadcast_indexes(key, shape):
    """
    Convert broadcasted indexers to orthogonal indexers.
    If there is no valid mapping, raises IndexError.

    key is usually generated by Variable._broadcast_indexes.

    key: tuple of np.ndarray, slice, integer
    shape: shape of array
    """
    key = expanded_indexer(key, len(shape))

    if all(isinstance(k, integer_types + (slice,)) for k in key):
        # basic indexing
        return key

    i_dim = 0
    orthogonal_keys = []
    for k in key:
        if hasattr(k, '__len__'):  # array
            if k.shape[i_dim] != k.size:
                raise IndexError(
                    "Indexer cannot be orthogonalized: {}".format(k))
            else:
                i_dim += 1
                orthogonal_keys.append(np.ravel(k))
        else:  # integer
            orthogonal_keys.append(k)
    return tuple(orthogonal_keys)


class BroadcastIndexedAdapter(IndexableArrayAdapter, utils.NDArrayMixin):
    """ An array wrapper for orthogonally indexed arrays, such as netCDF
    in order to indexed by broadcasted indexers. """
    def __init__(self, array):
        super(BroadcastIndexedAdapter, self).__init__('broadcast')
        self.array = array

    def __array__(self, dtype=None):
        return np.asarray(self.array, dtype=dtype)

    def __getitem__(self, key):
        key = expanded_indexer(key, self.ndim)
        key = unbroadcast_indexes(key, self.shape)
        return type(self)(self.array[key])

    def __setitem__(self, key, value):
        key = expanded_indexer(key, self.ndim)
        key = unbroadcast_indexes(key, self.shape)
        self.array[key] = value


def broadcasted_indexable(array):
    if isinstance(array, np.ndarray):
        return NumpyIndexingAdapter(array)
    if isinstance(array, pd.Index):
        return PandasIndexAdapter(array)
    if isinstance(array, dask_array_type):
        return DaskIndexingAdapter(array)
    return array


class NumpyIndexingAdapter(IndexableArrayAdapter, utils.NDArrayMixin):
    """Wrap a NumPy array to use broadcasted indexing
    """
    def __init__(self, array):
        super(NumpyIndexingAdapter, self).__init__('broadcast')
        self.array = array

    def _ensure_ndarray(self, value):
        # We always want the result of indexing to be a NumPy array. If it's
        # not, then it really should be a 0d array. Doing the coercion here
        # instead of inside variable.as_compatible_data makes it less error
        # prone.
        if not isinstance(value, np.ndarray):
            value = utils.to_0d_array(value)
        return value

    def __getitem__(self, key):
        return self._ensure_ndarray(self.array[key])

    def __setitem__(self, key, value):
        self.array[key] = value


class DaskIndexingAdapter(IndexableArrayAdapter, utils.NDArrayMixin):
    """Wrap a dask array to support broadcasted-indexing.
    """
    def __init__(self, array):
        """ This adapter is usually called in Variable.__getitem__ with
        array=Variable._broadcast_indexes
        """
        super(DaskIndexingAdapter, self).__init__('broadcast')
        self.array = array

    def _orthogonalize_indexes(self, key):
        key = unbroadcast_indexes(key, self.shape)
        # convert them to slice if possible
        return tuple(k if isinstance(k, (integer_types, slice))
                     else maybe_convert_to_slice(k, size)
                     for k, size in zip(key, self.shape))

    def __getitem__(self, key):
        try:
            key = self._orthogonalize_indexes(key)
            try:
                return self.array[key]
            except NotImplementedError:
                # manual orthogonal indexing.
                value = self.array
                for axis, subkey in reversed(list(enumerate(key))):
                    value = value[(slice(None),) * axis + (subkey,)]
                return value
        except IndexError:
            # TODO should support vindex
            raise IndexError(
              'dask does not support fancy indexing with key: {}'.format(key))

    def __setitem__(self, key, value):
        key = self._orthogonalize_indexes(key)
        raise TypeError("this variable's data is stored in a dask array, "
                        'which does not support item assignment. To '
                        'assign to this variable, you must first load it '
                        'into memory explicitly using the .load_data() '
                        'method or accessing its .values attribute.')
        self.array[key] = value


class PandasIndexAdapter(IndexableArrayAdapter, utils.NDArrayMixin):
    """Wrap a pandas.Index to be better about preserving dtypes and to handle
    indexing by length 1 tuples like numpy
    """
    def __init__(self, array, dtype=None):
        super(PandasIndexAdapter, self).__init__('broadcast')
        self.array = utils.safe_cast_to_index(array)
        if dtype is None:
            if isinstance(array, pd.PeriodIndex):
                dtype = np.dtype('O')
            elif hasattr(array, 'categories'):
                # category isn't a real numpy dtype
                dtype = array.categories.dtype
            elif not utils.is_valid_numpy_dtype(array.dtype):
                dtype = np.dtype('O')
            else:
                dtype = array.dtype
        self._dtype = dtype

    @property
    def dtype(self):
        return self._dtype

    def __array__(self, dtype=None):
        if dtype is None:
            dtype = self.dtype
        array = self.array
        if isinstance(array, pd.PeriodIndex):
            with suppress(AttributeError):
                # this might not be public API
                array = array.asobject
        return np.asarray(array.values, dtype=dtype)

    @property
    def shape(self):
        # .shape is broken on pandas prior to v0.15.2
        return (len(self.array),)

    def __getitem__(self, key):
        if isinstance(key, tuple) and len(key) == 1:
            # unpack key so it can index a pandas.Index object (pandas.Index
            # objects don't like tuples)
            key, = key

        result = self.array[key]

        if isinstance(result, pd.Index):
            result = PandasIndexAdapter(result, dtype=self.dtype)
        else:
            # result is a scalar
            if result is pd.NaT:
                # work around the impossibility of casting NaT with asarray
                # note: it probably would be better in general to return
                # pd.Timestamp rather np.than datetime64 but this is easier
                # (for now)
                result = np.datetime64('NaT', 'ns')
            elif isinstance(result, timedelta):
                result = np.timedelta64(getattr(result, 'value', result), 'ns')
            elif self.dtype != object:
                result = np.asarray(result, dtype=self.dtype)

            # as for numpy.ndarray indexing, we always want the result to be
            # a NumPy array.
            result = utils.to_0d_array(result)

        return result

    def __repr__(self):
        return ('%s(array=%r, dtype=%r)'
                % (type(self).__name__, self.array, self.dtype))
