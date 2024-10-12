from __future__ import annotations

from typing import Any, overload

from xarray.namedarray._array_api._utils import (
    _get_data_namespace,
    _get_namespace,
    _get_namespace_dtype,
    _infer_dims,
)
from xarray.namedarray._typing import (
    Default,
    _ArrayLike,
    _default,
    _Device,
    _DimsLike2,
    _DType,
    _Shape,
    _Shape1D,
    _ShapeType,
    duckarray,
)
from xarray.namedarray.core import NamedArray


def arange(
    start: int | float,
    /,
    stop: int | float | None = None,
    step: int | float = 1,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
    dims: _DimsLike2 | Default = _default,
) -> NamedArray[_Shape1D, _DType]:
    """
    Returns evenly spaced values within the half-open interval [start, stop) as a one-dimensional array.

    Examples
    --------
    >>> arange(3)
    <xarray.NamedArray (dim_0: 3)> Size: 24B
    array([0, 1, 2])
    >>> arange(3.0)
    <xarray.NamedArray (dim_0: 3)> Size: 24B
    array([0., 1., 2.])
    >>> arange(3,7)
    <xarray.NamedArray (dim_0: 4)> Size: 32B
    array([3, 4, 5, 6])
    >>> arange(3,7,2)
    <xarray.NamedArray (dim_0: 2)> Size: 16B
    array([3, 5])

    If dims is set:

    >>> arange(3, dims="x")
    <xarray.NamedArray (x: 3)> Size: 24B
    array([0, 1, 2])
    """
    xp = _get_namespace_dtype(dtype)
    _data = xp.arange(start, stop=stop, step=step, dtype=dtype, device=device)
    _dims = _infer_dims(_data.shape, dims)
    return NamedArray(_dims, _data)


@overload
def asarray(
    obj: duckarray[_ShapeType, Any],
    /,
    *,
    dtype: _DType,
    device: _Device | None = ...,
    copy: bool | None = ...,
    dims: _DimsLike2 | Default = ...,
) -> NamedArray[_ShapeType, _DType]: ...
@overload
def asarray(
    obj: _ArrayLike,
    /,
    *,
    dtype: _DType,
    device: _Device | None = ...,
    copy: bool | None = ...,
    dims: _DimsLike2 | Default = ...,
) -> NamedArray[Any, _DType]: ...
@overload
def asarray(
    obj: duckarray[_ShapeType, _DType],
    /,
    *,
    dtype: None,
    device: _Device | None = None,
    copy: bool | None = None,
    dims: _DimsLike2 | Default = ...,
) -> NamedArray[_ShapeType, _DType]: ...
@overload
def asarray(
    obj: _ArrayLike,
    /,
    *,
    dtype: None,
    device: _Device | None = ...,
    copy: bool | None = ...,
    dims: _DimsLike2 | Default = ...,
) -> NamedArray[Any, _DType]: ...
def asarray(
    obj: duckarray[_ShapeType, _DType] | _ArrayLike,
    /,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
    copy: bool | None = None,
    dims: _DimsLike2 | Default = _default,
) -> NamedArray[_ShapeType, _DType] | NamedArray[Any, Any]:
    """
    Create a NamedArray from an array-like object.

    Examples
    --------
    Convert a list into an array:

    >>> x = [1, 2]
    >>> asarray(x)
    <xarray.NamedArray (dim_0: 2)> Size: 16B
    array([1, 2])

    Existing arrays are not copied:

    >>> import numpy as np
    >>> x = NamedArray(("x",), np.array([1, 2]))
    >>> asarray(x) is x
    True

    If dtype is set, array is copied only if dtype does not match:

    >>> x = NamedArray(("x",), np.array([1, 2], dtype=np.float32))
    >>> asarray(x, dtype=np.float32) is x
    True
    >>> asarray(x, dtype=np.float64) is x
    False

    If dims is set:

    >>> x = [1, 2]
    >>> asarray(x, dims="x")
    <xarray.NamedArray (x: 2)> Size: 16B
    array([1, 2])

    If dims is set, array is copied only if dims does not match:

    >>> x = NamedArray(("x",), np.array([1, 2], dtype=np.float32))
    >>> asarray(x, dims="x") is x
    True
    >>> asarray(x, dims=("x",)) is x
    True
    >>> asarray(x, dims=("y",)) is x
    False
    """
    data = obj
    if isinstance(data, NamedArray):
        xp = _get_data_namespace(data)
        _dtype = data.dtype if dtype is None else dtype
        new_data = xp.asarray(data._data, dtype=_dtype, device=device, copy=copy)
        if new_data is data._data and (
            isinstance(dims, Default) or _normalize_dimensions(dims) == data.dims
        ):
            return data
        else:
            return NamedArray(
                data.dims if isinstance(dims, Default) else dims, new_data, data.attrs
            )

    xp = _get_namespace(data)
    _data = xp.asarray(data, dtype=dtype, device=device, copy=copy)
    _dims = _infer_dims(_data.shape, dims)
    return NamedArray(_dims, _data)


def empty(
    shape: _ShapeType,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
    dims: _DimsLike2 | Default = _default,
) -> NamedArray[_ShapeType, _DType]:
    """
    Returns an uninitialized array having a specified shape.

    Examples
    --------
    >>> import numpy as np
    >>> x = empty((2, 2))
    >>> x.dims, x.shape, x.dtype
    (('dim_1', 'dim_0'), (2, 2), dtype('float64'))
    >>> x = empty([2, 2], dtype=np.int64)
    >>> x.dims, x.shape, x.dtype
    (('dim_1', 'dim_0'), (2, 2), dtype('int64'))

    If dims is set:

    >>> x = empty((2, 2), dims=("x", "y"))
    >>> x.dims, x.shape, x.dtype
    (('x', 'y'), (2, 2), dtype('float64'))
    """
    xp = _get_namespace_dtype(dtype)
    _data = xp.empty(shape, dtype=dtype, device=device)
    _dims = _infer_dims(_data.shape, dims)
    return NamedArray(_dims, _data)


def empty_like(
    x: NamedArray[_ShapeType, _DType],
    /,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
) -> NamedArray[_ShapeType, _DType]:
    """
    Returns an uninitialized array with the same shape as an input array x.

    Examples
    --------
    >>> import numpy as np
    >>> x = empty_like(NamedArray(("x", "y"), np.array([[1, 2, 3], [4, 5, 6]])))
    >>> x.dims, x.shape, x.dtype
    (('x', 'y'), (2, 3), dtype('int64'))
    """
    xp = _get_data_namespace(x)
    _data = xp.empty_like(x._data, dtype=dtype, device=device)
    return x._new(data=_data)


def eye(
    n_rows: int,
    n_cols: int | None = None,
    /,
    *,
    k: int = 0,
    dtype: _DType | None = None,
    device: _Device | None = None,
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_namespace_dtype(dtype)
    _data = xp.eye(n_rows, n_cols, k=k, dtype=dtype, device=device)
    _dims = _infer_dims(_data.shape)
    return NamedArray(_dims, _data)


def from_dlpack(
    x: object,
    /,
    *,
    device: _Device | None = None,
    copy: bool | None = None,
) -> NamedArray[Any, Any]:
    if isinstance(x, NamedArray):
        xp = _get_data_namespace(x)
        _device = x.device if device is None else device
        _data = xp.from_dlpack(x, device=_device, copy=copy)
        _dims = x.dims
    else:
        xp = _get_namespace(x)
        _device = device
        _data = xp.from_dlpack(x, device=_device, copy=copy)
        _dims = _infer_dims(_data.shape)
    return NamedArray(_dims, _data)


def full(
    shape: _Shape,
    fill_value: bool | int | float | complex,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_namespace_dtype(dtype)
    _data = xp.full(shape, fill_value, dtype=dtype, device=device)
    _dims = _infer_dims(_data.shape)
    return NamedArray(_dims, _data)


def full_like(
    x: NamedArray[_ShapeType, _DType],
    /,
    fill_value: bool | int | float | complex,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_data_namespace(x)
    _data = xp.full_like(x._data, fill_value, dtype=dtype, device=device)
    return x._new(data=_data)


def linspace(
    start: int | float | complex,
    stop: int | float | complex,
    /,
    num: int,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
    endpoint: bool = True,
    dims: _DimsLike2 | Default = _default,
) -> NamedArray[_Shape1D, _DType]:
    xp = _get_namespace_dtype(dtype)
    _data = xp.linspace(
        start,
        stop,
        num=num,
        dtype=dtype,
        device=device,
        endpoint=endpoint,
    )
    _dims = _infer_dims(_data.shape, dims)
    return NamedArray(_dims, _data)


def meshgrid(
    *arrays: NamedArray[Any, Any], indexing: str = "xy"
) -> list[NamedArray[Any, Any]]:
    arr = arrays[0]
    xp = _get_data_namespace(arr)
    _datas = xp.meshgrid(*[a._data for a in arrays], indexing=indexing)
    # TODO: Can probably determine dim names from arrays, for now just default names:
    _dims = _infer_dims(_datas[0].shape)
    return [arr._new(_dims, _data) for _data in _datas]


def ones(
    shape: _Shape, *, dtype: _DType | None = None, device: _Device | None = None
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_namespace_dtype(dtype)
    _data = xp.ones(shape, dtype=dtype, device=device)
    _dims = _infer_dims(_data.shape)
    return NamedArray(_dims, _data)


def ones_like(
    x: NamedArray[_ShapeType, _DType],
    /,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_data_namespace(x)
    _data = xp.ones_like(x._data, dtype=dtype, device=device)
    return x._new(data=_data)


def tril(
    x: NamedArray[_ShapeType, _DType], /, *, k: int = 0
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_data_namespace(x)
    _data = xp.tril(x._data, k=k)
    # TODO: Can probably determine dim names from x, for now just default names:
    _dims = _infer_dims(_data.shape)
    return x._new(_dims, _data)


def triu(
    x: NamedArray[_ShapeType, _DType], /, *, k: int = 0
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_data_namespace(x)
    _data = xp.triu(x._data, k=k)
    # TODO: Can probably determine dim names from x, for now just default names:
    _dims = _infer_dims(_data.shape)
    return x._new(_dims, _data)


def zeros(
    shape: _Shape, *, dtype: _DType | None = None, device: _Device | None = None
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_namespace_dtype(dtype)
    _data = xp.zeros(shape, dtype=dtype, device=device)
    _dims = _infer_dims(_data.shape)
    return NamedArray(_dims, _data)


def zeros_like(
    x: NamedArray[_ShapeType, _DType],
    /,
    *,
    dtype: _DType | None = None,
    device: _Device | None = None,
) -> NamedArray[_ShapeType, _DType]:
    xp = _get_data_namespace(x)
    _data = xp.zeros_like(x._data, dtype=dtype, device=device)
    return x._new(data=_data)
