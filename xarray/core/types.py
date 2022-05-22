from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Literal, Sequence, TypeVar, Union

import numpy as np

if TYPE_CHECKING:
    from .common import DataWithCoords
    from .dataarray import DataArray
    from .dataset import Dataset
    from .groupby import DataArrayGroupBy, GroupBy
    from .indexes import Index
    from .npcompat import ArrayLike
    from .variable import Variable

    try:
        from dask.array import Array as DaskArray
    except ImportError:
        DaskArray = np.ndarray  # type: ignore


T_Dataset = TypeVar("T_Dataset", bound="Dataset")
T_DataArray = TypeVar("T_DataArray", bound="DataArray")
T_Variable = TypeVar("T_Variable", bound="Variable")
T_Index = TypeVar("T_Index", bound="Index")

T_DataArrayOrSet = TypeVar("T_DataArrayOrSet", bound=Union["Dataset", "DataArray"])

# Maybe we rename this to T_Data or something less Fortran-y?
T_Xarray = TypeVar("T_Xarray", "DataArray", "Dataset")
T_DataWithCoords = TypeVar("T_DataWithCoords", bound="DataWithCoords")

ScalarOrArray = Union["ArrayLike", np.generic, np.ndarray, "DaskArray"]
DsCompatible = Union["Dataset", "DataArray", "Variable", "GroupBy", "ScalarOrArray"]
DaCompatible = Union["DataArray", "Variable", "DataArrayGroupBy", "ScalarOrArray"]
VarCompatible = Union["Variable", "ScalarOrArray"]
GroupByIncompatible = Union["Variable", "GroupBy"]

ErrorOptions = Literal["raise", "ignore"]
ErrorOptionsWithWarn = Literal["raise", "warn", "ignore"]
CompatOptions = Literal[
    "identical", "equals", "broadcast_equals", "no_conflicts", "override", "minimal"
]
ConcatOptions = Literal["all", "minimal", "different"]
CombineAttrsOptions = Union[
    Literal["drop", "identical", "no_conflicts", "drop_conflicts", "override"],
    Callable[..., Any],
]
JoinOptions = Literal["outer", "inner", "left", "right", "exact", "override"]
InterpOptions = Literal["linear", "nearest", "zero", "slinear", "quadratic", "cubic"]

# TODO: Wait until mypy supports recursive objects in combination with typevars
_T = TypeVar("_T")
NestedSequence = Union[
    _T,
    Sequence[_T],
    Sequence[Sequence[_T]],
    Sequence[Sequence[Sequence[_T]]],
    Sequence[Sequence[Sequence[Sequence[_T]]]],
]
