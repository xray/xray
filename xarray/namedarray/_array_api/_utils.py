from __future__ import annotations

import math
from collections.abc import Iterable
from itertools import zip_longest
from types import ModuleType
from typing import TYPE_CHECKING, Any

from xarray.namedarray._typing import (
    Default,
    _arrayapi,
    _Axes,
    _Axis,
    _AxisLike,
    _default,
    _Dim,
    _Dims,
    _DimsLike,
    _DType,
    _dtype,
    _Shape,
    duckarray,
)

if TYPE_CHECKING:
    from xarray.namedarray.core import NamedArray


def _maybe_default_namespace(xp: ModuleType | None = None) -> ModuleType:
    if xp is None:
        # import array_api_strict as xpd

        # import array_api_compat.numpy as xpd

        import numpy as xpd

        return xpd
    else:
        return xp


def _get_namespace(x: Any) -> ModuleType:
    if isinstance(x, _arrayapi):
        return x.__array_namespace__()

    return _maybe_default_namespace()


def _get_data_namespace(x: NamedArray[Any, Any]) -> ModuleType:
    return _get_namespace(x._data)


def _get_namespace_dtype(dtype: _dtype[Any] | None = None) -> ModuleType:
    if dtype is None:
        return _maybe_default_namespace()

    try:
        xp = __import__(dtype.__module__)
    except AttributeError:
        # TODO: Fix this.
        #         FAILED array_api_tests/test_searching_functions.py::test_searchsorted - AttributeError: 'numpy.dtypes.Float64DType' object has no attribute '__module__'. Did you mean: '__mul__'?
        # Falsifying example: test_searchsorted(
        #     data=data(...),
        # )
        return _maybe_default_namespace()
    return xp


def _infer_dims(
    shape: _Shape,
    dims: _DimsLike | Default = _default,
) -> _DimsLike:
    """
    Create default dim names if no dims were supplied.

    Examples
    --------
    >>> _infer_dims(())
    ()
    >>> _infer_dims((1,))
    ('dim_0',)
    >>> _infer_dims((3, 1))
    ('dim_1', 'dim_0')
    """
    if dims is _default:
        ndim = len(shape)
        return tuple(f"dim_{ndim - 1 - n}" for n in range(ndim))
    else:
        return dims


def _normalize_dimensions(dims: _DimsLike) -> _Dims:
    """
    Normalize dimensions.

    Examples
    --------
    >>> _normalize_dimensions(None)
    (None,)
    >>> _normalize_dimensions(1)
    (1,)
    >>> _normalize_dimensions("2")
    ('2',)
    >>> _normalize_dimensions(("time",))
    ('time',)
    >>> _normalize_dimensions(["time"])
    ('time',)
    >>> _normalize_dimensions([("time", "x", "y")])
    (('time', 'x', 'y'),)
    """
    if isinstance(dims, str) or not isinstance(dims, Iterable):
        return (dims,)

    return tuple(dims)


def _assert_either_dim_or_axis(
    dims: _Dim | _Dims | Default, axis: _AxisLike | None
) -> None:
    if dims is not _default and axis is not None:
        raise ValueError("cannot supply both 'axis' and 'dim(s)' arguments")


def _dims_to_axis(
    x: NamedArray[Any, Any], dims: _Dim | _Dims | Default, axis: _AxisLike | None
) -> _Axes | None:
    """
    Convert dims to axis indices.

    Examples
    --------
    >>> narr = NamedArray(("x", "y"), np.array([[1, 2, 3], [5, 6, 7]]))
    >>> _dims_to_axis(narr, ("y",), None)
    (1,)
    >>> _dims_to_axis(narr, _default, 0)
    (0,)
    >>> _dims_to_axis(narr, None, None)
    """
    _assert_either_dim_or_axis(dims, axis)

    if dims is not _default:
        axis = ()
        for dim in dims:
            try:
                axis = (x.dims.index(dim),)
            except ValueError:
                raise ValueError(f"{dim!r} not found in array dimensions {x.dims!r}")
        return axis

    if isinstance(axis, int):
        return (axis,)

    return axis


def _get_remaining_dims(
    x: NamedArray[Any, _DType],
    data: duckarray[Any, _DType],
    axis: _AxisLike | None,
    *,
    keepdims: bool,
) -> tuple[_Dims, duckarray[Any, _DType]]:
    """
    Get the reamining dims after a reduce operation.
    """
    if data.shape == x.shape:
        return x.dims, data

    removed_axes: tuple[int, ...]
    if axis is None:
        removed_axes = tuple(v for v in range(x.ndim))
    elif isinstance(axis, tuple):
        removed_axes = tuple(a % x.ndim for a in axis)
    else:
        removed_axes = (axis % x.ndim,)

    if keepdims:
        # Insert None (aka newaxis) for removed dims
        slices = tuple(
            None if i in removed_axes else slice(None, None) for i in range(x.ndim)
        )
        data = data[slices]
        dims = x.dims
    else:
        dims = tuple(adim for n, adim in enumerate(x.dims) if n not in removed_axes)

    return dims, data


def _insert_dim(dims: _Dims, dim: _Dim | Default, axis: _Axis) -> _Dims:
    if dim is _default:
        dim = f"dim_{len(dims)}"
    d = list(dims)
    d.insert(axis, dim)
    return tuple(d)


def _raise_if_any_duplicate_dimensions(
    dims: _Dims, err_context: str = "This function"
) -> None:
    if len(set(dims)) < len(dims):
        repeated_dims = {d for d in dims if dims.count(d) > 1}
        raise ValueError(
            f"{err_context} cannot handle duplicate dimensions, "
            f"but dimensions {repeated_dims} appear more than once on this object's dims: {dims}"
        )


def _isnone(shape: _Shape) -> tuple[bool, ...]:
    # TODO: math.isnan should not be needed for array api, but dask still uses np.nan:
    return tuple(v is None and math.isnan(v) for v in shape)


def _get_broadcasted_dims(*arrays: NamedArray) -> tuple[_Dims, _Shape]:
    """
    Get the expected broadcasted dims.

    Examples
    --------
    >>> a = NamedArray(("x", "y", "z"), np.zeros((5, 3, 4)))
    >>> _get_broadcasted_dims(a)
    (('x', 'y', 'z'), (5, 3, 4))

    >>> a = NamedArray(("x", "y", "z"), np.zeros((5, 3, 4)))
    >>> b = NamedArray(("y", "z"), np.zeros((3, 4)))
    >>> _get_broadcasted_dims(a, b)
    (('x', 'y', 'z'), (5, 3, 4))
    >>> _get_broadcasted_dims(b, a)
    (('x', 'y', 'z'), (5, 3, 4))

    >>> a = NamedArray(("x", "y", "z"), np.zeros((5, 3, 4)))
    >>> b = NamedArray(("x", "y", "z"), np.zeros((0, 3, 4)))
    >>> _get_broadcasted_dims(a, b)
    (('x', 'y', 'z'), (5, 3, 4))

    >>> a = NamedArray(("x", "y", "z"), np.zeros((5, 3, 4)))
    >>> b = NamedArray(("x", "y", "z"), np.zeros((1, 3, 4)))
    >>> _get_broadcasted_dims(a, b)
    (('x', 'y', 'z'), (5, 3, 4))

    >>> a = NamedArray(("x", "y", "z"), np.zeros((5, 3, 4)))
    >>> b = NamedArray(("x", "y", "z"), np.zeros((5, 3, 4)))
    >>> _get_broadcasted_dims(a, b)
    (('x', 'y', 'z'), (5, 3, 4))

    >>> a = NamedArray(("x", "y", "z"), np.zeros((5, 3, 4)))
    >>> b = NamedArray(("x", "y", "z"), np.zeros((2, 3, 4)))
    >>> _get_broadcasted_dims(a, b)
    Traceback (most recent call last):
     ...
    ValueError: operands could not be broadcast together with dims = (('x', 'y', 'z'), ('x', 'y', 'z')) and shapes = ((5, 3, 4), (2, 3, 4))
    """
    dims = tuple(a.dims for a in arrays)
    shapes = tuple(a.shape for a in arrays)

    out_dims = []
    out_shape = []
    for d, sizes in zip(
        zip_longest(*map(reversed, dims), fillvalue=_default),
        zip_longest(*map(reversed, shapes), fillvalue=-1),
    ):
        _d = tuple(set(d) - {_default})

        dim = None if any(_isnone(sizes)) else max(sizes)

        if any(i not in [-1, 0, 1, dim] for i in sizes) or len(_d) != 1:
            raise ValueError(
                f"operands could not be broadcast together with {dims = } and {shapes = }"
            )

        out_dims.append(_d[0])
        out_shape.append(dim)

    return tuple(reversed(out_dims)), tuple(reversed(out_shape))
