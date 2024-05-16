from __future__ import annotations

import numpy as np
import pytest

from xarray.core import dtypes
from xarray.tests import requires_array_api_strict

try:
    import array_api_strict
except ImportError:

    class DummyArrayAPINamespace:
        bool = None
        int32 = None
        float64 = None

    array_api_strict = DummyArrayAPINamespace


@pytest.mark.parametrize(
    "args, expected",
    [
        ([bool], bool),
        ([bool, np.bytes_], np.object_),
        ([np.float32, np.float64], np.float64),
        ([np.float32, np.bytes_], np.object_),
        ([np.str_, np.int64], np.object_),
        ([np.str_, np.str_], np.str_),
        ([np.bytes_, np.str_], np.object_),
    ],
)
def test_result_type(args, expected) -> None:
    actual = dtypes.result_type(*args)
    assert actual == expected


def test_result_type_scalar() -> None:
    actual = dtypes.result_type(np.arange(3, dtype=np.float32), np.nan)
    assert actual == np.float32


def test_result_type_dask_array() -> None:
    # verify it works without evaluating dask arrays
    da = pytest.importorskip("dask.array")
    dask = pytest.importorskip("dask")

    def error():
        raise RuntimeError

    array = da.from_delayed(dask.delayed(error)(), (), np.float64)
    with pytest.raises(RuntimeError):
        array.compute()

    actual = dtypes.result_type(array)
    assert actual == np.float64

    # note that this differs from the behavior for scalar numpy arrays, which
    # would get promoted to float32
    actual = dtypes.result_type(array, np.array([0.5, 1.0], dtype=np.float32))
    assert actual == np.float64


@pytest.mark.parametrize("obj", [1.0, np.inf, "ab", 1.0 + 1.0j, True])
def test_inf(obj) -> None:
    assert dtypes.INF > obj
    assert dtypes.NINF < obj


@pytest.mark.parametrize(
    "kind, expected",
    [
        ("b", (np.float32, "nan")),  # dtype('int8')
        ("B", (np.float32, "nan")),  # dtype('uint8')
        ("c", (np.dtype("O"), "nan")),  # dtype('S1')
        ("D", (np.complex128, "(nan+nanj)")),  # dtype('complex128')
        ("d", (np.float64, "nan")),  # dtype('float64')
        ("e", (np.float16, "nan")),  # dtype('float16')
        ("F", (np.complex64, "(nan+nanj)")),  # dtype('complex64')
        ("f", (np.float32, "nan")),  # dtype('float32')
        ("h", (np.float32, "nan")),  # dtype('int16')
        ("H", (np.float32, "nan")),  # dtype('uint16')
        ("i", (np.float64, "nan")),  # dtype('int32')
        ("I", (np.float64, "nan")),  # dtype('uint32')
        ("l", (np.float64, "nan")),  # dtype('int64')
        ("L", (np.float64, "nan")),  # dtype('uint64')
        ("m", (np.timedelta64, "NaT")),  # dtype('<m8')
        ("M", (np.datetime64, "NaT")),  # dtype('<M8')
        ("O", (np.dtype("O"), "nan")),  # dtype('O')
        ("p", (np.float64, "nan")),  # dtype('int64')
        ("P", (np.float64, "nan")),  # dtype('uint64')
        ("q", (np.float64, "nan")),  # dtype('int64')
        ("Q", (np.float64, "nan")),  # dtype('uint64')
        ("S", (np.dtype("O"), "nan")),  # dtype('S')
        ("U", (np.dtype("O"), "nan")),  # dtype('<U')
        ("V", (np.dtype("O"), "nan")),  # dtype('V')
    ],
)
def test_maybe_promote(kind, expected) -> None:
    # 'g': np.float128 is not tested : not available on all platforms
    # 'G': np.complex256 is not tested : not available on all platforms

    actual = dtypes.maybe_promote(np.dtype(kind))
    assert actual[0] == expected[0]
    assert str(actual[1]) == expected[1]


def test_nat_types_membership() -> None:
    assert np.datetime64("NaT").dtype in dtypes.NAT_TYPES
    assert np.timedelta64("NaT").dtype in dtypes.NAT_TYPES
    assert np.float64 not in dtypes.NAT_TYPES


@pytest.mark.parametrize(
    ["dtype", "kinds", "xp", "expected"],
    (
        (np.dtype("int32"), "integral", np, True),
        (np.dtype("float16"), "real floating", np, True),
        (np.dtype("complex128"), "complex floating", np, True),
        (np.dtype("U"), "numeric", np, False),
        (np.dtype("int32"), "foo", np, ValueError("unknown dtype kinds:.+'foo'")),
        pytest.param(
            array_api_strict.int32,
            "integral",
            array_api_strict,
            True,
            marks=requires_array_api_strict,
            id="array_api-int",
        ),
        pytest.param(
            array_api_strict.float64,
            "real floating",
            array_api_strict,
            True,
            marks=requires_array_api_strict,
            id="array_api-float",
        ),
        pytest.param(
            array_api_strict.bool,
            "numeric",
            array_api_strict,
            False,
            marks=requires_array_api_strict,
            id="array_api-bool",
        ),
    ),
)
def test_isdtype(dtype, kinds, xp, expected) -> None:
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            dtypes.isdtype(dtype, kinds, xp=xp)

        return

    actual = dtypes.isdtype(dtype, kinds, xp=xp)
    assert actual == expected
