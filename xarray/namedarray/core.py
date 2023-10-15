from __future__ import annotations

import copy
import math
import sys
from collections.abc import Hashable, Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Literal,
    TypeVar,
    cast,
    overload,
)

import numpy as np

# TODO: get rid of this after migrating this class to array API
from xarray.core import dtypes
from xarray.namedarray._typing import (
    _arrayfunction_or_api,
    _DType,
    _DType_co,
    _ScalarType_co,
    _ShapeType_co,
)
from xarray.namedarray.utils import (
    _default,
    is_chunked_duck_array,
    is_duck_dask_array,
    to_0d_object_array,
)

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

    from xarray.namedarray._typing import (
        DuckArray,
        _AttrsLike,
        _Chunks,
        _Dim,
        _Dims,
        _DimsLike,
        _IntOrUnknown,
        _ScalarType,
        _Shape,
        duckarray,
    )
    from xarray.namedarray.utils import Default

    try:
        from dask.typing import (
            Graph,
            NestedKeys,
            PostComputeCallable,
            PostPersistCallable,
            SchedulerGetCallable,
        )
    except ImportError:
        Graph: Any  # type: ignore[no-redef]
        NestedKeys: Any  # type: ignore[no-redef]
        SchedulerGetCallable: Any  # type: ignore[no-redef]
        PostComputeCallable: Any  # type: ignore[no-redef]
        PostPersistCallable: Any  # type: ignore[no-redef]

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    T_NamedArray = TypeVar("T_NamedArray", bound="_NamedArray[Any]")
    T_NamedArrayInteger = TypeVar(
        "T_NamedArrayInteger", bound="_NamedArray[np.integer[Any]]"
    )


@overload
def _new(
    x: NamedArray[Any, _DType_co],
    dims: _DimsLike | Default = ...,
    data: duckarray[Any, _DType] = ...,
    attrs: _AttrsLike | Default = ...,
) -> NamedArray[Any, _DType]:
    ...


@overload
def _new(
    x: NamedArray[Any, _DType_co],
    dims: _DimsLike | Default = ...,
    data: Default = ...,
    attrs: _AttrsLike | Default = ...,
) -> NamedArray[Any, _DType_co]:
    ...


def _new(
    x: NamedArray[Any, _DType_co],
    dims: _DimsLike | Default = _default,
    data: duckarray[Any, _DType] | Default = _default,
    attrs: _AttrsLike | Default = _default,
) -> NamedArray[Any, _DType] | NamedArray[Any, _DType_co]:
    dims_ = copy.copy(x._dims) if dims is _default else dims

    attrs_: Mapping[Any, Any] | None
    if attrs is _default:
        attrs_ = None if x._attrs is None else x._attrs.copy()
    else:
        attrs_ = attrs

    if data is _default:
        return type(x)(dims_, copy.copy(x._data), attrs_)
    else:
        cls_ = cast("type[NamedArray[Any, _DType]]", type(x))
        return cls_(dims_, data, attrs_)


@overload
def from_array(
    dims: _DimsLike,
    data: DuckArray[_ScalarType],
    attrs: _AttrsLike = ...,
) -> _NamedArray[_ScalarType]:
    ...


@overload
def from_array(
    dims: _DimsLike,
    data: ArrayLike,
    attrs: _AttrsLike = ...,
) -> _NamedArray[Any]:
    ...


def from_array(
    dims: _DimsLike,
    data: DuckArray[_ScalarType] | ArrayLike,
    attrs: _AttrsLike = None,
) -> _NamedArray[_ScalarType] | _NamedArray[Any]:
    """
    Create a Named array from an array-like object.

    Parameters
    ----------
    dims : str or iterable of str
        Name(s) of the dimension(s).
    data : T_DuckArray or ArrayLike
        The actual data that populates the array. Should match the
        shape specified by `dims`.
    attrs : dict, optional
        A dictionary containing any additional information or
        attributes you want to store with the array.
        Default is None, meaning no attributes will be stored.
    """
    if isinstance(data, NamedArray):
        raise TypeError(
            "Array is already a Named array. Use 'data.data' to retrieve the data array"
        )

    # TODO: dask.array.ma.masked_array also exists, better way?
    if isinstance(data, np.ma.MaskedArray):
        mask = np.ma.getmaskarray(data)  # type: ignore[no-untyped-call]
        if mask.any():
            # TODO: requires refactoring/vendoring xarray.core.dtypes and
            # xarray.core.duck_array_ops
            raise NotImplementedError("MaskedArray is not supported yet")

        return NamedArray(dims, data, attrs)

    if isinstance(data, _arrayfunction_or_api):
        return NamedArray(dims, data, attrs)
    else:
        if isinstance(data, tuple):
            return NamedArray(dims, to_0d_object_array(data), attrs)
        else:
            # validate whether the data is valid data types.
            return NamedArray(dims, np.asarray(data), attrs)


class NamedArray(Generic[_ShapeType_co, _DType_co]):
    """
    A wrapper around duck arrays with named dimensions
    and attributes which describe a single Array.
    Numeric operations on this object implement array broadcasting and
    dimension alignment based on dimension names,
    rather than axis order.


    Parameters
    ----------
    dims : str or iterable of str
        Name(s) of the dimension(s).
    data : T_DuckArray
        The actual data that populates the array. Should match the
        shape specified by `dims`.
    attrs : dict, optional
        A dictionary containing any additional information or
        attributes you want to store with the array.
        Default is None, meaning no attributes will be stored.

    Raises
    ------
    ValueError
        If the `dims` length does not match the number of data dimensions (ndim).


    Examples
    --------
    >>> data = np.array([1.5, 2, 3], dtype=float)
    >>> narr = NamedArray(("x",), data, {"units": "m"})  # TODO: Better name than narr?
    """

    __slots__ = ("_data", "_dims", "_attrs")

    _data: duckarray[Any, _DType_co]
    _dims: _Dims
    _attrs: dict[Any, Any] | None

    def __init__(
        self,
        dims: _DimsLike,
        data: duckarray[Any, _DType_co],
        attrs: _AttrsLike = None,
    ):
        self._data = data
        self._dims = self._parse_dimensions(dims)
        self._attrs = dict(attrs) if attrs else None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if NamedArray in cls.__bases__ and (cls._new == NamedArray._new):
            # Type hinting does not work for subclasses unless _new is overriden with
            # the correct class.
            raise TypeError(
                "Subclasses of `NamedArray` must override the `_new` method."
            )
        super().__init_subclass__(**kwargs)

    @overload
    def _new(
        self,
        dims: _DimsLike | Default = ...,
        data: duckarray[Any, _DType] = ...,
        attrs: _AttrsLike | Default = ...,
    ) -> NamedArray[Any, _DType]:
        ...

    @overload
    def _new(
        self,
        dims: _DimsLike | Default = ...,
        data: Default = ...,
        attrs: _AttrsLike | Default = ...,
    ) -> NamedArray[Any, _DType_co]:
        ...

    def _new(
        self,
        dims: _DimsLike | Default = _default,
        data: duckarray[Any, _DType] | Default = _default,
        attrs: _AttrsLike | Default = _default,
    ) -> NamedArray[Any, _DType] | NamedArray[Any, _DType_co]:
        return _new(self, dims, data, attrs)

    def _replace(
        self,
        dims: _DimsLike | Default = _default,
        data: duckarray[Any, _DType_co] | Default = _default,
        attrs: _AttrsLike | Default = _default,
    ) -> Self:
        """
        Create a new Named array with dims, data or attrs.

        The types for each argument cannot change,
        use self._new if that is a risk.
        """
        return cast(Self, self._new(dims, data, attrs))

    def _copy(
        self,
        deep: bool = True,
        data: duckarray[Any, _DType_co] | None = None,
        memo: dict[int, Any] | None = None,
    ) -> Self:
        if data is None:
            ndata = self._data
            if deep:
                ndata = copy.deepcopy(ndata, memo=memo)
        else:
            ndata = data
            self._check_shape(ndata)

        attrs = (
            copy.deepcopy(self._attrs, memo=memo) if deep else copy.copy(self._attrs)
        )

        return self._replace(data=ndata, attrs=attrs)

    def __copy__(self) -> Self:
        return self._copy(deep=False)

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
        return self._copy(deep=True, memo=memo)

    def copy(
        self,
        deep: bool = True,
        data: duckarray[Any, _DType_co] | None = None,
    ) -> Self:
        """Returns a copy of this object.

        If `deep=True`, the data array is loaded into memory and copied onto
        the new object. Dimensions, attributes and encodings are always copied.

        Use `data` to create a new object with the same structure as
        original but entirely new data.

        Parameters
        ----------
        deep : bool, default: True
            Whether the data array is loaded into memory and copied onto
            the new object. Default is True.
        data : array_like, optional
            Data to use in the new object. Must have same shape as original.
            When `data` is used, `deep` is ignored.

        Returns
        -------
        object : NamedArray
            New object with dimensions, attributes, and optionally
            data copied from original.


        """
        return self._copy(deep=deep, data=data)

    @property
    def ndim(self) -> _IntOrUnknown:
        """
        Number of array dimensions.

        See Also
        --------
        numpy.ndarray.ndim
        """
        return len(self.shape)

    @property
    def size(self) -> _IntOrUnknown:
        """
        Number of elements in the array.

        Equal to ``np.prod(a.shape)``, i.e., the product of the array’s dimensions.

        See Also
        --------
        numpy.ndarray.size
        """
        return math.prod(self.shape)

    def __len__(self) -> _IntOrUnknown:
        try:
            return self.shape[0]
        except Exception as exc:
            raise TypeError("len() of unsized object") from exc

    @property
    def dtype(self) -> _DType_co:
        """
        Data-type of the array’s elements.

        See Also
        --------
        ndarray.dtype
        numpy.dtype
        """
        return self._data.dtype

    @property
    def shape(self) -> _Shape:
        """


        Returns
        -------
        shape : tuple of ints
                Tuple of array dimensions.



        See Also
        --------
        numpy.ndarray.shape
        """
        return self._data.shape

    @property
    def nbytes(self) -> _IntOrUnknown:
        """
        Total bytes consumed by the elements of the data array.

        If the underlying data array does not include ``nbytes``, estimates
        the bytes consumed based on the ``size`` and ``dtype``.
        """
        if hasattr(self._data, "nbytes"):
            return self._data.nbytes  # type: ignore[no-any-return]
        else:
            return self.size * self.dtype.itemsize

    @property
    def dims(self) -> _Dims:
        """Tuple of dimension names with which this NamedArray is associated."""
        return self._dims

    @dims.setter
    def dims(self, value: _DimsLike) -> None:
        self._dims = self._parse_dimensions(value)

    def _parse_dimensions(self, dims: _DimsLike) -> _Dims:
        dims = (dims,) if isinstance(dims, str) else tuple(dims)
        if len(dims) != self.ndim:
            raise ValueError(
                f"dimensions {dims} must have the same length as the "
                f"number of data dimensions, ndim={self.ndim}"
            )
        return dims

    @property
    def attrs(self) -> dict[Any, Any]:
        """Dictionary of local attributes on this NamedArray."""
        if self._attrs is None:
            self._attrs = {}
        return self._attrs

    @attrs.setter
    def attrs(self, value: Mapping[Any, Any]) -> None:
        self._attrs = dict(value)

    def _check_shape(self, new_data: duckarray[Any, _DType_co]) -> None:
        if new_data.shape != self.shape:
            raise ValueError(
                f"replacement data must match the {self.__class__.__name__}'s shape. "
                f"replacement data has shape {new_data.shape}; {self.__class__.__name__} has shape {self.shape}"
            )

    @property
    def data(self) -> duckarray[Any, _DType_co]:
        """
        The NamedArray's data as an array. The underlying array type
        (e.g. dask, sparse, pint) is preserved.

        """

        return self._data

    @data.setter
    def data(self, data: duckarray[Any, _DType_co]) -> None:
        self._check_shape(data)
        self._data = data

    def __dask_tokenize__(self) -> Hashable:
        # Use v.data, instead of v._data, in order to cope with the wrappers
        # around NetCDF and the like
        from dask.base import normalize_token

        s, d, a, attrs = type(self), self._dims, self.data, self.attrs
        return normalize_token((s, d, a, attrs))  # type: ignore[no-any-return]

    def __dask_graph__(self) -> Graph | None:
        if is_duck_dask_array(self._data):
            return self._data.__dask_graph__()
        else:
            # TODO: Should this method just raise instead?
            # raise NotImplementedError("Method requires self.data to be a dask array")
            return None

    def __dask_keys__(self) -> NestedKeys:
        if is_duck_dask_array(self._data):
            return self._data.__dask_keys__()
        else:
            raise AttributeError("Method requires self.data to be a dask array.")

    def __dask_layers__(self) -> Sequence[str]:
        if is_duck_dask_array(self._data):
            return self._data.__dask_layers__()
        else:
            raise AttributeError("Method requires self.data to be a dask array.")

    @property
    def __dask_optimize__(
        self,
    ) -> Callable[..., dict[Any, Any]]:
        if is_duck_dask_array(self._data):
            return self._data.__dask_optimize__  # type: ignore[no-any-return]
        else:
            raise AttributeError("Method requires self.data to be a dask array.")

    @property
    def __dask_scheduler__(self) -> SchedulerGetCallable:
        if is_duck_dask_array(self._data):
            return self._data.__dask_scheduler__
        else:
            raise AttributeError("Method requires self.data to be a dask array.")

    def __dask_postcompute__(
        self,
    ) -> tuple[PostComputeCallable, tuple[Any, ...]]:
        if is_duck_dask_array(self._data):
            array_func, array_args = self._data.__dask_postcompute__()  # type: ignore[no-untyped-call]
            return self._dask_finalize, (array_func,) + array_args
        else:
            raise AttributeError("Method requires self.data to be a dask array.")

    def __dask_postpersist__(
        self,
    ) -> tuple[
        Callable[
            [Graph, PostPersistCallable[Any], Any, Any],
            Self,
        ],
        tuple[Any, ...],
    ]:
        if is_duck_dask_array(self._data):
            a: tuple[PostPersistCallable[Any], tuple[Any, ...]]
            a = self._data.__dask_postpersist__()  # type: ignore[no-untyped-call]
            array_func, array_args = a

            return self._dask_finalize, (array_func,) + array_args
        else:
            raise AttributeError("Method requires self.data to be a dask array.")

    def _dask_finalize(
        self,
        results: Graph,
        array_func: PostPersistCallable[Any],
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        data = array_func(results, *args, **kwargs)
        return type(self)(self._dims, data, attrs=self._attrs)

    @property
    def chunks(self) -> _Chunks | None:
        """
        Tuple of block lengths for this NamedArray's data, in order of dimensions, or None if
        the underlying data is not a dask array.

        See Also
        --------
        NamedArray.chunk
        NamedArray.chunksizes
        xarray.unify_chunks
        """
        data = self._data
        if is_chunked_duck_array(data):
            return data.chunks
        else:
            return None

    @property
    def chunksizes(
        self,
    ) -> Mapping[_Dim, _Shape]:
        """
        Mapping from dimension names to block lengths for this namedArray's data, or None if
        the underlying data is not a dask array.
        Cannot be modified directly, but can be modified by calling .chunk().

        Differs from NamedArray.chunks because it returns a mapping of dimensions to chunk shapes
        instead of a tuple of chunk shapes.

        See Also
        --------
        NamedArray.chunk
        NamedArray.chunks
        xarray.unify_chunks
        """
        data = self._data
        if is_chunked_duck_array(data):
            return dict(zip(self.dims, data.chunks))
        else:
            return {}

    @property
    def sizes(self) -> dict[_Dim, _IntOrUnknown]:
        """Ordered mapping from dimension names to lengths."""
        return dict(zip(self.dims, self.shape))

    def _nonzero(self: T_NamedArrayInteger) -> tuple[T_NamedArrayInteger, ...]:
        """Equivalent numpy's nonzero but returns a tuple of NamedArrays."""
        # TODO: we should replace dask's native nonzero
        # after https://github.com/dask/dask/issues/1076 is implemented.
        # TODO: cast to ndarray and back to T_DuckArray is a workaround
        nonzeros = np.nonzero(cast("NDArray[np.integer[Any]]", self.data))
        _attrs = self.attrs
        return tuple(
            self._new((dim,), nz, _attrs) for nz, dim in zip(nonzeros, self.dims)
        )

    def _as_sparse(
        self,
        sparse_format: Literal["coo"] | Default = _default,
        fill_value: ArrayLike | Default = _default,
    ) -> Self:
        """
        use sparse-array as backend.
        """
        import sparse

        from xarray.namedarray._array_api import astype

        # TODO: what to do if dask-backended?
        if fill_value is _default:
            dtype, fill_value = dtypes.maybe_promote(self.dtype)
        else:
            dtype = dtypes.result_type(self.dtype, fill_value)

        if sparse_format is _default:
            sparse_format = "coo"
        try:
            as_sparse = getattr(sparse, f"as_{sparse_format.lower()}")
        except AttributeError as exc:
            raise ValueError(f"{sparse_format} is not a valid sparse format") from exc

        data = as_sparse(astype(self, dtype).data, fill_value=fill_value)
        return self._replace(data=data)

    def _to_dense(self) -> Self:
        """
        Change backend from sparse to np.array
        """
        from xarray.namedarray._typing import _sparsearrayfunction_or_api

        if isinstance(self._data, _sparsearrayfunction_or_api):
            # return self._replace(data=self._data.todense())
            data_: np.ndarray[Any, Any] = self._data.todense()
            return self._replace(data=data_)
        else:
            raise TypeError("self.data is not a sparse array")


_NamedArray = NamedArray[Any, np.dtype[_ScalarType_co]]
