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


def assert_equal_with_units(a, b):
    try:
        from pint.quantity import BaseQuantity
    except ImportError:
        BaseQuantity = unit_registry.Quantity

    a_ = a if not isinstance(a, (xr.Dataset, xr.DataArray, xr.Variable)) else a.data
    b_ = b if not isinstance(b, (xr.Dataset, xr.DataArray, xr.Variable)) else b.data

    # workaround until pint implements allclose in __array_function__
    if isinstance(a_, BaseQuantity) or isinstance(b_, BaseQuantity):
        assert (hasattr(a_, "magnitude") and hasattr(b_, "magnitude")) and np.allclose(
            a_.magnitude, b_.magnitude, equal_nan=True
        )
    else:
        assert np.allclose(a_, b_, equal_nan=True)

    if hasattr(a_, "units") or hasattr(b_, "units"):
        assert (hasattr(a_, "units") and hasattr(b_, "units")) and a_.units == b_.units


def strip_units(data_array):
    def magnitude(da):
        if isinstance(da, xr.Variable):
            data = da.data
        else:
            data = da

        try:
            return data.magnitude
        except AttributeError:
            return data

    array = magnitude(data_array)
    coords = {name: magnitude(values) for name, values in data_array.coords.items()}

    return xr.DataArray(data=array, coords=coords, dims=data_array.dims)


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

        func = getattr(obj, self.name, None)
        if func is None or not isinstance(func, Callable):
            # fall back to module level numpy functions if not a xarray object
            if not isinstance(obj, (xr.Variable, xr.DataArray, xr.Dataset)):
                numpy_func = getattr(np, self.name)
                func = partial(numpy_func, obj)
            else:
                raise AttributeError(
                    "{obj} has no method named '{self.name}'".format(obj=obj, self=self)
                )

        all_args = list(self.args) + list(args)
        all_kwargs = {**self.kwargs, **kwargs}
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
            function("median"),
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
        ),
        ids=repr,
    )
    def test_aggregation(self, func, dtype):
        array = np.arange(10).astype(dtype) * unit_registry.m
        data_array = xr.DataArray(data=array)

        result_array = func(array)
        result_data_array = func(data_array)

        assert_equal_with_units(result_array, result_data_array)

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

        assert_equal_with_units(func(array), func(data_array))

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

        assert_equal_with_units(func(array), func(data_array))

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
        "value,error",
        (
            pytest.param(8, ValueError, id="without_unit"),
            pytest.param(
                8 * unit_registry.dimensionless, DimensionalityError, id="dimensionless"
            ),
            pytest.param(8 * unit_registry.s, DimensionalityError, id="incorrect_unit"),
            pytest.param(8 * unit_registry.m, None, id="correct_unit"),
        ),
    )
    def test_comparisons(self, comparison, value, error, dtype):
        array = (
            np.array([10.1, 5.2, 6.5, 8.0, 21.3, 7.1, 1.3]).astype(dtype)
            * unit_registry.m
        )
        data_array = xr.DataArray(data=array)

        # incompatible units are all not equal
        if error is not None and comparison is not operator.eq:
            with pytest.raises(error):
                comparison(array, value)

            with pytest.raises(error):
                comparison(data_array, value)
        else:
            result_data_array = comparison(data_array, value)
            result_array = comparison(array, value)

            assert_equal_with_units(result_array, result_data_array)

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
            assert_equal_with_units(np.sin(array), np.sin(data_array))

    @require_pint_array_function
    def test_bivariate_ufunc(self, dtype):
        unit = unit_registry.m
        array = np.arange(10).astype(dtype) * unit
        data_array = xr.DataArray(data=array)

        result_array = np.maximum(array, 0 * unit)
        assert_equal_with_units(result_array, np.maximum(data_array, 0 * unit))
        assert_equal_with_units(result_array, np.maximum(0 * unit, data_array))

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

        assert_equal_with_units(array[indices], data_array.isel(x=indices))

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
    @pytest.mark.xfail(
        reason="interp() mistakes quantities as objects instead of numeric type arrays"
    )
    @pytest.mark.parametrize(
        "unit,error",
        (
            pytest.param(1, None, id="without unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="with incorrect unit"),
            pytest.param(unit_registry.m, None, id="with correct unit"),
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
            pytest.param(1, None, id="without unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="with incorrect unit"),
            pytest.param(unit_registry.m, None, id="with correct unit"),
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
            pytest.param(1, None, id="without unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="with incorrect unit"),
            pytest.param(unit_registry.m, None, id="with correct unit"),
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
            pytest.param(1, None, id="without unit"),
            pytest.param(unit_registry.dimensionless, None, id="dimensionless"),
            pytest.param(unit_registry.s, None, id="with incorrect unit"),
            pytest.param(unit_registry.m, None, id="with correct unit"),
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
            result_array = (
                xr.DataArray(
                    data=array.magnitude,
                    coords={name: value.magnitude for name, value in coords.items()},
                    dims=("x", "y"),
                ).reindex_like(strip_units(new_data_array))
                * unit_registry.degK
            )
            result_data_array = data_array.reindex_like(new_data_array)

            assert_equal_with_units(result_array, result_data_array)
