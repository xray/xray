from __future__ import absolute_import, division, print_function

import itertools
import warnings
from collections import Counter

import pandas as pd

import numpy as np

from . import utils
from .alignment import align
from .merge import merge
from .pycompat import OrderedDict, basestring, iteritems
from .variable import IndexVariable, Variable, as_variable
from .variable import concat as concat_vars


def concat(objs, dim=None, data_vars='all', coords='different',
           compat='equals', positions=None, indexers=None, mode=None,
           concat_over=None):
    """Concatenate xarray objects along a new or existing dimension.

    Parameters
    ----------
    objs : sequence of Dataset and DataArray objects
        xarray objects to concatenate together. Each object is expected to
        consist of variables and coordinates with matching shapes except for
        along the concatenated dimension.
    dim : str or DataArray or pandas.Index
        Name of the dimension to concatenate along. This can either be a new
        dimension name, in which case it is added along axis=0, or an existing
        dimension name, in which case the location of the dimension is
        unchanged. If dimension is provided as a DataArray or Index, its name
        is used as the dimension to concatenate along and the values are added
        as a coordinate.
    data_vars : {'minimal', 'different', 'all' or list of str}, optional
        These data variables will be concatenated together:
          * 'minimal': Only data variables in which the dimension already
            appears are included.
          * 'different': Data variables which are not equal (ignoring
            attributes) across all datasets are also concatenated (as well as
            all for which dimension already appears). Beware: this option may
            load the data payload of data variables into memory if they are not
            already loaded.
          * 'all': All data variables will be concatenated.
          * list of str: The listed data variables will be concatenated, in
            addition to the 'minimal' data variables.
        If objects are DataArrays, data_vars must be 'all'.
    coords : {'minimal', 'different', 'all' or list of str}, optional
        These coordinate variables will be concatenated together:
          * 'minimal': Only coordinates in which the dimension already appears
            are included.
          * 'different': Coordinates which are not equal (ignoring attributes)
            across all datasets are also concatenated (as well as all for which
            dimension already appears). Beware: this option may load the data
            payload of coordinate variables into memory if they are not already
            loaded.
          * 'all': All coordinate variables will be concatenated, except
            those corresponding to other dimensions.
          * list of str: The listed coordinate variables will be concatenated,
            in addition the 'minimal' coordinates.
    compat : {'equals', 'identical'}, optional
        String indicating how to compare non-concatenated variables and
        dataset global attributes for potential conflicts. 'equals' means
        that all variable values and dimensions must be the same;
        'identical' means that variable attributes and global attributes
        must also be equal.
    positions : None or list of integer arrays, optional
        List of integer arrays which specifies the integer positions to which
        to assign each dataset along the concatenated dimension. If not
        supplied, objects are concatenated in the provided order.
    indexers, mode, concat_over : deprecated

    Returns
    -------
    concatenated : type of objs

    See also
    --------
    merge
    auto_combine
    """
    # TODO: add join and ignore_index arguments copied from pandas.concat
    # TODO: support concatenating scalar coordinates even if the concatenated
    # dimension already exists
    from .dataset import Dataset
    from .dataarray import DataArray

    try:
        first_obj, objs = utils.peek_at(objs)
    except StopIteration:
        raise ValueError('must supply at least one object to concatenate')

    if dim is None:
        warnings.warn('the `dim` argument to `concat` will be required '
                      'in a future version of xarray; for now, setting it to '
                      "the old default of 'concat_dim'",
                      FutureWarning, stacklevel=2)
        dim = 'concat_dims'

    if indexers is not None:  # pragma: nocover
        warnings.warn('indexers has been renamed to positions; the alias '
                      'will be removed in a future version of xarray',
                      FutureWarning, stacklevel=2)
        positions = indexers

    if mode is not None:
        raise ValueError('`mode` is no longer a valid argument to '
                         'xarray.concat; it has been split into the '
                         '`data_vars` and `coords` arguments')
    if concat_over is not None:
        raise ValueError('`concat_over` is no longer a valid argument to '
                         'xarray.concat; it has been split into the '
                         '`data_vars` and `coords` arguments')

    if isinstance(first_obj, DataArray):
        f = _dataarray_concat
    elif isinstance(first_obj, Dataset):
        f = _dataset_concat
    else:
        raise TypeError('can only concatenate xarray Dataset and DataArray '
                        'objects, got %s' % type(first_obj))
    return f(objs, dim, data_vars, coords, compat, positions)


def _calc_concat_dim_coord(dim):
    """
    Infer the dimension name and 1d coordinate variable (if appropriate)
    for concatenating along the new dimension.
    """
    from .dataarray import DataArray

    if isinstance(dim, basestring):
        coord = None
    elif not isinstance(dim, (DataArray, Variable)):
        dim_name = getattr(dim, 'name', None)
        if dim_name is None:
            dim_name = 'concat_dim'
        coord = IndexVariable(dim_name, dim)
        dim = dim_name
    elif not isinstance(dim, DataArray):
        coord = as_variable(dim).to_index_variable()
        dim, = coord.dims
    else:
        coord = dim
        dim, = coord.dims
    return dim, coord


def _calc_concat_over(datasets, dim, data_vars, coords):
    """
    Determine which dataset variables need to be concatenated in the result,
    and which can simply be taken from the first dataset.
    """
    # Return values
    concat_over = set()
    equals = {}

    if dim in datasets[0]:
        concat_over.add(dim)
    for ds in datasets:
        concat_over.update(k for k, v in ds.variables.items()
                           if dim in v.dims)

    def process_subset_opt(opt, subset):
        if isinstance(opt, basestring):
            if opt == 'different':
                # all nonindexes that are not the same in each dataset
                for k in getattr(datasets[0], subset):
                    if k not in concat_over:
                        # Compare the variable of all datasets vs. the one
                        # of the first dataset. Perform the minimum amount of
                        # loads in order to avoid multiple loads from disk
                        # while keeping the RAM footprint low.
                        v_lhs = datasets[0].variables[k].load()
                        # We'll need to know later on if variables are equal.
                        computed = []
                        for ds_rhs in datasets[1:]:
                            v_rhs = ds_rhs.variables[k].compute()
                            computed.append(v_rhs)
                            if not v_lhs.equals(v_rhs):
                                concat_over.add(k)
                                equals[k] = False
                                # computed variables are not to be re-computed
                                # again in the future
                                for ds, v in zip(datasets[1:], computed):
                                    ds.variables[k].data = v.data
                                break
                        else:
                            equals[k] = True

            elif opt == 'all':
                concat_over.update(set(getattr(datasets[0], subset)) -
                                   set(datasets[0].dims))
            elif opt == 'minimal':
                pass
            else:
                raise ValueError("unexpected value for %s: %s" % (subset, opt))
        else:
            invalid_vars = [k for k in opt
                            if k not in getattr(datasets[0], subset)]
            if invalid_vars:
                if subset == 'coords':
                    raise ValueError(
                        'some variables in coords are not coordinates on '
                        'the first dataset: %s' % (invalid_vars,))
                else:
                    raise ValueError(
                        'some variables in data_vars are not data variables '
                        'on the first dataset: %s' % (invalid_vars,))
            concat_over.update(opt)

    process_subset_opt(data_vars, 'data_vars')
    process_subset_opt(coords, 'coords')
    return concat_over, equals


def _dataset_concat(datasets, dim, data_vars, coords, compat, positions):
    """
    Concatenate a sequence of datasets along a new or existing dimension
    """
    from .dataset import Dataset

    if compat not in ['equals', 'identical']:
        raise ValueError("compat=%r invalid: must be 'equals' "
                         "or 'identical'" % compat)

    dim, coord = _calc_concat_dim_coord(dim)
    # Make sure we're working on a copy (we'll be loading variables)
    datasets = [ds.copy() for ds in datasets]
    datasets = align(*datasets, join='outer', copy=False, exclude=[dim])

    concat_over, equals = _calc_concat_over(datasets, dim, data_vars, coords)

    def insert_result_variable(k, v):
        assert isinstance(v, Variable)
        if k in datasets[0].coords:
            result_coord_names.add(k)
        result_vars[k] = v

    # create the new dataset and add constant variables
    result_vars = OrderedDict()
    result_coord_names = set(datasets[0].coords)
    result_attrs = datasets[0].attrs
    result_encoding = datasets[0].encoding

    for k, v in datasets[0].variables.items():
        if k not in concat_over:
            insert_result_variable(k, v)

    # check that global attributes and non-concatenated variables are fixed
    # across all datasets
    for ds in datasets[1:]:
        if (compat == 'identical' and
                not utils.dict_equiv(ds.attrs, result_attrs)):
            raise ValueError('dataset global attributes not equal')
        for k, v in iteritems(ds.variables):
            if k not in result_vars and k not in concat_over:
                raise ValueError('encountered unexpected variable %r' % k)
            elif (k in result_coord_names) != (k in ds.coords):
                raise ValueError('%r is a coordinate in some datasets but not '
                                 'others' % k)
            elif k in result_vars and k != dim:
                # Don't use Variable.identical as it internally invokes
                # Variable.equals, and we may already know the answer
                if compat == 'identical' and not utils.dict_equiv(
                        v.attrs, result_vars[k].attrs):
                    raise ValueError(
                        'variable %s not identical across datasets' % k)

                # Proceed with equals()
                try:
                    # May be populated when using the "different" method
                    is_equal = equals[k]
                except KeyError:
                    result_vars[k].load()
                    is_equal = v.equals(result_vars[k])
                if not is_equal:
                    raise ValueError(
                        'variable %s not equal across datasets' % k)

    # we've already verified everything is consistent; now, calculate
    # shared dimension sizes so we can expand the necessary variables
    dim_lengths = [ds.dims.get(dim, 1) for ds in datasets]
    non_concat_dims = {}
    for ds in datasets:
        non_concat_dims.update(ds.dims)
    non_concat_dims.pop(dim, None)

    def ensure_common_dims(vars):
        # ensure each variable with the given name shares the same
        # dimensions and the same shape for all of them except along the
        # concat dimension
        common_dims = tuple(pd.unique([d for v in vars for d in v.dims]))
        if dim not in common_dims:
            common_dims = (dim,) + common_dims
        for var, dim_len in zip(vars, dim_lengths):
            if var.dims != common_dims:
                common_shape = tuple(non_concat_dims.get(d, dim_len)
                                     for d in common_dims)
                var = var.set_dims(common_dims, common_shape)
            yield var

    # stack up each variable to fill-out the dataset (in order)
    for k in datasets[0].variables:
        if k in concat_over:
            vars = ensure_common_dims([ds.variables[k] for ds in datasets])
            combined = concat_vars(vars, dim, positions)
            insert_result_variable(k, combined)

    result = Dataset(result_vars, attrs=result_attrs)
    result = result.set_coords(result_coord_names)
    result.encoding = result_encoding

    if coord is not None:
        # add concat dimension last to ensure that its in the final Dataset
        result[coord.name] = coord

    return result


def _dataarray_concat(arrays, dim, data_vars, coords, compat,
                      positions):
    arrays = list(arrays)

    if data_vars != 'all':
        raise ValueError('data_vars is not a valid argument when '
                         'concatenating DataArray objects')

    datasets = []
    for n, arr in enumerate(arrays):
        if n == 0:
            name = arr.name
        elif name != arr.name:
            if compat == 'identical':
                raise ValueError('array names not identical')
            else:
                arr = arr.rename(name)
        datasets.append(arr._to_temp_dataset())

    ds = _dataset_concat(datasets, dim, data_vars, coords, compat,
                         positions)
    return arrays[0]._from_temp_dataset(ds, name)


def _auto_concat(datasets, dim=None, data_vars='all', coords='different'):
    if len(datasets) == 1 and dim is None:
        # There is nothing more to combine, so kick out early.
        return datasets[0]
    else:
        if dim is None:
            ds0 = datasets[0]
            ds1 = datasets[1]
            concat_dims = set(ds0.dims)
            if ds0.dims != ds1.dims:
                dim_tuples = set(ds0.dims.items()) - set(ds1.dims.items())
                concat_dims = set(i for i, _ in dim_tuples)
            if len(concat_dims) > 1:
                concat_dims = set(d for d in concat_dims
                                  if not ds0[d].equals(ds1[d]))
            if len(concat_dims) > 1:
                raise ValueError('too many different dimensions to '
                                 'concatenate: %s' % concat_dims)
            elif len(concat_dims) == 0:
                raise ValueError('cannot infer dimension to concatenate: '
                                 'supply the ``concat_dim`` argument '
                                 'explicitly')
            dim, = concat_dims
        return concat(datasets, dim=dim, data_vars=data_vars, coords=coords)


_CONCAT_DIM_DEFAULT = utils.ReprObject('<inferred>')


def _infer_concat_order_from_positions(datasets, concat_dims):

    combined_ids = OrderedDict(_infer_tile_ids_from_nested_list(datasets, ()))

    tile_id, ds = list(combined_ids.items())[0]
    n_dims = len(tile_id)

    if concat_dims is _CONCAT_DIM_DEFAULT:
        concat_dims = [_CONCAT_DIM_DEFAULT] * n_dims
    else:
        if len(concat_dims) != n_dims:
            raise ValueError("concat_dims has length " + str(len(concat_dims))
                             + " but the datasets passed are nested in a " +
                             str(n_dims) + "-dimensional structure")

    return combined_ids, concat_dims


def _infer_tile_ids_from_nested_list(entry, current_pos):
    """
    Given a list of lists (of lists...) of objects, returns a iterator
    which returns a tuple containing the index of each object in the nested
    list structure as the key, and the object. This can then be called by the
    dict constructor to create a dictionary of the objects organised by their
    position in the original nested list.

    Recursively traverses the given structure, while keeping track of the
    current position. Should work for any type of object which isn't a list.

    Parameters
    ----------
    entry : list[list[obj, obj, ...]]
        List of lists of arbitrary depth, containing objects in the order
        they are to be concatenated.

    Returns
    -------
    combined_tile_ids : dict[tuple(int, ...), obj]
    """

    if isinstance(entry, list):
        for i, item in enumerate(entry):
            for result in _infer_tile_ids_from_nested_list(item,
                                                           current_pos + (i,)):
                yield result
    else:
        yield current_pos, entry


def _infer_concat_order_from_coords(datasets):

    concat_dims = []
    tile_ids = [() for ds in datasets]

    # All datasets have same variables because they've been grouped as such
    ds0 = datasets[0]
    for dim in ds0.dims:

        # Check if dim is a coordinate dimension
        if dim in ds0:

            # Need to read coordinate values to do ordering
            coord_vals = [ds[dim].values for ds in datasets]

            # If dimension coordinate values are same on every dataset then
            # should be leaving this dimension alone (it's just a "bystander")
            if not _all_arrays_equal(coord_vals):

                # Infer order datasets should be arranged in along this dim
                concat_dims.append(dim)

                # TODO generalise this to deduce whether coord should be monotonically increasing or decreasing
                if not all(pd.Index(coord).is_monotonic_increasing
                           for coord in coord_vals):
                    raise ValueError(f"Coordinate variable {dim} is not "
                                     "monotonically increasing on all "
                                     "datasets")

                # Sort datasets along dim
                # Assume that any two datasets whose coord along dim starts with
                # the same value have the exact same coord values throughout.
                first_coord_vals = [coord[0] for coord in coord_vals]
                new_positions = _infer_order_1d(first_coord_vals,
                                                method='dense')

                # TODO check that resulting global coordinate is monotonic

                # Append positions along extra dimension to structure which
                # encodes the multi-dimensional concatentation order
                tile_ids = [tile_id + (position,) for tile_id, position
                            in zip(tile_ids, new_positions)]

    # TODO check that this is still the correct logic for case of merging but no concatenation
    if len(datasets) > 1 and not concat_dims:
        raise ValueError("Could not find any dimension coordinates to use to "
                         "order the datasets for concatenation")

    combined_ids = OrderedDict(zip(tile_ids, datasets))

    return combined_ids, concat_dims


def _all_arrays_equal(iterator):
    try:
       iterator = iter(iterator)
       first = next(iterator)
       return all(np.array_equal(first, rest) for rest in iterator)
    except StopIteration:
       return True


def _infer_order_1d(arr, method='dense'):
    # TODO Special cases for string coords - natural sorting instead?
    # TODO sort datetime coords too
    arr = np.array(arr)

    # We want rank but with identical elements given identical position indices
    # - they should be concatenated along another dimension, not along this one
    ranks = pd.Series(arr).rank(method=method).values

    return ranks.astype('int') - 1


def _check_shape_tile_ids(combined_tile_ids):
    tile_ids = combined_tile_ids.keys()

    # Check all tuples are the same length
    # i.e. check that all lists are nested to the same depth
    nesting_depths = [len(tile_id) for tile_id in tile_ids]
    if not set(nesting_depths) == {nesting_depths[0]}:
        raise ValueError("The supplied objects do not form a hypercube because"
                         " sub-lists do not have consistent depths")

    # Check all lists along one dimension are same length
    for dim in range(nesting_depths[0]):
        indices_along_dim = [tile_id[dim] for tile_id in tile_ids]
        occurrences = Counter(indices_along_dim)
        if len(set(occurrences.values())) != 1:
            raise ValueError("The supplied objects do not form a hypercube "
                             "because sub-lists do not have consistent "
                             "lengths along dimension" + str(dim))


def _combine_nd(combined_ids, concat_dims, data_vars='all',
                coords='different', compat='no_conflicts'):
    """
    Combines an N-dimensional structure of datasets into one by applying a
    series of either concat and merge operations along each dimension.

    No checks are performed on the consistency of the datasets, concat_dims or
    tile_IDs, because it is assumed that this has already been done.

    Parameters
    ----------
    combined_ids : Dict[Tuple[int, ...]], xarray.Dataset]
        Structure containing all datasets to be concatenated with "tile_IDs" as
        keys, which specify position within the desired final combined result.
    concat_dims : sequence of str
        The dimensions along which the datasets should be concatenated. Must be
        in order, and the length must match the length of the tuples used as
        keys in combined_ids. If the string is a dimension name then concat
        along that dimension, if it is None then merge.

    Returns
    -------
    combined_ds : xarray.Dataset
    """

    # Each iteration of this loop reduces the length of the tile_ids tuples
    # by one. It always combines along the first dimension, removing the first
    # element of the tuple
    for concat_dim in concat_dims:
        combined_ids = _combine_all_along_first_dim(combined_ids,
                                                    dim=concat_dim,
                                                    data_vars=data_vars,
                                                    coords=coords,
                                                    compat=compat)
    combined_ds = list(combined_ids.values())[0]
    return combined_ds


def _combine_all_along_first_dim(combined_ids, dim, data_vars, coords, compat):

    # Group into lines of datasets which must be combined along dim
    # need to sort by _new_tile_id first for groupby to work
    # TODO remove all these sorted OrderedDicts once python >= 3.6 only
    combined_ids = OrderedDict(sorted(combined_ids.items(), key=_new_tile_id))
    grouped = itertools.groupby(combined_ids.items(), key=_new_tile_id)

    # Combine all of these datasets along dim
    new_combined_ids = {}
    for new_id, group in grouped:
        combined_ids = OrderedDict(sorted(group))
        datasets = combined_ids.values()
        new_combined_ids[new_id] = _combine_1d(datasets, dim, compat,
                                               data_vars, coords)
    return new_combined_ids


def _combine_1d(datasets, concat_dim=_CONCAT_DIM_DEFAULT,
                compat='no_conflicts', data_vars='all', coords='different'):
    """
    Applies either concat or merge to 1D list of datasets depending on value
    of concat_dim
    """

    # TODO this logic is taken from old 1D auto_combine - check if it's right
    # Should it just use concat directly instead?
    if concat_dim is not None:
        dim = None if concat_dim is _CONCAT_DIM_DEFAULT else concat_dim
        combined = _auto_concat(datasets, dim=dim, data_vars=data_vars,
                                coords=coords)
    else:
        combined = merge(datasets, compat=compat)

    return combined


def _new_tile_id(single_id_ds_pair):
    tile_id, ds = single_id_ds_pair
    return tile_id[1:]


def _manual_combine(datasets, concat_dims, compat, data_vars, coords, ids):

    # Arrange datasets for concatenation
    # Use information from the shape of the user input
    if not ids:
        # Determine tile_IDs by structure of input in N-D
        # (i.e. ordering in list-of-lists)
        combined_ids, concat_dims = _infer_concat_order_from_positions(
            datasets, concat_dims)
    else:
        # Already sorted so just use the ids already passed
        combined_ids = OrderedDict(zip(ids, datasets))

    # Check that the inferred shape is combinable
    _check_shape_tile_ids(combined_ids)

    # Apply series of concatenate or merge operations along each dimension
    combined = _combine_nd(combined_ids, concat_dims, compat=compat,
                           data_vars=data_vars, coords=coords)
    return combined


def manual_combine(datasets, concat_dim=_CONCAT_DIM_DEFAULT,
                   compat='no_conflicts', data_vars='all', coords='different'):
    """
    Explicitly combine an N-dimensional grid of datasets into one by using a
    succession of concat and merge operations along each dimension of the grid.

    Does not sort data under any circumstances, so the datasets must be passed
    in the order you wish them to be concatenated. It does align coordinates,
    but different variables on datasets can cause it to fail under some
    scenarios. In complex cases, you may need to clean up your data and use
    concat/merge explicitly.

    To concatenate along multiple dimensions the datasets must be passed as a
    nested list-of-lists, with a depth equal to the length of ``concat_dims``.
    ``manual_combine`` will concatenate along the top-level list first.

    Useful for combining datasets from a set of nested directories, or for
    collecting the output of a simulation parallelized along multiple
    dimensions.

    Parameters
    ----------
    datasets : list or nested list of xarray.Dataset objects.
        Dataset objects to combine.
        If concatenation or merging along more than one dimension is desired,
        then datasets must be supplied in a nested list-of-lists.
    concat_dim : str, or list of str, DataArray, Index or None, optional
        Dimensions along which to concatenate variables, as used by
        :py:func:`xarray.concat`.
        By default, xarray attempts to infer this argument by examining
        component files. Set ``concat_dim=[..., None, ...]`` explicitly to
        disable concatenation and merge instead along a particular dimension.
        Must be the same length as the depth of the list passed to
        ``datasets``.
    compat : {'identical', 'equals', 'broadcast_equals',
              'no_conflicts'}, optional
        String indicating how to compare variables of the same name for
        potential merge conflicts:

        - 'broadcast_equals': all values must be equal when variables are
          broadcast against each other to ensure common dimensions.
        - 'equals': all values and dimensions must be the same.
        - 'identical': all values, dimensions and attributes must be the
          same.
        - 'no_conflicts': only values which are not null in both datasets
          must be equal. The returned dataset then contains the combination
          of all non-null values.
    data_vars : {'minimal', 'different', 'all' or list of str}, optional
        Details are in the documentation of concat
    coords : {'minimal', 'different', 'all' or list of str}, optional
        Details are in the documentation of concat

    Returns
    -------
    combined : xarray.Dataset

    Examples
    --------

    Collecting output from a parallel simulation:

    Collecting data from a simulation which decomposes its domain into 4 parts,
    2 each along both the x and y axes, requires organising the datasets into a
    nested list, e.g.

    >>> x1y1
    <xarray.Dataset>
    Dimensions:         (x: 2, y: 2)
    Coordinates:
      lon               (x, y) float64 -99.83 -99.32 -99.79 -99.23
      lat               (x, y) float64 42.25 42.21 42.63 42.59
    Dimensions without coordinates: x, y
    Data variables:
      temperature       (x, y) float64 11.04 23.57 20.77 ...
      precipitation     (x, y) float64 5.904 2.453 3.404 ...

    >>> ds_grid = [[x1y1, x1y2], [x2y1, x2y2]]
    >>> combined = xr.auto_combine(ds_grid, concat_dims=['x', 'y'])
    <xarray.Dataset>
    Dimensions:         (x: 4, y: 4)
    Coordinates:
      lon               (x, y) float64 -99.83 -99.32 -99.79 -99.23
      lat               (x, y) float64 42.25 42.21 42.63 42.59
    Dimensions without coordinates: x, y
    Data variables:
      temperature       (x, y) float64 11.04 23.57 20.77 ...
      precipitation     (x, y) float64 5.904 2.453 3.404 ...

    See also
    --------
    concat
    merge
    auto_combine
    """

    if concat_dim is not _CONCAT_DIM_DEFAULT:
        if isinstance(concat_dim, str) or concat_dim is None:
            concat_dim = [concat_dim]

    # The IDs argument tells _manual_combine that datasets aren't yet sorted
    return _manual_combine(datasets, concat_dims=concat_dim, compat=compat,
                           data_vars=data_vars, coords=coords, ids=False)


def auto_combine(datasets, compat='no_conflicts', data_vars='all',
                 coords='different'):
    """
    Attempt to auto-magically combine the given datasets into one by using
    dimension coordinates.

    This method attempts to combine a group of datasets along any number of
    dimensions into a single entity by inspecting coords and metadata and using
    a combination of concat and merge.

    Will attempt to order the datasets such that the values in their dimension
    coordinates are monotonically increasing along all dimensions. If it cannot
    determine the order in which to concatenate the datasets, it will raise an
    error.
    Non-coordinate dimensions will be ignored, as will any coordinate
    dimensions which do not vary between each dataset.

    Aligns coordinates, but different variables on datasets can cause it
    to fail under some scenarios. In complex cases, you may need to clean up
    your data and use concat/merge explicitly (also see `manual_combine`).

    Works well if, for example, you have N years of data and M data variables,
    and each combination of a distinct time period and set of data variables is
    saved as its own dataset. Also useful for if you have a simulation which is
    parallelized in multiple dimensions, but has global coordinates saved in
    each file specifying it's position within the domain.

    Parameters
    ----------
    datasets : sequence of xarray.Dataset
        Dataset objects to combine.
    compat : {'identical', 'equals', 'broadcast_equals',
              'no_conflicts'}, optional
        String indicating how to compare variables of the same name for
        potential conflicts:

        - 'broadcast_equals': all values must be equal when variables are
          broadcast against each other to ensure common dimensions.
        - 'equals': all values and dimensions must be the same.
        - 'identical': all values, dimensions and attributes must be the
          same.
        - 'no_conflicts': only values which are not null in both datasets
          must be equal. The returned dataset then contains the combination
          of all non-null values.
    data_vars : {'minimal', 'different', 'all' or list of str}, optional
        Details are in the documentation of concat
    coords : {'minimal', 'different', 'all' or list of str}, optional
        Details are in the documentation of concat

    Returns
    -------
    combined : xarray.Dataset

    See also
    --------
    concat
    merge
    manual_combine
    """

    # Group by data vars
    grouped = itertools.groupby(datasets, key=lambda ds: tuple(sorted(ds)))

    # Perform the multidimensional combine on each group of data variables
    # before merging back together
    concatenated_grouped_by_data_vars = []
    for vars, datasets in grouped:
        combined_ids, concat_dims = _infer_concat_order_from_coords(
            list(datasets))

        # TODO checking the shape of the combined ids appropriate here?
        _check_shape_tile_ids(combined_ids)

        # Concatenate along all of concat_dims one by one to create single ds
        concatenated = _combine_nd(combined_ids, concat_dims=concat_dims,
                                   data_vars=data_vars, coords=coords)

        # TODO check the overall coordinates are monotonically increasing?
        concatenated_grouped_by_data_vars.append(concatenated)

    return merge(concatenated_grouped_by_data_vars, compat=compat)
