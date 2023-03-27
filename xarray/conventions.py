from __future__ import annotations

import warnings
from collections import defaultdict
from collections.abc import Hashable, Iterable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, Union

import numpy as np
import pandas as pd

from xarray.coding import strings, times, variables
from xarray.coding.variables import SerializationWarning, pop_to
from xarray.core import duck_array_ops, indexing
from xarray.core.common import (
    _contains_datetime_like_objects,
    contains_cftime_datetimes,
)
from xarray.core.pycompat import is_duck_dask_array
from xarray.core.variable import IndexVariable, Variable

CF_RELATED_DATA = (
    "bounds",
    "grid_mapping",
    "climatology",
    "geometry",
    "node_coordinates",
    "node_count",
    "part_node_count",
    "interior_ring",
    "cell_measures",
    "formula_terms",
)
CF_RELATED_DATA_NEEDS_PARSING = (
    "cell_measures",
    "formula_terms",
)


if TYPE_CHECKING:
    from xarray.backends.common import AbstractDataStore
    from xarray.core.dataset import Dataset

    T_VarTuple = tuple[tuple[Hashable, ...], Any, dict, dict]
    T_Name = Union[Hashable, None]
    T_Variables = Mapping[Any, Variable]
    T_Attrs = MutableMapping[Any, Any]
    T_DropVariables = Union[str, Iterable[Hashable], None]
    T_DatasetOrAbstractstore = Union[Dataset, AbstractDataStore]


class NativeEndiannessArray(indexing.ExplicitlyIndexedNDArrayMixin):
    """Decode arrays on the fly from non-native to native endianness

    This is useful for decoding arrays from netCDF3 files (which are all
    big endian) into native endianness, so they can be used with Cython
    functions, such as those found in bottleneck and pandas.

    >>> x = np.arange(5, dtype=">i2")

    >>> x.dtype
    dtype('>i2')

    >>> NativeEndiannessArray(x).dtype
    dtype('int16')

    >>> indexer = indexing.BasicIndexer((slice(None),))
    >>> NativeEndiannessArray(x)[indexer].dtype
    dtype('int16')
    """

    __slots__ = ("array",)

    def __init__(self, array):
        self.array = indexing.as_indexable(array)

    @property
    def dtype(self):
        return np.dtype(self.array.dtype.kind + str(self.array.dtype.itemsize))

    def __getitem__(self, key):
        return np.asarray(self.array[key], dtype=self.dtype)


class BoolTypeArray(indexing.ExplicitlyIndexedNDArrayMixin):
    """Decode arrays on the fly from integer to boolean datatype

    This is useful for decoding boolean arrays from integer typed netCDF
    variables.

    >>> x = np.array([1, 0, 1, 1, 0], dtype="i1")

    >>> x.dtype
    dtype('int8')

    >>> BoolTypeArray(x).dtype
    dtype('bool')

    >>> indexer = indexing.BasicIndexer((slice(None),))
    >>> BoolTypeArray(x)[indexer].dtype
    dtype('bool')
    """

    __slots__ = ("array",)

    def __init__(self, array):
        self.array = indexing.as_indexable(array)

    @property
    def dtype(self):
        return np.dtype("bool")

    def __getitem__(self, key):
        return np.asarray(self.array[key], dtype=self.dtype)


def _var_as_tuple(var: Variable) -> T_VarTuple:
    return var.dims, var.data, var.attrs.copy(), var.encoding.copy()


def maybe_encode_nonstring_dtype(var: Variable, name: T_Name = None) -> Variable:
    if "dtype" in var.encoding and var.encoding["dtype"] not in ("S1", str):
        dims, data, attrs, encoding = _var_as_tuple(var)
        dtype = np.dtype(encoding.pop("dtype"))
        if dtype != var.dtype:
            if np.issubdtype(dtype, np.integer):
                if (
                    np.issubdtype(var.dtype, np.floating)
                    and "_FillValue" not in var.attrs
                    and "missing_value" not in var.attrs
                ):
                    warnings.warn(
                        f"saving variable {name} with floating "
                        "point data as an integer dtype without "
                        "any _FillValue to use for NaNs",
                        SerializationWarning,
                        stacklevel=10,
                    )
                data = np.around(data)
            data = data.astype(dtype=dtype)
        var = Variable(dims, data, attrs, encoding, fastpath=True)
    return var


def maybe_default_fill_value(var: Variable) -> Variable:
    # make NaN the fill value for float types:
    if (
        "_FillValue" not in var.attrs
        and "_FillValue" not in var.encoding
        and np.issubdtype(var.dtype, np.floating)
    ):
        var.attrs["_FillValue"] = var.dtype.type(np.nan)
    return var


def maybe_encode_bools(var: Variable) -> Variable:
    if (
        (var.dtype == bool)
        and ("dtype" not in var.encoding)
        and ("dtype" not in var.attrs)
    ):
        dims, data, attrs, encoding = _var_as_tuple(var)
        attrs["dtype"] = "bool"
        data = duck_array_ops.astype(data, dtype="i1", copy=True)
        var = Variable(dims, data, attrs, encoding, fastpath=True)
    return var


def _infer_dtype(array, name: T_Name = None) -> np.dtype:
    """Given an object array with no missing values, infer its dtype from its
    first element
    """
    if array.dtype.kind != "O":
        raise TypeError("infer_type must be called on a dtype=object array")

    if array.size == 0:
        return np.dtype(float)

    element = array[(0,) * array.ndim]
    # We use the base types to avoid subclasses of bytes and str (which might
    # not play nice with e.g. hdf5 datatypes), such as those from numpy
    if isinstance(element, bytes):
        return strings.create_vlen_dtype(bytes)
    elif isinstance(element, str):
        return strings.create_vlen_dtype(str)

    dtype = np.array(element).dtype
    if dtype.kind != "O":
        return dtype

    raise ValueError(
        "unable to infer dtype on variable {!r}; xarray "
        "cannot serialize arbitrary Python objects".format(name)
    )


def ensure_not_multiindex(var: Variable, name: T_Name = None) -> None:
    if isinstance(var, IndexVariable) and isinstance(var.to_index(), pd.MultiIndex):
        raise NotImplementedError(
            "variable {!r} is a MultiIndex, which cannot yet be "
            "serialized to netCDF files. Instead, either use reset_index() "
            "to convert MultiIndex levels into coordinate variables instead "
            "or use https://cf-xarray.readthedocs.io/en/latest/coding.html.".format(
                name
            )
        )


def _copy_with_dtype(data, dtype: np.typing.DTypeLike):
    """Create a copy of an array with the given dtype.

    We use this instead of np.array() to ensure that custom object dtypes end
    up on the resulting array.
    """
    result = np.empty(data.shape, dtype)
    result[...] = data
    return result


def ensure_dtype_not_object(var: Variable, name: T_Name = None) -> Variable:
    # TODO: move this from conventions to backends? (it's not CF related)
    if var.dtype.kind == "O":
        dims, data, attrs, encoding = _var_as_tuple(var)

        if is_duck_dask_array(data):
            warnings.warn(
                "variable {} has data in the form of a dask array with "
                "dtype=object, which means it is being loaded into memory "
                "to determine a data type that can be safely stored on disk. "
                "To avoid this, coerce this variable to a fixed-size dtype "
                "with astype() before saving it.".format(name),
                SerializationWarning,
            )
            data = data.compute()

        missing = pd.isnull(data)
        if missing.any():
            # nb. this will fail for dask.array data
            non_missing_values = data[~missing]
            inferred_dtype = _infer_dtype(non_missing_values, name)

            # There is no safe bit-pattern for NA in typical binary string
            # formats, we so can't set a fill_value. Unfortunately, this means
            # we can't distinguish between missing values and empty strings.
            fill_value: bytes | str
            if strings.is_bytes_dtype(inferred_dtype):
                fill_value = b""
            elif strings.is_unicode_dtype(inferred_dtype):
                fill_value = ""
            else:
                # insist on using float for numeric values
                if not np.issubdtype(inferred_dtype, np.floating):
                    inferred_dtype = np.dtype(float)
                fill_value = inferred_dtype.type(np.nan)

            data = _copy_with_dtype(data, dtype=inferred_dtype)
            data[missing] = fill_value
        else:
            data = _copy_with_dtype(data, dtype=_infer_dtype(data, name))

        assert data.dtype.kind != "O" or data.dtype.metadata
        var = Variable(dims, data, attrs, encoding, fastpath=True)
    return var


def encode_cf_variable(
    var: Variable, needs_copy: bool = True, name: T_Name = None
) -> Variable:
    """
    Converts an Variable into an Variable which follows some
    of the CF conventions:

        - Nans are masked using _FillValue (or the deprecated missing_value)
        - Rescaling via: scale_factor and add_offset
        - datetimes are converted to the CF 'units since time' format
        - dtype encodings are enforced.

    Parameters
    ----------
    var : Variable
        A variable holding un-encoded data.

    Returns
    -------
    out : Variable
        A variable which has been encoded as described above.
    """
    ensure_not_multiindex(var, name=name)

    for coder in [
        times.CFDatetimeCoder(),
        times.CFTimedeltaCoder(),
        variables.CFScaleOffsetCoder(),
        variables.CFMaskCoder(),
        variables.UnsignedIntegerCoder(),
    ]:
        var = coder.encode(var, name=name)

    # TODO(shoyer): convert all of these to use coders, too:
    var = maybe_encode_nonstring_dtype(var, name=name)
    var = maybe_default_fill_value(var)
    var = maybe_encode_bools(var)
    var = ensure_dtype_not_object(var, name=name)

    for attr_name in CF_RELATED_DATA:
        pop_to(var.encoding, var.attrs, attr_name)
    return var


def decode_cf_variable(
    name: Hashable,
    var: Variable,
    concat_characters: bool = True,
    mask_and_scale: bool = True,
    decode_times: bool = True,
    decode_endianness: bool = True,
    stack_char_dim: bool = True,
    use_cftime: bool | None = None,
    decode_timedelta: bool | None = None,
) -> Variable:
    """
    Decodes a variable which may hold CF encoded information.

    This includes variables that have been masked and scaled, which
    hold CF style time variables (this is almost always the case if
    the dataset has been serialized) and which have strings encoded
    as character arrays.

    Parameters
    ----------
    name : str
        Name of the variable. Used for better error messages.
    var : Variable
        A variable holding potentially CF encoded information.
    concat_characters : bool
        Should character arrays be concatenated to strings, for
        example: ["h", "e", "l", "l", "o"] -> "hello"
    mask_and_scale : bool
        Lazily scale (using scale_factor and add_offset) and mask
        (using _FillValue). If the _Unsigned attribute is present
        treat integer arrays as unsigned.
    decode_times : bool
        Decode cf times ("hours since 2000-01-01") to np.datetime64.
    decode_endianness : bool
        Decode arrays from non-native to native endianness.
    stack_char_dim : bool
        Whether to stack characters into bytes along the last dimension of this
        array. Passed as an argument because we need to look at the full
        dataset to figure out if this is appropriate.
    use_cftime : bool, optional
        Only relevant if encoded dates come from a standard calendar
        (e.g. "gregorian", "proleptic_gregorian", "standard", or not
        specified).  If None (default), attempt to decode times to
        ``np.datetime64[ns]`` objects; if this is not possible, decode times to
        ``cftime.datetime`` objects. If True, always decode times to
        ``cftime.datetime`` objects, regardless of whether or not they can be
        represented using ``np.datetime64[ns]`` objects.  If False, always
        decode times to ``np.datetime64[ns]`` objects; if this is not possible
        raise an error.

    Returns
    -------
    out : Variable
        A variable holding the decoded equivalent of var.
    """
    # Ensure datetime-like Variables are passed through unmodified (GH 6453)
    if _contains_datetime_like_objects(var):
        return var

    original_dtype = var.dtype

    if decode_timedelta is None:
        decode_timedelta = decode_times

    if concat_characters:
        if stack_char_dim:
            var = strings.CharacterArrayCoder().decode(var, name=name)
        var = strings.EncodedStringCoder().decode(var)

    if mask_and_scale:
        for coder in [
            variables.UnsignedIntegerCoder(),
            variables.CFMaskCoder(),
            variables.CFScaleOffsetCoder(),
        ]:
            var = coder.decode(var, name=name)

    if decode_timedelta:
        var = times.CFTimedeltaCoder().decode(var, name=name)
    if decode_times:
        var = times.CFDatetimeCoder(use_cftime=use_cftime).decode(var, name=name)

    dimensions, data, attributes, encoding = variables.unpack_for_decoding(var)
    # TODO(shoyer): convert everything below to use coders

    if decode_endianness and not data.dtype.isnative:
        # do this last, so it's only done if we didn't already unmask/scale
        data = NativeEndiannessArray(data)
        original_dtype = data.dtype

    encoding.setdefault("dtype", original_dtype)

    if "dtype" in attributes and attributes["dtype"] == "bool":
        del attributes["dtype"]
        data = BoolTypeArray(data)

    if not is_duck_dask_array(data):
        data = indexing.LazilyIndexedArray(data)

    return Variable(dimensions, data, attributes, encoding=encoding, fastpath=True)


def _update_bounds_attributes(variables: T_Variables) -> None:
    """Adds time attributes to time bounds variables.

    Variables handling time bounds ("Cell boundaries" in the CF
    conventions) do not necessarily carry the necessary attributes to be
    decoded. This copies the attributes from the time variable to the
    associated boundaries.

    See Also:

    http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/
         cf-conventions.html#cell-boundaries

    https://github.com/pydata/xarray/issues/2565
    """

    # For all time variables with bounds
    for v in variables.values():
        attrs = v.attrs
        units = attrs.get("units")
        has_date_units = isinstance(units, str) and "since" in units
        if has_date_units and "bounds" in attrs:
            if attrs["bounds"] in variables:
                bounds_attrs = variables[attrs["bounds"]].attrs
                bounds_attrs.setdefault("units", attrs["units"])
                if "calendar" in attrs:
                    bounds_attrs.setdefault("calendar", attrs["calendar"])


def _update_bounds_encoding(variables: T_Variables) -> None:
    """Adds time encoding to time bounds variables.

    Variables handling time bounds ("Cell boundaries" in the CF
    conventions) do not necessarily carry the necessary attributes to be
    decoded. This copies the encoding from the time variable to the
    associated bounds variable so that we write CF-compliant files.

    See Also:

    http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/
         cf-conventions.html#cell-boundaries

    https://github.com/pydata/xarray/issues/2565
    """

    # For all time variables with bounds
    for name, v in variables.items():
        attrs = v.attrs
        encoding = v.encoding
        has_date_units = "units" in encoding and "since" in encoding["units"]
        is_datetime_type = np.issubdtype(
            v.dtype, np.datetime64
        ) or contains_cftime_datetimes(v)

        if (
            is_datetime_type
            and not has_date_units
            and "bounds" in attrs
            and attrs["bounds"] in variables
        ):
            warnings.warn(
                "Variable '{0}' has datetime type and a "
                "bounds variable but {0}.encoding does not have "
                "units specified. The units encodings for '{0}' "
                "and '{1}' will be determined independently "
                "and may not be equal, counter to CF-conventions. "
                "If this is a concern, specify a units encoding for "
                "'{0}' before writing to a file.".format(name, attrs["bounds"]),
                UserWarning,
            )

        if has_date_units and "bounds" in attrs:
            if attrs["bounds"] in variables:
                bounds_encoding = variables[attrs["bounds"]].encoding
                bounds_encoding.setdefault("units", encoding["units"])
                if "calendar" in encoding:
                    bounds_encoding.setdefault("calendar", encoding["calendar"])


def decode_cf_variables(
    variables: T_Variables,
    attributes: T_Attrs,
    concat_characters: bool = True,
    mask_and_scale: bool = True,
    decode_times: bool = True,
    decode_coords: bool = True,
    drop_variables: T_DropVariables = None,
    use_cftime: bool | None = None,
    decode_timedelta: bool | None = None,
) -> tuple[T_Variables, T_Attrs, set[Hashable]]:
    """
    Decode several CF encoded variables.

    See: decode_cf_variable
    """
    dimensions_used_by = defaultdict(list)
    for v in variables.values():
        for d in v.dims:
            dimensions_used_by[d].append(v)

    def stackable(dim: Hashable) -> bool:
        # figure out if a dimension can be concatenated over
        if dim in variables:
            return False
        for v in dimensions_used_by[dim]:
            if v.dtype.kind != "S" or dim != v.dims[-1]:
                return False
        return True

    coord_names = set()

    if isinstance(drop_variables, str):
        drop_variables = [drop_variables]
    elif drop_variables is None:
        drop_variables = []
    drop_variables = set(drop_variables)

    # Time bounds coordinates might miss the decoding attributes
    if decode_times:
        _update_bounds_attributes(variables)

    new_vars = {}
    for k, v in variables.items():
        if k in drop_variables:
            continue
        stack_char_dim = (
            concat_characters
            and v.dtype == "S1"
            and v.ndim > 0
            and stackable(v.dims[-1])
        )
        try:
            new_vars[k] = decode_cf_variable(
                k,
                v,
                concat_characters=concat_characters,
                mask_and_scale=mask_and_scale,
                decode_times=decode_times,
                stack_char_dim=stack_char_dim,
                use_cftime=use_cftime,
                decode_timedelta=decode_timedelta,
            )
        except Exception as e:
            raise type(e)(f"Failed to decode variable {k!r}: {e}")
        if decode_coords in [True, "coordinates", "all"]:
            var_attrs = new_vars[k].attrs
            if "coordinates" in var_attrs:
                coord_str = var_attrs["coordinates"]
                var_coord_names = coord_str.split()
                if all(k in variables for k in var_coord_names):
                    new_vars[k].encoding["coordinates"] = coord_str
                    del var_attrs["coordinates"]
                    coord_names.update(var_coord_names)

        if decode_coords == "all":
            for attr_name in CF_RELATED_DATA:
                if attr_name in var_attrs:
                    attr_val = var_attrs[attr_name]
                    if attr_name not in CF_RELATED_DATA_NEEDS_PARSING:
                        var_names = attr_val.split()
                    else:
                        roles_and_names = [
                            role_or_name
                            for part in attr_val.split(":")
                            for role_or_name in part.split()
                        ]
                        if len(roles_and_names) % 2 == 1:
                            warnings.warn(
                                f"Attribute {attr_name:s} malformed", stacklevel=5
                            )
                        var_names = roles_and_names[1::2]
                    if all(var_name in variables for var_name in var_names):
                        new_vars[k].encoding[attr_name] = attr_val
                        coord_names.update(var_names)
                    else:
                        referenced_vars_not_in_variables = [
                            proj_name
                            for proj_name in var_names
                            if proj_name not in variables
                        ]
                        warnings.warn(
                            f"Variable(s) referenced in {attr_name:s} not in variables: {referenced_vars_not_in_variables!s}",
                            stacklevel=5,
                        )
                    del var_attrs[attr_name]

    if decode_coords and isinstance(attributes.get("coordinates", None), str):
        attributes = dict(attributes)
        crds = attributes.pop("coordinates")
        coord_names.update(crds.split())

    return new_vars, attributes, coord_names


def decode_cf(
    obj: T_DatasetOrAbstractstore,
    concat_characters: bool = True,
    mask_and_scale: bool = True,
    decode_times: bool = True,
    decode_coords: bool = True,
    drop_variables: T_DropVariables = None,
    use_cftime: bool | None = None,
    decode_timedelta: bool | None = None,
) -> Dataset:
    """Decode the given Dataset or Datastore according to CF conventions into
    a new Dataset.

    Parameters
    ----------
    obj : Dataset or DataStore
        Object to decode.
    concat_characters : bool, optional
        Should character arrays be concatenated to strings, for
        example: ["h", "e", "l", "l", "o"] -> "hello"
    mask_and_scale : bool, optional
        Lazily scale (using scale_factor and add_offset) and mask
        (using _FillValue).
    decode_times : bool, optional
        Decode cf times (e.g., integers since "hours since 2000-01-01") to
        np.datetime64.
    decode_coords : bool or {"coordinates", "all"}, optional
        Controls which variables are set as coordinate variables:

        - "coordinates" or True: Set variables referred to in the
          ``'coordinates'`` attribute of the datasets or individual variables
          as coordinate variables.
        - "all": Set variables referred to in  ``'grid_mapping'``, ``'bounds'`` and
          other attributes as coordinate variables.
    drop_variables : str or iterable, optional
        A variable or list of variables to exclude from being parsed from the
        dataset. This may be useful to drop variables with problems or
        inconsistent values.
    use_cftime : bool, optional
        Only relevant if encoded dates come from a standard calendar
        (e.g. "gregorian", "proleptic_gregorian", "standard", or not
        specified).  If None (default), attempt to decode times to
        ``np.datetime64[ns]`` objects; if this is not possible, decode times to
        ``cftime.datetime`` objects. If True, always decode times to
        ``cftime.datetime`` objects, regardless of whether or not they can be
        represented using ``np.datetime64[ns]`` objects.  If False, always
        decode times to ``np.datetime64[ns]`` objects; if this is not possible
        raise an error.
    decode_timedelta : bool, optional
        If True, decode variables and coordinates with time units in
        {"days", "hours", "minutes", "seconds", "milliseconds", "microseconds"}
        into timedelta objects. If False, leave them encoded as numbers.
        If None (default), assume the same value of decode_time.

    Returns
    -------
    decoded : Dataset
    """
    from xarray.backends.common import AbstractDataStore
    from xarray.core.dataset import Dataset

    vars: T_Variables
    attrs: T_Attrs
    if isinstance(obj, Dataset):
        vars = obj._variables
        attrs = obj.attrs
        extra_coords = set(obj.coords)
        close = obj._close
        encoding = obj.encoding
    elif isinstance(obj, AbstractDataStore):
        vars, attrs = obj.load()
        extra_coords = set()
        close = obj.close
        encoding = obj.get_encoding()
    else:
        raise TypeError("can only decode Dataset or DataStore objects")

    vars, attrs, coord_names = decode_cf_variables(
        vars,
        attrs,
        concat_characters,
        mask_and_scale,
        decode_times,
        decode_coords,
        drop_variables=drop_variables,
        use_cftime=use_cftime,
        decode_timedelta=decode_timedelta,
    )
    ds = Dataset(vars, attrs=attrs)
    ds = ds.set_coords(coord_names.union(extra_coords).intersection(vars))
    ds.set_close(close)
    ds.encoding = encoding

    return ds


def cf_decoder(
    variables: T_Variables,
    attributes: T_Attrs,
    concat_characters: bool = True,
    mask_and_scale: bool = True,
    decode_times: bool = True,
) -> tuple[T_Variables, T_Attrs]:
    """
    Decode a set of CF encoded variables and attributes.

    Parameters
    ----------
    variables : dict
        A dictionary mapping from variable name to xarray.Variable
    attributes : dict
        A dictionary mapping from attribute name to value
    concat_characters : bool
        Should character arrays be concatenated to strings, for
        example: ["h", "e", "l", "l", "o"] -> "hello"
    mask_and_scale : bool
        Lazily scale (using scale_factor and add_offset) and mask
        (using _FillValue).
    decode_times : bool
        Decode cf times ("hours since 2000-01-01") to np.datetime64.

    Returns
    -------
    decoded_variables : dict
        A dictionary mapping from variable name to xarray.Variable objects.
    decoded_attributes : dict
        A dictionary mapping from attribute name to values.

    See Also
    --------
    decode_cf_variable
    """
    variables, attributes, _ = decode_cf_variables(
        variables, attributes, concat_characters, mask_and_scale, decode_times
    )
    return variables, attributes


def _encode_coordinates(variables, attributes, non_dim_coord_names):
    # calculate global and variable specific coordinates
    non_dim_coord_names = set(non_dim_coord_names)

    for name in list(non_dim_coord_names):
        if isinstance(name, str) and " " in name:
            warnings.warn(
                "coordinate {!r} has a space in its name, which means it "
                "cannot be marked as a coordinate on disk and will be "
                "saved as a data variable instead".format(name),
                SerializationWarning,
                stacklevel=6,
            )
            non_dim_coord_names.discard(name)

    global_coordinates = non_dim_coord_names.copy()
    variable_coordinates = defaultdict(set)
    not_technically_coordinates = set()
    for coord_name in non_dim_coord_names:
        target_dims = variables[coord_name].dims
        for k, v in variables.items():
            if (
                k not in non_dim_coord_names
                and k not in v.dims
                and set(target_dims) <= set(v.dims)
            ):
                variable_coordinates[k].add(coord_name)

            if any(
                attr_name in v.encoding and coord_name in v.encoding.get(attr_name)
                for attr_name in CF_RELATED_DATA
            ):
                not_technically_coordinates.add(coord_name)
                global_coordinates.discard(coord_name)

    variables = {k: v.copy(deep=False) for k, v in variables.items()}

    # keep track of variable names written to file under the "coordinates" attributes
    written_coords = set()
    for name, var in variables.items():
        encoding = var.encoding
        attrs = var.attrs
        if "coordinates" in attrs and "coordinates" in encoding:
            raise ValueError(
                f"'coordinates' found in both attrs and encoding for variable {name!r}."
            )

        # if coordinates set to None, don't write coordinates attribute
        if (
            "coordinates" in attrs
            and attrs.get("coordinates") is None
            or "coordinates" in encoding
            and encoding.get("coordinates") is None
        ):
            # make sure "coordinates" is removed from attrs/encoding
            attrs.pop("coordinates", None)
            encoding.pop("coordinates", None)
            continue

        # this will copy coordinates from encoding to attrs if "coordinates" in attrs
        # after the next line, "coordinates" is never in encoding
        # we get support for attrs["coordinates"] for free.
        coords_str = pop_to(encoding, attrs, "coordinates") or attrs.get("coordinates")
        if not coords_str and variable_coordinates[name]:
            coordinates_text = " ".join(
                str(coord_name)
                for coord_name in variable_coordinates[name]
                if coord_name not in not_technically_coordinates
            )
            if coordinates_text:
                attrs["coordinates"] = coordinates_text
        if "coordinates" in attrs:
            written_coords.update(attrs["coordinates"].split())

    # These coordinates are not associated with any particular variables, so we
    # save them under a global 'coordinates' attribute so xarray can roundtrip
    # the dataset faithfully. Because this serialization goes beyond CF
    # conventions, only do it if necessary.
    # Reference discussion:
    # http://mailman.cgd.ucar.edu/pipermail/cf-metadata/2014/007571.html
    global_coordinates.difference_update(written_coords)
    if global_coordinates:
        attributes = dict(attributes)
        if "coordinates" in attributes:
            warnings.warn(
                f"cannot serialize global coordinates {global_coordinates!r} because the global "
                f"attribute 'coordinates' already exists. This may prevent faithful roundtripping"
                f"of xarray datasets",
                SerializationWarning,
            )
        else:
            attributes["coordinates"] = " ".join(map(str, global_coordinates))

    return variables, attributes


def encode_dataset_coordinates(dataset):
    """Encode coordinates on the given dataset object into variable specific
    and global attributes.

    When possible, this is done according to CF conventions.

    Parameters
    ----------
    dataset : Dataset
        Object to encode.

    Returns
    -------
    variables : dict
    attrs : dict
    """
    non_dim_coord_names = set(dataset.coords) - set(dataset.dims)
    return _encode_coordinates(
        dataset._variables, dataset.attrs, non_dim_coord_names=non_dim_coord_names
    )


def cf_encoder(variables, attributes):
    """
    Encode a set of CF encoded variables and attributes.
    Takes a dicts of variables and attributes and encodes them
    to conform to CF conventions as much as possible.
    This includes masking, scaling, character array handling,
    and CF-time encoding.

    Parameters
    ----------
    variables : dict
        A dictionary mapping from variable name to xarray.Variable
    attributes : dict
        A dictionary mapping from attribute name to value

    Returns
    -------
    encoded_variables : dict
        A dictionary mapping from variable name to xarray.Variable,
    encoded_attributes : dict
        A dictionary mapping from attribute name to value

    See Also
    --------
    decode_cf_variable, encode_cf_variable
    """

    # add encoding for time bounds variables if present.
    _update_bounds_encoding(variables)

    new_vars = {k: encode_cf_variable(v, name=k) for k, v in variables.items()}

    # Remove attrs from bounds variables (issue #2921)
    for var in new_vars.values():
        bounds = var.attrs["bounds"] if "bounds" in var.attrs else None
        if bounds and bounds in new_vars:
            # see http://cfconventions.org/cf-conventions/cf-conventions.html#cell-boundaries
            for attr in [
                "units",
                "standard_name",
                "axis",
                "positive",
                "calendar",
                "long_name",
                "leap_month",
                "leap_year",
                "month_lengths",
            ]:
                if attr in new_vars[bounds].attrs and attr in var.attrs:
                    if new_vars[bounds].attrs[attr] == var.attrs[attr]:
                        new_vars[bounds].attrs.pop(attr)

    return new_vars, attributes
