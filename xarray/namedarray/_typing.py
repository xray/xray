from __future__ import annotations

import sys
from collections.abc import Hashable, Iterable, Mapping, Sequence
from enum import Enum
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Final,
    Literal,
    Protocol,
    SupportsIndex,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

import numpy as np

try:
    if sys.version_info >= (3, 11):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias
except ImportError:
    if TYPE_CHECKING:
        raise
    else:
        Self: Any = None


# Singleton type, as per https://github.com/python/typing/pull/240
class Default(Enum):
    token: Final = 0


_default = Default.token

# https://stackoverflow.com/questions/74633074/how-to-type-hint-a-generic-numpy-array
_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)

_generic = Any
# _generic = np.generic


class _DType2(Protocol[_T_co]):
    def __eq__(self, other: _DType2[_generic], /) -> bool:
        """
        Computes the truth value of ``self == other`` in order to test for data type object equality.

        Parameters
        ----------
        self: dtype
            data type instance. May be any supported data type.
        other: dtype
            other data type instance. May be any supported data type.

        Returns
        -------
        out: bool
            a boolean indicating whether the data type objects are equal.
        """
        ...


_dtype = np.dtype
_DType = TypeVar("_DType", bound=_dtype[Any])
_DType_co = TypeVar("_DType_co", covariant=True, bound=_dtype[Any])
# A subset of `npt.DTypeLike` that can be parametrized w.r.t. `np.generic`

# _ScalarType = TypeVar("_ScalarType", bound=_generic)
# _ScalarType_co = TypeVar("_ScalarType_co", bound=_generic, covariant=True)
_ScalarType = TypeVar("_ScalarType", bound=np.generic)
_ScalarType_co = TypeVar("_ScalarType_co", bound=np.generic, covariant=True)


# A protocol for anything with the dtype attribute
@runtime_checkable
class _SupportsDType(Protocol[_DType_co]):
    @property
    def dtype(self) -> _DType_co: ...


_DTypeLike = Union[
    _dtype[_ScalarType],
    type[_ScalarType],
    _SupportsDType[_dtype[_ScalarType]],
]

# For unknown shapes Dask uses np.nan, array_api uses None:
_IntOrUnknown = int
_Shape = tuple[_IntOrUnknown, ...]
_ShapeLike = Union[SupportsIndex, Sequence[SupportsIndex]]
_ShapeType = TypeVar("_ShapeType", bound=Any)
_ShapeType_co = TypeVar("_ShapeType_co", bound=Any, covariant=True)

_Axis = int
_Axes = tuple[_Axis, ...]
_AxisLike = Union[_Axis, _Axes]

_Chunk = tuple[int, ...]
_Chunks = tuple[_Chunk, ...]
_NormalizedChunks = tuple[tuple[int, ...], ...]  # TODO: Same as Chunks.
_ChunksLike = Union[
    int, Literal["auto"], None, _Chunk, _Chunks
]  # TODO: Literal["auto"]
_ChunksType = TypeVar("_ChunksType", bound=_Chunks)

# FYI in some cases we don't allow `None`, which this doesn't take account of.
T_ChunkDim: TypeAlias = Union[int, Literal["auto"], None, tuple[int, ...]]
# We allow the tuple form of this (though arguably we could transition to named dims only)
T_Chunks: TypeAlias = Union[T_ChunkDim, Mapping[Any, T_ChunkDim]]

_Dim = Hashable
_Dims = tuple[_Dim, ...]

_DimsLike = Union[str, Iterable[_Dim]]

# https://data-apis.org/array-api/latest/API_specification/indexing.html
# TODO: np.array_api was bugged and didn't allow (None,), but should!
# https://github.com/numpy/numpy/pull/25022
# https://github.com/data-apis/array-api/pull/674
_IndexKey = Union[int, slice, "ellipsis"]
_IndexKeys = tuple[Union[_IndexKey], ...]  #  tuple[Union[_IndexKey, None], ...]
_IndexKeyLike = Union[_IndexKey, _IndexKeys]

_AttrsLike = Union[Mapping[Any, Any], None]


class _SupportsReal(Protocol[_T_co]):
    @property
    def real(self) -> _T_co: ...


class _SupportsImag(Protocol[_T_co]):
    @property
    def imag(self) -> _T_co: ...


@runtime_checkable
class _array(Protocol[_ShapeType_co, _DType_co]):
    """
    Minimal duck array named array uses.

    Corresponds to np.ndarray.
    """

    @property
    def shape(self) -> _Shape: ...

    @property
    def dtype(self) -> _DType_co: ...


@runtime_checkable
class _arrayfunction(_array[_ShapeType, _DType_co], Protocol[_ShapeType, _DType_co]):
    """
    Duck array supporting NEP 18.

    Corresponds to np.ndarray.
    """

    @overload
    def __getitem__(
        self, key: _arrayfunction[Any, Any] | tuple[_arrayfunction[Any, Any], ...], /
    ) -> _arrayfunction[Any, _DType_co]: ...

    @overload
    def __getitem__(self, key: _IndexKeyLike, /) -> Any: ...

    def __getitem__(
        self,
        key: (
            _IndexKeyLike
            | _arrayfunction[Any, Any]
            | tuple[_arrayfunction[Any, Any], ...]
        ),
        /,
    ) -> _arrayfunction[Any, _DType_co] | Any: ...

    @overload
    def __array__(self, dtype: None = ..., /) -> np.ndarray[_ShapeType, _DType_co]: ...

    @overload
    def __array__(self, dtype: _DType, /) -> np.ndarray[_ShapeType, _DType]: ...

    def __array__(
        self, dtype: _DType | None = ..., /
    ) -> np.ndarray[_ShapeType, _DType] | np.ndarray[_ShapeType, _DType_co]: ...

    # TODO: Should return the same subclass but with a new dtype generic.
    # https://github.com/python/typing/issues/548
    def __array_ufunc__(
        self,
        ufunc: Any,
        method: Any,
        *inputs: Any,
        **kwargs: Any,
    ) -> Any: ...

    # TODO: Should return the same subclass but with a new dtype generic.
    # https://github.com/python/typing/issues/548
    def __array_function__(
        self,
        func: Callable[..., Any],
        types: Iterable[type],
        args: Iterable[Any],
        kwargs: Mapping[str, Any],
    ) -> Any: ...

    @property
    def imag(self) -> _arrayfunction[_ShapeType, Any]: ...

    @property
    def real(self) -> _arrayfunction[_ShapeType, Any]: ...


@runtime_checkable
class _arrayapi(_array[_ShapeType_co, _DType_co], Protocol[_ShapeType_co, _DType_co]):
    """
    Duck array supporting NEP 47.

    Corresponds to np.ndarray.
    """

    def __getitem__(
        self,
        key: (
            _IndexKeyLike | Any
        ),  # TODO: Any should be _arrayapi[Any, _dtype[np.integer]]
        /,
    ) -> _arrayapi[Any, Any]: ...

    def __array_namespace__(self) -> ModuleType: ...


# NamedArray can most likely use both __array_function__ and __array_namespace__:
_arrayfunction_or_api = (_arrayfunction, _arrayapi)

duckarray = Union[
    _arrayfunction[_ShapeType_co, _DType_co], _arrayapi[_ShapeType_co, _DType_co]
]

# Corresponds to np.typing.NDArray:
DuckArray = _arrayfunction[Any, _dtype[_ScalarType_co]]


@runtime_checkable
class _chunkedarray(
    _array[_ShapeType_co, _DType_co], Protocol[_ShapeType_co, _DType_co]
):
    """
    Minimal chunked duck array.

    Corresponds to np.ndarray.
    """

    @property
    def chunks(self) -> _Chunks: ...


@runtime_checkable
class _chunkedarrayfunction(
    _arrayfunction[_ShapeType, _DType_co], Protocol[_ShapeType, _DType_co]
):
    """
    Chunked duck array supporting NEP 18.

    Corresponds to np.ndarray.
    """

    @property
    def chunks(self) -> _Chunks: ...

    def rechunk(
        self,
        chunks: _ChunksLike,
    ) -> _chunkedarrayfunction[_ShapeType, _DType_co]: ...


@runtime_checkable
class _chunkedarrayapi(
    _arrayapi[_ShapeType_co, _DType_co], Protocol[_ShapeType_co, _DType_co]
):
    """
    Chunked duck array supporting NEP 47.

    Corresponds to np.ndarray.
    """

    @property
    def chunks(self) -> _Chunks: ...

    def rechunk(
        self,
        chunks: _ChunksLike,
    ) -> _chunkedarrayapi[_ShapeType_co, _DType_co]: ...


# NamedArray can most likely use both __array_function__ and __array_namespace__:
_chunkedarrayfunction_or_api = (_chunkedarrayfunction, _chunkedarrayapi)
chunkedduckarray = Union[
    _chunkedarrayfunction[_ShapeType_co, _DType_co],
    _chunkedarrayapi[_ShapeType_co, _DType_co],
]


@runtime_checkable
class _sparsearray(
    _array[_ShapeType_co, _DType_co], Protocol[_ShapeType_co, _DType_co]
):
    """
    Minimal sparse duck array.

    Corresponds to np.ndarray.
    """

    def todense(self) -> np.ndarray[Any, np.dtype[np.generic]]: ...


@runtime_checkable
class _sparsearrayfunction(
    _arrayfunction[_ShapeType, _DType_co], Protocol[_ShapeType, _DType_co]
):
    """
    Sparse duck array supporting NEP 18.

    Corresponds to np.ndarray.
    """

    def todense(self) -> np.ndarray[Any, np.dtype[np.generic]]: ...


@runtime_checkable
class _sparsearrayapi(
    _arrayapi[_ShapeType_co, _DType_co], Protocol[_ShapeType_co, _DType_co]
):
    """
    Sparse duck array supporting NEP 47.

    Corresponds to np.ndarray.
    """

    def todense(self) -> np.ndarray[Any, np.dtype[np.generic]]: ...


# NamedArray can most likely use both __array_function__ and __array_namespace__:
_sparsearrayfunction_or_api = (_sparsearrayfunction, _sparsearrayapi)
sparseduckarray = Union[
    _sparsearrayfunction[_ShapeType_co, _DType_co],
    _sparsearrayapi[_ShapeType_co, _DType_co],
]

ErrorOptions = Literal["raise", "ignore"]
ErrorOptionsWithWarn = Literal["raise", "warn", "ignore"]


# def test(arr: duckarray[_ShapeType, _DType]) -> duckarray[_ShapeType, _DType]:
#     return np.round(arr)


# test(np.array([], dtype=np.int64))


# def test2(arr: _arrayfunction[Any, _DType]) -> _arrayfunction[Any, _DType]:
#     return np.round(arr)
#     # return np.asarray(arr)
#     # return arr.__array__()
#     # return arr


# test2(np.array([], dtype=np.int64))
