import operator
from distutils.version import LooseVersion

import numpy as np
import pytest

import xarray as xr
from xarray.core.npcompat import IS_NEP18_ACTIVE

pint = pytest.importorskip("pint")
pytestmark = [
    pytest.mark.skipif(
        not IS_NEP18_ACTIVE, reason="NUMPY_EXPERIMENTAL_ARRAY_FUNCTION is not enabled"
    ),
    # pytest.mark.filterwarnings("ignore:::pint[.*]"),
]


def use_pint_version_or_xfail(*, version, reason):
    return pytest.mark.xfail(LooseVersion(pint.__version__) < version, reason=reason)


DimensionalityError = pint.errors.DimensionalityError
unit_registry = pint.UnitRegistry()
require_pint_array_function = pytest.mark.xfail(
    not hasattr(unit_registry.Quantity, "__array_function__"),
    reason="pint does not implement __array_function__ yet",
)

try:
    from pint.quantity import BaseQuantity
except ImportError:
    BaseQuantity = unit_registry.Quantity


def array_extract_units(obj):
    raw = obj.data if hasattr(obj, "data") else obj
    try:
        return raw.units
    except AttributeError:
        return None


def array_strip_units(array):
    try:
        return array.magnitude
    except AttributeError:
        return array


def array_attach_units(data, unit, convert=False):
    if isinstance(data, BaseQuantity):
        if convert:
            return data.to(unit if unit != 1 else unit_registry.dimensionless)
        else:
            raise RuntimeError(
                "cannot attach unit {unit} to quantity with {data.units}".format(
                    unit=unit, data=data
                )
            )

    # to make sure we also encounter the case of "equal if converted"
    if (
        convert
        and isinstance(unit, unit_registry.Unit)
        and "[length]" in unit.dimensionality
    ):
        quantity = (data * unit_registry.m).to(unit)
    else:
        quantity = data * unit

    return quantity


def extract_units(obj):
    if isinstance(obj, xr.Dataset):
        vars_units = {
            name: array_extract_units(value) for name, value in obj.data_vars.items()
        }
        coords_units = {
            name: array_extract_units(value) for name, value in obj.coords.items()
        }

        units = {**vars_units, **coords_units}
    elif isinstance(obj, xr.DataArray):
        vars_units = {obj.name: array_extract_units(obj)}
        coords_units = {
            name: array_extract_units(value) for name, value in obj.coords.items()
        }

        units = {**vars_units, **coords_units}
    elif hasattr(obj, "units"):
        vars_units = {"<array>": array_extract_units(obj)}

        units = {**vars_units}
    else:
        units = {}

    return units


def strip_units(obj):
    if isinstance(obj, xr.Dataset):
        data_vars = {name: strip_units(value) for name, value in obj.data_vars.items()}
        coords = {name: strip_units(value) for name, value in obj.coords.items()}

        new_obj = xr.Dataset(data_vars=data_vars, coords=coords)
    elif isinstance(obj, xr.DataArray):
        data = array_strip_units(obj.data)
        coords = {
            name: (
                (value.dims, array_strip_units(value.data))
                if isinstance(value.data, BaseQuantity)
                else value  # to preserve multiindexes
            )
            for name, value in obj.coords.items()
        }

        new_obj = xr.DataArray(name=obj.name, data=data, coords=coords, dims=obj.dims)
    elif hasattr(obj, "magnitude"):
        new_obj = obj.magnitude
    else:
        new_obj = obj

    return new_obj


def attach_units(obj, units):
    if not isinstance(obj, (xr.DataArray, xr.Dataset)):
        return array_attach_units(obj, units.get("data", 1))

    if isinstance(obj, xr.Dataset):
        data_vars = {
            name: attach_units(value, units) for name, value in obj.data_vars.items()
        }

        coords = {
            name: attach_units(value, units) for name, value in obj.coords.items()
        }

        new_obj = xr.Dataset(data_vars=data_vars, coords=coords, attrs=obj.attrs)
    else:
        data_units = units.get(obj.name or "data", 1)

        data = array_attach_units(obj.data, data_units)

        coords = {
            name: (
                (value.dims, array_attach_units(value, units.get(name)))
                if name in units
                # to preserve multiindexes
                else value
            )
            for name, value in obj.coords.items()
        }
        dims = obj.dims
        attrs = obj.attrs

        new_obj = xr.DataArray(data=data, coords=coords, attrs=attrs, dims=dims)

    return new_obj


def assert_equal_with_units(a, b):
    # works like xr.testing.assert_equal, but also explicitly checks units
    # so, it is more like assert_identical
    __tracebackhide__ = True

    if isinstance(a, xr.Dataset) or isinstance(b, xr.Dataset):
        a_units = extract_units(a)
        b_units = extract_units(b)

        a_without_units = strip_units(a)
        b_without_units = strip_units(b)
        assert a_without_units.equals(b_without_units)
        assert a_units == b_units
    else:
        a = a if not isinstance(a, (xr.DataArray, xr.Variable)) else a.data
        b = b if not isinstance(b, (xr.DataArray, xr.Variable)) else b.data

        assert type(a) == type(b) or (
            isinstance(a, BaseQuantity) and isinstance(b, BaseQuantity)
        )

        # workaround until pint implements allclose in __array_function__
        if isinstance(a, BaseQuantity) or isinstance(b, BaseQuantity):
            assert (
                hasattr(a, "magnitude") and hasattr(b, "magnitude")
            ) and np.allclose(a.magnitude, b.magnitude, equal_nan=True)
            assert (hasattr(a, "units") and hasattr(b, "units")) and a.units == b.units
        else:
            assert np.allclose(a, b, equal_nan=True)


@pytest.fixture(params=[float, int])
def dtype(request):
    return request.param


class method:
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __call__(self, obj, *args, **kwargs):
        from collections.abc import Callable
        from functools import partial

        all_args = list(self.args) + list(args)
        all_kwargs = {**self.kwargs, **kwargs}

        func = getattr(obj, self.name, None)
        if func is None or not isinstance(func, Callable):
            # fall back to module level numpy functions if not a xarray object
            if not isinstance(obj, (xr.Variable, xr.DataArray, xr.Dataset)):
                numpy_func = getattr(np, self.name)
                func = partial(numpy_func, obj)
                # remove typical xr args like "dim"
                exclude_kwargs = ("dim", "dims")
                all_kwargs = {
                    key: value
                    for key, value in all_kwargs.items()
                    if key not in exclude_kwargs
                }
            else:
                raise AttributeError(
                    "{obj} has no method named '{self.name}'".format(obj=obj, self=self)
                )

        return func(*all_args, **all_kwargs)

    def __repr__(self):
        return "method {self.name}".format(self=self)


class function:
    def __init__(self, name):
        self.name = name
        self.func = getattr(np, name)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return "function {self.name}".format(self=self)


@require_pint_array_function
@pytest.mark.parametrize("func", (xr.zeros_like, xr.ones_like))
def test_replication(func, dtype):
    array = np.linspace(0, 10, 20).astype(dtype) * unit_registry.s
    data_array = xr.DataArray(data=array, dims="x")

    numpy_func = getattr(np, func.__name__)
    expected = numpy_func(array)
    result = func(data_array)

    assert_equal_with_units(expected, result)


@pytest.mark.xfail(
    reason="np.full_like on Variable strips the unit and pint does not allow mixed args"
)
@require_pint_array_function
@pytest.mark.parametrize(
    "unit,error",
    (
        pytest.param(1, DimensionalityError, id="no_unit"),
        pytest.param(
            unit_registry.dimensionless, DimensionalityError, id="dimensionless"
        ),
        pytest.param(unit_registry.m, DimensionalityError, id="incompatible_unit"),
        pytest.param(unit_registry.ms, None, id="compatible_unit"),
        pytest.param(unit_registry.s, None, id="identical_unit"),
    ),
)
def test_replication_full_like(unit, error, dtype):
    array = np.linspace(0, 5, 10) * unit_registry.s
    data_array = xr.DataArray(data=array, dims="x")

    fill_value = -1 * unit
    if error is not None:
        with pytest.raises(error):
            xr.full_like(data_array, fill_value=fill_value)
    else:
        result = xr.full_like(data_array, fill_value=fill_value)
        expected = np.full_like(array, fill_value=fill_value)

        assert_equal_with_units(expected, result)


class TestDataArray:
    @require_pint_array_function
    @pytest.mark.filterwarnings("error:::pint[.*]")
    @pytest.mark.parametrize(
        "coords",
        (
            pytest.param(True, id="with coords"),
            pytest.param(False, id="without coords"),
        ),
    )
    def test_init(self, coords):
        array = np.linspace(1, 2, 10) * unit_registry.m
        parameters = {"data": array}
        if coords:
            x = np.arange(len(array)) * unit_registry.s
            y = x.to(unit_registry.ms)
            parameters["coords"] = {"x": x, "y": ("x", y)}
            parameters["dims"] = ["x"]

        data_array = xr.DataArray(**parameters)
        assert_equal_with_units(array, data_array)

    @require_pint_array_function
    @pytest.mark.filterwarnings("error:::pint[.*]")
    @pytest.mark.parametrize(
        "func", (pytest.param(str, id="str"), pytest.param(repr, id="repr"))
    )
    @pytest.mark.parametrize(
        "coords",
        (
            pytest.param(
                True,
                id="coords",
                marks=pytest.mark.xfail(
                    reason="formatting currently does not delegate for coordinates"
                ),
            ),
            pytest.param(False, id="no coords"),
        ),
    )
    def test_repr(self, func, coords):
        array = np.linspace(1, 2, 10) * unit_registry.m
        x = np.arange(len(array)) * unit_registry.s

        if coords:
            data_array = xr.DataArray(data=array, coords={"x": x}, dims=["x"])
            print(data_array.x._variable._data)
        else:
            data_array = xr.DataArray(data=array)

        # FIXME: this just checks that the repr does not raise
        # warnings or errors, but does not check the result
        func(data_array)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (
            pytest.param(
                function("all"),
                marks=pytest.mark.xfail(reason="not implemented by pint yet"),
            ),
            pytest.param(
                function("any"),
                marks=pytest.mark.xfail(reason="not implemented by pint yet"),
            ),
            pytest.param(
                function("argmax"),
                marks=pytest.mark.xfail(
                    reason="comparison of quantity with ndarrays in nanops not implemented"
                ),
            ),
            pytest.param(
                function("argmin"),
                marks=pytest.mark.xfail(
                    reason="comparison of quantity with ndarrays in nanops not implemented"
                ),
            ),
            function("max"),
            function("mean"),
            pytest.param(
                function("median"),
                marks=pytest.mark.xfail(
                    reason="np.median on DataArray strips the units"
                ),
            ),
            function("min"),
            pytest.param(
                function("prod"),
                marks=pytest.mark.xfail(reason="not implemented by pint yet"),
            ),
            pytest.param(
                function("sum"),
                marks=pytest.mark.xfail(
                    reason="comparison of quantity with ndarrays in nanops not implemented"
                ),
            ),
            function("std"),
            function("var"),
            function("cumsum"),
            pytest.param(
                function("cumprod"),
                marks=pytest.mark.xfail(reason="not implemented by pint yet"),
            ),
            pytest.param(
                method("all"),
                marks=pytest.mark.xfail(reason="not implemented by pint yet"),
            ),
            pytest.param(
                method("any"),
                marks=pytest.mark.xfail(reason="not implemented by pint yet"),
            ),
            pytest.param(
                method("argmax"),
                marks=pytest.mark.xfail(
                    reason="comparison of quantities with ndarrays in nanops not implemented"
                ),
            ),
            pytest.param(
                method("argmin"),
                marks=pytest.mark.xfail(
                    reason="comparison of quantities with ndarrays in nanops not implemented"
                ),
            ),
            method("max"),
            method("mean"),
            method("median"),
            method("min"),
            pytest.param(
                method("prod"),
                marks=pytest.mark.xfail(
                    reason="comparison of quantity with ndarrays in nanops not implemented"
                ),
            ),
            pytest.param(
                method("sum"),
                marks=pytest.mark.xfail(
                    reason="comparison of quantity with ndarrays in nanops not implemented"
                ),
            ),
            method("std"),
            method("var"),
            method("cumsum"),
            pytest.param(
                method("cumprod"),
                marks=pytest.mark.xfail(reason="pint does not implement cumprod yet"),
            ),
        ),
        ids=repr,
    )
    def test_aggregation(self, func, dtype):
        array = np.arange(10).astype(dtype) * unit_registry.m
        data_array = xr.DataArray(data=array)

        expected = func(array)
        result = func(data_array)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (
            pytest.param(operator.neg, id="negate"),
            pytest.param(abs, id="absolute"),
            pytest.param(
                np.round,
                id="round",
                marks=pytest.mark.xfail(reason="pint does not implement round"),
            ),
        ),
    )
    def test_unary_operations(self, func, dtype):
        array = np.arange(10).astype(dtype) * unit_registry.m
        data_array = xr.DataArray(data=array)

        expected = xr.DataArray(data=func(array))
        result = func(data_array)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (
            pytest.param(lambda x: 2 * x, id="multiply"),
            pytest.param(lambda x: x + x, id="add"),
            pytest.param(lambda x: x[0] + x, id="add scalar"),
            pytest.param(
                lambda x: x.T @ x,
                id="matrix multiply",
                marks=pytest.mark.xfail(
                    reason="pint does not support matrix multiplication yet"
                ),
            ),
        ),
    )
    def test_binary_operations(self, func, dtype):
        array = np.arange(10).astype(dtype) * unit_registry.m
        data_array = xr.DataArray(data=array)

        expected = xr.DataArray(data=func(array))
        result = func(data_array)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "comparison",
        (
            pytest.param(operator.lt, id="less_than"),
            pytest.param(operator.ge, id="greater_equal"),
            pytest.param(operator.eq, id="equal"),
        ),
    )
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, ValueError, id="without_unit"),
            pytest.param(
                unit_registry.dimensionless, DimensionalityError, id="dimensionless"
            ),
            pytest.param(unit_registry.s, DimensionalityError, id="incorrect_unit"),
            pytest.param(unit_registry.m, None, id="correct_unit"),
        ),
    )
    def test_comparison_operations(self, comparison, unit, error, dtype):
        array = (
            np.array([10.1, 5.2, 6.5, 8.0, 21.3, 7.1, 1.3]).astype(dtype)
            * unit_registry.m
        )
        data_array = xr.DataArray(data=array)

        value = 8
        to_compare_with = value * unit

        # incompatible units are all not equal
        if error is not None and comparison is not operator.eq:
            with pytest.raises(error):
                comparison(array, to_compare_with)

            with pytest.raises(error):
                comparison(data_array, to_compare_with)
        else:
            result = comparison(data_array, to_compare_with)
            # pint compares incompatible arrays to False, so we need to extend
            # the multiplication works for both scalar and array results
            expected = comparison(array, to_compare_with) * np.ones_like(
                array, dtype=bool
            )

            assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "units,error",
        (
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(
                unit_registry.m, pint.errors.DimensionalityError, id="incorrect unit"
            ),
            pytest.param(unit_registry.degree, None, id="correct unit"),
        ),
    )
    def test_univariate_ufunc(self, units, error, dtype):
        array = np.arange(10).astype(dtype) * units
        data_array = xr.DataArray(data=array)

        if error is not None:
            with pytest.raises(error):
                np.sin(data_array)
        else:
            expected = xr.DataArray(data=np.sin(array))
            result = np.sin(data_array)

            assert_equal_with_units(expected, result)

    @pytest.mark.xfail(reason="pint's implementation of `np.maximum` strips units")
    @require_pint_array_function
    def test_bivariate_ufunc(self, dtype):
        unit = unit_registry.m
        array = np.arange(10).astype(dtype) * unit
        data_array = xr.DataArray(data=array)

        expected = xr.DataArray(np.maximum(array, 0 * unit))

        assert_equal_with_units(expected, np.maximum(data_array, 0 * unit))
        assert_equal_with_units(expected, np.maximum(0 * unit, data_array))

    @require_pint_array_function
    @pytest.mark.parametrize("property", ("T", "imag", "real"))
    def test_numpy_properties(self, property, dtype):
        array = (
            np.arange(5 * 10).astype(dtype)
            + 1j * np.linspace(-1, 0, 5 * 10).astype(dtype)
        ).reshape(5, 10) * unit_registry.s
        data_array = xr.DataArray(data=array, dims=("x", "y"))

        expected = xr.DataArray(
            data=getattr(array, property),
            dims=("x", "y")[:: 1 if property != "T" else -1],
        )
        result = getattr(data_array, property)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (
            method("conj"),
            method("argsort"),
            method("conjugate"),
            method("round"),
            pytest.param(
                method("rank", dim="x"),
                marks=pytest.mark.xfail(reason="pint does not implement rank yet"),
            ),
        ),
        ids=repr,
    )
    def test_numpy_methods(self, func, dtype):
        array = np.arange(10).astype(dtype) * unit_registry.m
        data_array = xr.DataArray(data=array, dims="x")

        expected = xr.DataArray(func(array), dims="x")
        result = func(data_array)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func", (method("clip", min=3, max=8), method("searchsorted", v=5)), ids=repr
    )
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, DimensionalityError, id="no_unit"),
            pytest.param(
                unit_registry.dimensionless, DimensionalityError, id="dimensionless"
            ),
            pytest.param(unit_registry.s, DimensionalityError, id="incompatible_unit"),
            pytest.param(unit_registry.cm, None, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="identical_unit"),
        ),
    )
    def test_numpy_methods_with_args(self, func, unit, error, dtype):
        array = np.arange(10).astype(dtype) * unit_registry.m
        data_array = xr.DataArray(data=array, dims="x")

        scalar_types = (int, float)
        kwargs = {
            key: (value * unit if isinstance(value, scalar_types) else value)
            for key, value in func.kwargs.items()
        }

        if error is not None:
            with pytest.raises(error):
                func(data_array, **kwargs)
        else:
            expected = func(array, **kwargs)
            result = func(data_array, **kwargs)

            assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func", (method("isnull"), method("notnull"), method("count")), ids=repr
    )
    def test_missing_value_detection(self, func, dtype):
        array = (
            np.array(
                [
                    [1.4, 2.3, np.nan, 7.2],
                    [np.nan, 9.7, np.nan, np.nan],
                    [2.1, np.nan, np.nan, 4.6],
                    [9.9, np.nan, 7.2, 9.1],
                ]
            )
            * unit_registry.degK
        )
        x = np.arange(array.shape[0]) * unit_registry.m
        y = np.arange(array.shape[1]) * unit_registry.m

        data_array = xr.DataArray(data=array, coords={"x": x, "y": y}, dims=("x", "y"))

        expected = func(strip_units(data_array))
        result = func(data_array)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.xfail(reason="ffill and bfill lose units in data")
    @pytest.mark.parametrize("func", (method("ffill"), method("bfill")), ids=repr)
    def test_missing_value_filling(self, func, dtype):
        array = (
            np.array([1.4, np.nan, 2.3, np.nan, np.nan, 9.1]).astype(dtype)
            * unit_registry.degK
        )
        x = np.arange(len(array))
        data_array = xr.DataArray(data=array, coords={"x": x}, dims=["x"])

        result_without_units = func(strip_units(data_array), dim="x")
        result = xr.DataArray(
            data=result_without_units.data * unit_registry.degK,
            coords={"x": x},
            dims=["x"],
        )

        expected = attach_units(
            func(strip_units(data_array), dim="x"), {"data": unit_registry.degK}
        )
        result = func(data_array, dim="x")

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.xfail(reason="fillna drops the unit")
    @pytest.mark.parametrize(
        "fill_value",
        (
            pytest.param(
                -1,
                id="python scalar",
                marks=pytest.mark.xfail(
                    reason="python scalar cannot be converted using astype()"
                ),
            ),
            pytest.param(np.array(-1), id="numpy scalar"),
            pytest.param(np.array([-1]), id="numpy array"),
        ),
    )
    def test_fillna(self, fill_value, dtype):
        unit = unit_registry.m
        array = np.array([1.4, np.nan, 2.3, np.nan, np.nan, 9.1]).astype(dtype) * unit
        data_array = xr.DataArray(data=array)

        expected = attach_units(
            strip_units(data_array).fillna(value=fill_value), {"data": unit}
        )
        result = data_array.fillna(value=fill_value * unit)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    def test_dropna(self, dtype):
        array = (
            np.array([1.4, np.nan, 2.3, np.nan, np.nan, 9.1]).astype(dtype)
            * unit_registry.m
        )
        x = np.arange(len(array))
        data_array = xr.DataArray(data=array, coords={"x": x}, dims=["x"])

        expected = attach_units(
            strip_units(data_array).dropna(dim="x"), {"data": unit_registry.m}
        )
        result = data_array.dropna(dim="x")

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.xfail(reason="pint does not implement `numpy.isin`")
    @pytest.mark.parametrize(
        "unit",
        (
            pytest.param(1, id="no_unit"),
            pytest.param(unit_registry.dimensionless, id="dimensionless"),
            pytest.param(unit_registry.s, id="incompatible_unit"),
            pytest.param(unit_registry.cm, id="compatible_unit"),
            pytest.param(unit_registry.m, id="same_unit"),
        ),
    )
    def test_isin(self, unit, dtype):
        array = (
            np.array([1.4, np.nan, 2.3, np.nan, np.nan, 9.1]).astype(dtype)
            * unit_registry.m
        )
        data_array = xr.DataArray(data=array, dims="x")

        raw_values = np.array([1.4, np.nan, 2.3]).astype(dtype)
        values = raw_values * unit

        result_without_units = strip_units(data_array).isin(raw_values)
        if unit != unit_registry.m:
            result_without_units[:] = False
        result_with_units = data_array.isin(values)

        assert_equal_with_units(result_without_units, result_with_units)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "variant",
        (
            pytest.param(
                "masking",
                marks=pytest.mark.xfail(reason="nan not compatible with quantity"),
            ),
            pytest.param(
                "replacing_scalar",
                marks=pytest.mark.xfail(reason="scalar not convertible using astype"),
            ),
            pytest.param(
                "replacing_array",
                marks=pytest.mark.xfail(
                    reason="replacing using an array drops the units"
                ),
            ),
            pytest.param(
                "dropping",
                marks=pytest.mark.xfail(reason="nan not compatible with quantity"),
            ),
        ),
    )
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, DimensionalityError, id="no_unit"),
            pytest.param(
                unit_registry.dimensionless, DimensionalityError, id="dimensionless"
            ),
            pytest.param(unit_registry.s, DimensionalityError, id="incompatible_unit"),
            pytest.param(unit_registry.cm, None, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="same_unit"),
        ),
    )
    def test_where(self, variant, unit, error, dtype):
        def _strip_units(mapping):
            return {key: array_strip_units(value) for key, value in mapping.items()}

        original_unit = unit_registry.m
        array = np.linspace(0, 1, 10).astype(dtype) * original_unit

        data_array = xr.DataArray(data=array)

        condition = data_array < 0.5 * original_unit
        other = np.linspace(-2, -1, 10).astype(dtype) * unit
        variant_kwargs = {
            "masking": {"cond": condition},
            "replacing_scalar": {"cond": condition, "other": -1 * unit},
            "replacing_array": {"cond": condition, "other": other},
            "dropping": {"cond": condition, "drop": True},
        }
        kwargs = variant_kwargs.get(variant)
        kwargs_without_units = _strip_units(kwargs)

        if variant not in ("masking", "dropping") and error is not None:
            with pytest.raises(error):
                data_array.where(**kwargs)
        else:
            expected = attach_units(
                strip_units(array).where(**kwargs_without_units),
                {"data": original_unit},
            )
            result = data_array.where(**kwargs)

            assert_equal_with_units(expected, result)

    @pytest.mark.xfail(reason="interpolate strips units")
    @require_pint_array_function
    def test_interpolate_na(self, dtype):
        array = (
            np.array([-1.03, 0.1, 1.4, np.nan, 2.3, np.nan, np.nan, 9.1])
            * unit_registry.m
        )
        x = np.arange(len(array))
        data_array = xr.DataArray(data=array, coords={"x": x}, dims="x").astype(dtype)

        expected = attach_units(
            strip_units(data_array).interpolate_na(dim="x"), {"data": unit_registry.m}
        )
        result = data_array.interpolate_na(dim="x")

        assert_equal_with_units(expected, result)

    @pytest.mark.xfail(reason="uses DataArray.where, which currently fails")
    @require_pint_array_function
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, DimensionalityError, id="no_unit"),
            pytest.param(
                unit_registry.dimensionless, DimensionalityError, id="dimensionless"
            ),
            pytest.param(unit_registry.s, DimensionalityError, id="incompatible_unit"),
            pytest.param(unit_registry.cm, None, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="identical_unit"),
        ),
    )
    def test_combine_first(self, unit, error, dtype):
        array = np.zeros(shape=(2, 2), dtype=dtype) * unit_registry.m
        other_array = np.ones_like(array) * unit

        data_array = xr.DataArray(
            data=array, coords={"x": ["a", "b"], "y": [-1, 0]}, dims=["x", "y"]
        )
        other = xr.DataArray(
            data=other_array, coords={"x": ["b", "c"], "y": [0, 1]}, dims=["x", "y"]
        )

        if error is not None:
            with pytest.raises(error):
                data_array.combine_first(other)
        else:
            expected = attach_units(
                strip_units(data_array).combine_first(strip_units(other)),
                {"data": unit_registry.m},
            )
            result = data_array.combine_first(other)

            assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "unit",
        (
            pytest.param(1, id="no_unit"),
            pytest.param(unit_registry.dimensionless, id="dimensionless"),
            pytest.param(unit_registry.s, id="incompatible_unit"),
            pytest.param(unit_registry.cm, id="compatible_unit"),
            pytest.param(unit_registry.m, id="identical_unit"),
        ),
    )
    @pytest.mark.parametrize(
        "variation",
        (
            "data",
            pytest.param(
                "dims", marks=pytest.mark.xfail(reason="units in indexes not supported")
            ),
            "coords",
        ),
    )
    @pytest.mark.parametrize(
        "func",
        (
            method("equals"),
            pytest.param(
                method("identical"),
                marks=pytest.mark.xfail(reason="identical does not check units yet"),
            ),
        ),
        ids=repr,
    )
    def test_comparisons(self, func, variation, unit, dtype):
        data = np.linspace(0, 5, 10).astype(dtype)
        coord = np.arange(len(data)).astype(dtype)

        quantity = data * unit_registry.m
        x = coord * unit_registry.m
        y = coord * unit_registry.m

        units = {
            "data": (unit, unit_registry.m, unit_registry.m),
            "dims": (unit_registry.m, unit, unit_registry.m),
            "coords": (unit_registry.m, unit_registry.m, unit),
        }
        data_unit, dim_unit, coord_unit = units.get(variation)

        data_array = xr.DataArray(
            data=quantity, coords={"x": x, "y": ("x", y)}, dims="x"
        )
        other = xr.DataArray(
            data=array_attach_units(data, data_unit, convert=True),
            coords={
                "x": array_attach_units(coord, dim_unit, convert=True),
                "y": ("x", array_attach_units(coord, coord_unit, convert=True)),
            },
            dims="x",
        )

        # TODO: test dim coord once indexes leave units intact
        # also, express this in terms of calls on the raw data array
        # and then check the units
        equal_arrays = (
            np.all(quantity == other.data)
            and (np.all(x == other.x.data) or True)  # dims can't be checked yet
            and np.all(y == other.y.data)
        )
        equal_units = (
            data_unit == unit_registry.m
            and coord_unit == unit_registry.m
            and dim_unit == unit_registry.m
        )
        expected = equal_arrays and (func.name != "identical" or equal_units)
        result = func(data_array, other)

        assert expected == result

    @require_pint_array_function
    @pytest.mark.parametrize(
        "unit",
        (
            pytest.param(1, id="no_unit"),
            pytest.param(unit_registry.dimensionless, id="dimensionless"),
            pytest.param(unit_registry.s, id="incompatible_unit"),
            pytest.param(unit_registry.cm, id="compatible_unit"),
            pytest.param(unit_registry.m, id="identical_unit"),
        ),
    )
    def test_broadcast_equals(self, unit, dtype):
        left_array = np.ones(shape=(2, 2), dtype=dtype) * unit_registry.m
        right_array = array_attach_units(
            np.ones(shape=(2,), dtype=dtype), unit, convert=True
        )

        left = xr.DataArray(data=left_array, dims=("x", "y"))
        right = xr.DataArray(data=right_array, dims="x")

        expected = np.all(left_array == right_array[:, None])
        result = left.broadcast_equals(right)

        assert expected == result

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (
            method("pipe", lambda da: da * 10),
            method("assign_coords", y2=("y", np.arange(10) * unit_registry.mm)),
            method("assign_attrs", attr1="value"),
            method("rename", x2="x_mm"),
            method("swap_dims", {"x": "x2"}),
            method(
                "expand_dims",
                dim={"z": np.linspace(10, 20, 12) * unit_registry.s},
                axis=1,
            ),
            method("drop", labels="x"),
            method("reset_coords", names="x2"),
            method("copy"),
            pytest.param(
                method("astype", np.float32),
                marks=pytest.mark.xfail(reason="units get stripped"),
            ),
            pytest.param(
                method("item", 1), marks=pytest.mark.xfail(reason="units get stripped")
            ),
        ),
        ids=repr,
    )
    def test_content_manipulation(self, func, dtype):
        quantity = (
            np.linspace(0, 10, 5 * 10).reshape(5, 10).astype(dtype)
            * unit_registry.pascal
        )
        x = np.arange(quantity.shape[0]) * unit_registry.m
        y = np.arange(quantity.shape[1]) * unit_registry.m
        x2 = x.to(unit_registry.mm)

        data_array = xr.DataArray(
            name="data",
            data=quantity,
            coords={"x": x, "x2": ("x", x2), "y": y},
            dims=("x", "y"),
        )

        stripped_kwargs = {
            key: array_strip_units(value) for key, value in func.kwargs.items()
        }
        expected = attach_units(
            func(strip_units(data_array), **stripped_kwargs),
            {"data": quantity.units, "x": x.units, "x2": x2.units, "y": y.units},
        )
        result = func(data_array)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (
            pytest.param(
                method("drop", labels=np.array([1, 5]), dim="x"),
                marks=pytest.mark.xfail(
                    reason="selecting using incompatible units does not raise"
                ),
            ),
            pytest.param(method("copy", data=np.arange(20))),
        ),
        ids=repr,
    )
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, DimensionalityError, id="no_unit"),
            pytest.param(
                unit_registry.dimensionless, DimensionalityError, id="dimensionless"
            ),
            pytest.param(unit_registry.s, DimensionalityError, id="incompatible_unit"),
            pytest.param(unit_registry.cm, KeyError, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="identical_unit"),
        ),
    )
    def test_content_manipulation_with_units(self, func, unit, error, dtype):
        quantity = np.linspace(0, 10, 20, dtype=dtype) * unit_registry.pascal
        x = np.arange(len(quantity)) * unit_registry.m

        data_array = xr.DataArray(name="data", data=quantity, coords={"x": x}, dims="x")

        kwargs = {
            key: (value * unit if isinstance(value, np.ndarray) else value)
            for key, value in func.kwargs.items()
        }
        stripped_kwargs = func.kwargs

        expected = attach_units(
            func(strip_units(data_array), **stripped_kwargs),
            {"data": quantity.units if func.name == "drop" else unit, "x": x.units},
        )
        if error is not None and func.name == "drop":
            with pytest.raises(error):
                func(data_array, **kwargs)
        else:
            result = func(data_array, **kwargs)
            assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "indices",
        (
            pytest.param(4, id="single index"),
            pytest.param([5, 2, 9, 1], id="multiple indices"),
        ),
    )
    def test_isel(self, indices, dtype):
        array = np.arange(10).astype(dtype) * unit_registry.s
        x = np.arange(len(array)) * unit_registry.m

        data_array = xr.DataArray(data=array, coords={"x": x}, dims=["x"])

        expected = attach_units(
            strip_units(data_array).isel(x=indices),
            {"data": unit_registry.s, "x": unit_registry.m},
        )
        result = data_array.isel(x=indices)

        assert_equal_with_units(expected, result)

    @pytest.mark.xfail(
        reason="xarray does not support duck arrays in dimension coordinates"
    )
    @require_pint_array_function
    @pytest.mark.parametrize(
        "values",
        (
            pytest.param(12, id="single value"),
            pytest.param([10, 5, 13], id="list of multiple values"),
            pytest.param(np.array([9, 3, 7, 12]), id="array of multiple values"),
        ),
    )
    @pytest.mark.parametrize(
        "units,error",
        (
            pytest.param(1, KeyError, id="no units"),
            pytest.param(unit_registry.dimensionless, KeyError, id="dimensionless"),
            pytest.param(unit_registry.degree, KeyError, id="incorrect unit"),
            pytest.param(unit_registry.s, None, id="correct unit"),
        ),
    )
    def test_sel(self, values, units, error, dtype):
        array = np.linspace(5, 10, 20).astype(dtype) * unit_registry.m
        x = np.arange(len(array)) * unit_registry.s
        data_array = xr.DataArray(data=array, coords={"x": x}, dims=["x"])

        values_with_units = values * units

        if error is not None:
            with pytest.raises(error):
                data_array.sel(x=values_with_units)
        else:
            result_array = array[values]
            result_data_array = data_array.sel(x=values_with_units)
            assert_equal_with_units(result_array, result_data_array)

    @pytest.mark.xfail(
        reason="xarray does not support duck arrays in dimension coordinates"
    )
    @require_pint_array_function
    @pytest.mark.parametrize(
        "values",
        (
            pytest.param(12, id="single value"),
            pytest.param([10, 5, 13], id="list of multiple values"),
            pytest.param(np.array([9, 3, 7, 12]), id="array of multiple values"),
        ),
    )
    @pytest.mark.parametrize(
        "units,error",
        (
            pytest.param(1, KeyError, id="no units"),
            pytest.param(unit_registry.dimensionless, KeyError, id="dimensionless"),
            pytest.param(unit_registry.degree, KeyError, id="incorrect unit"),
            pytest.param(unit_registry.s, None, id="correct unit"),
        ),
    )
    def test_loc(self, values, units, error, dtype):
        array = np.linspace(5, 10, 20).astype(dtype) * unit_registry.m
        x = np.arange(len(array)) * unit_registry.s
        data_array = xr.DataArray(data=array, coords={"x": x}, dims=["x"])

        values_with_units = values * units

        if error is not None:
            with pytest.raises(error):
                data_array.loc[values_with_units]
        else:
            result_array = array[values]
            result_data_array = data_array.loc[values_with_units]
            assert_equal_with_units(result_array, result_data_array)

    @require_pint_array_function
    @pytest.mark.xfail(reason="tries to coerce using asarray")
    @pytest.mark.parametrize(
        "shape",
        (
            pytest.param((10, 20), id="nothing squeezable"),
            pytest.param((10, 20, 1), id="last dimension squeezable"),
            pytest.param((10, 1, 20), id="middle dimension squeezable"),
            pytest.param((1, 10, 20), id="first dimension squeezable"),
            pytest.param((1, 10, 1, 20), id="first and last dimension squeezable"),
        ),
    )
    def test_squeeze(self, shape, dtype):
        names = "xyzt"
        coords = {
            name: np.arange(length).astype(dtype)
            * (unit_registry.m if name != "t" else unit_registry.s)
            for name, length in zip(names, shape)
        }
        array = np.arange(10 * 20).astype(dtype).reshape(shape) * unit_registry.J
        data_array = xr.DataArray(
            data=array, coords=coords, dims=tuple(names[: len(shape)])
        )

        result_array = array.squeeze()
        result_data_array = data_array.squeeze()
        assert_equal_with_units(result_array, result_data_array)

        # try squeezing the dimensions separately
        names = tuple(dim for dim, coord in coords.items() if len(coord) == 1)
        for index, name in enumerate(names):
            assert_equal_with_units(
                np.squeeze(array, axis=index), data_array.squeeze(dim=name)
            )

    @require_pint_array_function
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, None, id="no_unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="incompatible_unit"),
            pytest.param(unit_registry.cm, None, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="identical_unit"),
        ),
    )
    def test_interp(self, unit, error):
        array = np.linspace(1, 2, 10 * 5).reshape(10, 5) * unit_registry.degK
        new_coords = (np.arange(10) + 0.5) * unit
        coords = {
            "x": np.arange(10) * unit_registry.m,
            "y": np.arange(5) * unit_registry.m,
        }

        data_array = xr.DataArray(array, coords=coords, dims=("x", "y"))

        if error is not None:
            with pytest.raises(error):
                data_array.interp(x=new_coords)
        else:
            new_coords_ = (
                new_coords.magnitude if hasattr(new_coords, "magnitude") else new_coords
            )
            result_array = strip_units(data_array).interp(
                x=new_coords_ * unit_registry.degK
            )
            result_data_array = data_array.interp(x=new_coords)

            assert_equal_with_units(result_array, result_data_array)

    @require_pint_array_function
    @pytest.mark.xfail(reason="tries to coerce using asarray")
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, None, id="no_unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="incompatible_unit"),
            pytest.param(unit_registry.cm, None, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="identical_unit"),
        ),
    )
    def test_interp_like(self, unit, error):
        array = np.linspace(1, 2, 10 * 5).reshape(10, 5) * unit_registry.degK
        coords = {
            "x": (np.arange(10) + 0.3) * unit_registry.m,
            "y": (np.arange(5) + 0.3) * unit_registry.m,
        }

        data_array = xr.DataArray(array, coords=coords, dims=("x", "y"))
        new_data_array = xr.DataArray(
            data=np.empty((20, 10)),
            coords={"x": np.arange(20) * unit, "y": np.arange(10) * unit},
            dims=("x", "y"),
        )

        if error is not None:
            with pytest.raises(error):
                data_array.interp_like(new_data_array)
        else:
            result_array = (
                xr.DataArray(
                    data=array.magnitude,
                    coords={name: value.magnitude for name, value in coords.items()},
                    dims=("x", "y"),
                ).interp_like(strip_units(new_data_array))
                * unit_registry.degK
            )
            result_data_array = data_array.interp_like(new_data_array)

            assert_equal_with_units(result_array, result_data_array)

    @require_pint_array_function
    @pytest.mark.xfail(
        reason="pint does not implement np.result_type in __array_function__ yet"
    )
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, None, id="no_unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="incompatible_unit"),
            pytest.param(unit_registry.cm, None, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="identical_unit"),
        ),
    )
    def test_reindex(self, unit, error):
        array = np.linspace(1, 2, 10 * 5).reshape(10, 5) * unit_registry.degK
        new_coords = (np.arange(10) + 0.5) * unit
        coords = {
            "x": np.arange(10) * unit_registry.m,
            "y": np.arange(5) * unit_registry.m,
        }

        data_array = xr.DataArray(array, coords=coords, dims=("x", "y"))

        if error is not None:
            with pytest.raises(error):
                data_array.interp(x=new_coords)
        else:
            result_array = strip_units(data_array).reindex(
                x=(
                    new_coords.magnitude
                    if hasattr(new_coords, "magnitude")
                    else new_coords
                )
                * unit_registry.degK
            )
            result_data_array = data_array.reindex(x=new_coords)

            assert_equal_with_units(result_array, result_data_array)

    @require_pint_array_function
    @pytest.mark.xfail(
        reason="pint does not implement np.result_type in __array_function__ yet"
    )
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, None, id="no_unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="incompatible_unit"),
            pytest.param(unit_registry.cm, None, id="compatible_unit"),
            pytest.param(unit_registry.m, None, id="identical_unit"),
        ),
    )
    def test_reindex_like(self, unit, error):
        array = np.linspace(1, 2, 10 * 5).reshape(10, 5) * unit_registry.degK
        coords = {
            "x": (np.arange(10) + 0.3) * unit_registry.m,
            "y": (np.arange(5) + 0.3) * unit_registry.m,
        }

        data_array = xr.DataArray(array, coords=coords, dims=("x", "y"))
        new_data_array = xr.DataArray(
            data=np.empty((20, 10)),
            coords={"x": np.arange(20) * unit, "y": np.arange(10) * unit},
            dims=("x", "y"),
        )

        if error is not None:
            with pytest.raises(error):
                data_array.reindex_like(new_data_array)
        else:
            expected = attach_units(
                strip_units(data_array).reindex_like(strip_units(new_data_array)),
                {
                    "data": unit_registry.degK,
                    "x": unit_registry.m,
                    "y": unit_registry.m,
                },
            )
            result = data_array.reindex_like(new_data_array)

            assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (method("unstack"), method("reset_index", "z"), method("reorder_levels")),
        ids=repr,
    )
    def test_stacking_stacked(self, func, dtype):
        array = (
            np.linspace(0, 10, 5 * 10).reshape(5, 10).astype(dtype) * unit_registry.m
        )
        x = np.arange(array.shape[0])
        y = np.arange(array.shape[1])

        data_array = xr.DataArray(
            name="data", data=array, coords={"x": x, "y": y}, dims=("x", "y")
        )
        stacked = data_array.stack(z=("x", "y"))

        expected = attach_units(func(strip_units(stacked)), {"data": unit_registry.m})
        result = func(stacked)

        assert_equal_with_units(expected, result)

    @require_pint_array_function
    @pytest.mark.parametrize(
        "func",
        (
            method("transpose", "y", "x", "z"),
            method("stack", a=("x", "y")),
            method("set_index", x="x2"),
            pytest.param(
                method("shift", x=2), marks=pytest.mark.xfail(reason="strips units")
            ),
            pytest.param(
                method("roll", x=2), marks=pytest.mark.xfail(reason="strips units")
            ),
            method("sortby", "x2"),
        ),
        ids=repr,
    )
    def test_stacking_reordering(self, func, dtype):
        array = (
            np.linspace(0, 10, 2 * 5 * 10).reshape(2, 5, 10).astype(dtype)
            * unit_registry.m
        )
        x = np.arange(array.shape[0])
        y = np.arange(array.shape[1])
        z = np.arange(array.shape[2])
        x2 = np.linspace(0, 1, array.shape[0])[::-1]

        data_array = xr.DataArray(
            name="data",
            data=array,
            coords={"x": x, "y": y, "z": z, "x2": ("x", x2)},
            dims=("x", "y", "z"),
        )

        expected = attach_units(
            func(strip_units(data_array)), {"data": unit_registry.m}
        )
        result = func(data_array)

        assert_equal_with_units(expected, result)
