try:
    import dask
    import dask.array
    from dask.highlevelgraph import HighLevelGraph

except ImportError:
    pass

import itertools
import numpy as np
import operator

from .dataarray import DataArray
from .dataset import Dataset


def _to_array(obj):
    if not isinstance(obj, Dataset):
        raise ValueError("Trying to convert DataArray to DataArray!")

    if len(obj.data_vars) > 1:
        raise ValueError(
            "Trying to convert Dataset with more than one variable to DataArray"
        )

    name = list(obj.data_vars)[0]
    # this should be easier
    da = obj.to_array().squeeze().drop("variable")
    da.name = name
    return da


def make_meta(obj):

    from dask.array.utils import meta_from_array

    if isinstance(obj, DataArray):
        meta = DataArray(obj.data._meta, dims=obj.dims)

    if isinstance(obj, Dataset):
        meta = Dataset()
        for name, variable in obj.variables.items():
            if dask.is_dask_collection(variable):
                meta_obj = obj[name].data._meta
            else:
                meta_obj = meta_from_array(obj[name].data)
            meta[name] = DataArray(meta_obj, dims=obj[name].dims)
    else:
        meta = obj

    return meta


def infer_template(func, obj, *args, **kwargs):
    """ Infer return object by running the function on meta objects. """
    meta_args = []
    for arg in (obj,) + args:
        meta_args.append(make_meta(arg))

    try:
        template = func(*meta_args, **kwargs)
    except ValueError:
        raise ValueError("Cannot infer object returned by user-provided function.")

    return template


def _make_dict(x):
    # Dataset.to_dict() is too complicated
    # maps variable name to numpy array
    if isinstance(x, DataArray):
        x = x._to_temp_dataset()

    to_return = dict()
    for var in x.variables:
        # if var not in x:
        #    raise ValueError("Variable %r not found in returned object." % var)
        to_return[var] = x[var].values

    return to_return


def map_blocks(func, obj, *args, **kwargs):
    """
    Apply a function to each chunk of a DataArray or Dataset. This function is experimental
    and its signature may change.

    Parameters
    ----------
    func: callable
        User-provided function that should accept DataArrays corresponding to one chunk.
        The function will be run on a small piece of data that looks like 'obj' to determine
        properties of the returned object such as dtype, variable names,
        new dimensions and new indexes (if any).

        This function cannot
        - change size of existing dimensions.
        - add new chunked dimensions.

    obj: DataArray, Dataset
        Chunks of this object will be provided to 'func'. The function must not change
        shape of the provided DataArray.
    args:
        Passed on to func.
    kwargs:
        Passed on to func.


    Returns
    -------
    DataArray or Dataset

    See Also
    --------
    dask.array.map_blocks
    """

    def _wrapper(func, obj, to_array, args, kwargs):
        if to_array:
            obj = _to_array(obj)

        result = func(obj, *args, **kwargs)

        for name, index in result.indexes.items():
            if name in obj.indexes:
                if len(index) != len(obj.indexes[name]):
                    raise ValueError(
                        "Length of the %r dimension has changed. This is not allowed."
                        % name
                    )

        to_return = _make_dict(result)

        return to_return

    if not dask.is_dask_collection(obj):
        raise ValueError(
            "map_blocks can only be used with dask-backed DataArrays. Use .chunk() to convert to a Dask array."
        )

    if isinstance(obj, DataArray):
        dataset = obj._to_temp_dataset()
        input_is_array = True
    else:
        dataset = obj
        input_is_array = False

    template = infer_template(func, obj, *args, **kwargs)
    if isinstance(template, DataArray):
        result_is_array = True
        template = template._to_temp_dataset()
    else:
        result_is_array = False

    # If two different variables have different chunking along the same dim
    # .chunks will raise an error.
    input_chunks = dataset.chunks

    indexes = dict(dataset.indexes)
    for dim in template.indexes:
        if dim not in indexes:
            indexes[dim] = template.indexes[dim]

    graph = {}
    gname = "%s-%s" % (dask.utils.funcname(func), dask.base.tokenize(dataset))

    # map dims to list of chunk indexes
    ichunk = {dim: range(len(input_chunks[dim])) for dim in input_chunks}
    # mapping from chunk index to slice bounds
    chunk_index_bounds = {
        dim: np.cumsum((0,) + input_chunks[dim]) for dim in input_chunks
    }

    # iterate over all possible chunk combinations
    for v in itertools.product(*ichunk.values()):
        chunk_index_dict = dict(zip(dataset.dims, v))

        # this will become [[name1, variable1],
        #                   [name2, variable2],
        #                   ...]
        # which is passed to dict and then to Dataset
        data_vars = []
        coords = []

        for name, variable in dataset.variables.items():
            # make a task that creates tuple of (dims, chunk)
            if dask.is_dask_collection(variable.data):
                var_dask_keys = variable.__dask_keys__()

                # recursively index into dask_keys nested list to get chunk
                chunk = var_dask_keys
                for dim in variable.dims:
                    chunk = chunk[chunk_index_dict[dim]]

                task_name = ("tuple-" + dask.base.tokenize(chunk),) + v
                graph[task_name] = (tuple, [variable.dims, chunk])
            else:
                # numpy array with possibly chunked dimensions
                # index into variable appropriately
                subsetter = dict()
                for dim in variable.dims:
                    if dim in chunk_index_dict:
                        which_chunk = chunk_index_dict[dim]
                        subsetter[dim] = slice(
                            chunk_index_bounds[dim][which_chunk],
                            chunk_index_bounds[dim][which_chunk + 1],
                        )

                subset = variable.isel(subsetter)
                task_name = (name + dask.base.tokenize(subset),) + v
                graph[task_name] = (tuple, [subset.dims, subset])

            # this task creates dict mapping variable name to above tuple
            if name in dataset.data_vars:
                data_vars.append([name, task_name])
            if name in dataset.coords:
                coords.append([name, task_name])

        from_wrapper = (gname,) + v
        graph[from_wrapper] = (
            _wrapper,
            func,
            (Dataset, (dict, data_vars), (dict, coords), dataset.attrs),
            input_is_array,
            args,
            kwargs,
        )

        # mapping from variable name to dask graph key
        var_key_map = {}
        for name, variable in template.variables.items():
            var_dims = variable.dims
            # cannot tokenize "name" because the hash of <this-array> is not invariant!
            # This happens when the user function does not set a name on the returned DataArray
            gname_l = "%s-%s" % (gname, name)
            var_key_map[name] = gname_l

            key = (gname_l,)
            for dim in var_dims:
                if dim in chunk_index_dict:
                    key += (chunk_index_dict[dim],)
                else:
                    # unchunked dimensions in the input have one chunk in the result
                    key += (0,)

            graph[key] = (operator.getitem, from_wrapper, name)

    graph = HighLevelGraph.from_collections(name, graph, dependencies=[dataset])

    result = Dataset()
    for var, key in var_key_map.items():
        # indexes need to be known
        # otherwise compute is called when DataArray is created
        if var in indexes:
            result[var] = indexes[var]
            continue

        dims = template[var].dims
        var_chunks = []
        for dim in dims:
            if dim in input_chunks:
                var_chunks.append(input_chunks[dim])
            else:
                if dim in indexes:
                    var_chunks.append((len(indexes[dim]),))

        data = dask.array.Array(
            graph, name=key, chunks=var_chunks, dtype=template[var].dtype
        )
        result[var] = DataArray(data=data, dims=dims, name=var)

    if result_is_array:
        result = _to_array(result)

    return result
