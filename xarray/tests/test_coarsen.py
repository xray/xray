from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import xarray as xr
from xarray import DataArray, Dataset, set_options

from . import (
    assert_allclose,
    assert_equal,
    assert_identical,
    has_dask,
    raise_if_dask_computes,
    requires_cftime,
)


def test_coarsen_absent_dims_error(dataset: Dataset) -> None:
    with pytest.raises(ValueError, match=r"not found in Dataset."):
        dataset.coarsen(foo=2)


@pytest.mark.parametrize("dask", [True, False])
@pytest.mark.parametrize(("boundary", "side"), [("trim", "left"), ("pad", "right")])
def test_coarsen_dataset(dataset, dask, boundary, side):

    if dask and has_dask:
        dataset = dataset.chunk({"x": 4})

    actual = dataset.coarsen(time=2, x=3, boundary=boundary, side=side).max()
    assert_equal(
        actual["z1"], dataset["z1"].coarsen(x=3, boundary=boundary, side=side).max()
    )
    # coordinate should be mean by default
    assert_equal(
        actual["time"],
        dataset["time"].coarsen(time=2, boundary=boundary, side=side).mean(),
    )


@pytest.mark.parametrize("dask", [True, False])
def test_coarsen_coords(dataset, dask):

    if dask and has_dask:
        dataset = dataset.chunk({"x": 4})

    # check if coord_func works
    actual = dataset.coarsen(
        time=2, x=3, boundary="trim", coord_func={"time": "max"}
    ).max()
    assert_equal(actual["z1"], dataset["z1"].coarsen(x=3, boundary="trim").max())
    assert_equal(actual["time"], dataset["time"].coarsen(time=2, boundary="trim").max())

    # raise if exact
    with pytest.raises(ValueError):
        dataset.coarsen(x=3).mean()
    # should be no error
    dataset.isel(x=slice(0, 3 * (len(dataset["x"]) // 3))).coarsen(x=3).mean()

    # working test with pd.time
    da = xr.DataArray(
        np.linspace(0, 365, num=364),
        dims="time",
        coords={"time": pd.date_range("1999-12-15", periods=364)},
    )
    actual = da.coarsen(time=2).mean()


@requires_cftime
def test_coarsen_coords_cftime():
    times = xr.cftime_range("2000", periods=6)
    da = xr.DataArray(range(6), [("time", times)])
    actual = da.coarsen(time=3).mean()
    expected_times = xr.cftime_range("2000-01-02", freq="3D", periods=2)
    np.testing.assert_array_equal(actual.time, expected_times)


@pytest.mark.parametrize(
    "funcname, argument",
    [
        ("reduce", (np.mean,)),
        ("mean", ()),
    ],
)
def test_coarsen_keep_attrs(funcname, argument) -> None:
    global_attrs = {"units": "test", "long_name": "testing"}
    da_attrs = {"da_attr": "test"}
    attrs_coords = {"attrs_coords": "test"}
    da_not_coarsend_attrs = {"da_not_coarsend_attr": "test"}

    data = np.linspace(10, 15, 100)
    coords = np.linspace(1, 10, 100)

    ds = Dataset(
        data_vars={
            "da": ("coord", data, da_attrs),
            "da_not_coarsend": ("no_coord", data, da_not_coarsend_attrs),
        },
        coords={"coord": ("coord", coords, attrs_coords)},
        attrs=global_attrs,
    )

    # attrs are now kept per default
    func = getattr(ds.coarsen(dim={"coord": 5}), funcname)
    result = func(*argument)
    assert result.attrs == global_attrs
    assert result.da.attrs == da_attrs
    assert result.da_not_coarsend.attrs == da_not_coarsend_attrs
    assert result.coord.attrs == attrs_coords
    assert result.da.name == "da"
    assert result.da_not_coarsend.name == "da_not_coarsend"

    # discard attrs
    func = getattr(ds.coarsen(dim={"coord": 5}), funcname)
    result = func(*argument, keep_attrs=False)
    assert result.attrs == {}
    assert result.da.attrs == {}
    assert result.da_not_coarsend.attrs == {}
    assert result.coord.attrs == {}
    assert result.da.name == "da"
    assert result.da_not_coarsend.name == "da_not_coarsend"

    # test discard attrs using global option
    func = getattr(ds.coarsen(dim={"coord": 5}), funcname)
    with set_options(keep_attrs=False):
        result = func(*argument)

    assert result.attrs == {}
    assert result.da.attrs == {}
    assert result.da_not_coarsend.attrs == {}
    assert result.coord.attrs == {}
    assert result.da.name == "da"
    assert result.da_not_coarsend.name == "da_not_coarsend"

    # keyword takes precedence over global option
    func = getattr(ds.coarsen(dim={"coord": 5}), funcname)
    with set_options(keep_attrs=False):
        result = func(*argument, keep_attrs=True)

    assert result.attrs == global_attrs
    assert result.da.attrs == da_attrs
    assert result.da_not_coarsend.attrs == da_not_coarsend_attrs
    assert result.coord.attrs == attrs_coords
    assert result.da.name == "da"
    assert result.da_not_coarsend.name == "da_not_coarsend"

    func = getattr(ds.coarsen(dim={"coord": 5}), funcname)
    with set_options(keep_attrs=True):
        result = func(*argument, keep_attrs=False)

    assert result.attrs == {}
    assert result.da.attrs == {}
    assert result.da_not_coarsend.attrs == {}
    assert result.coord.attrs == {}
    assert result.da.name == "da"
    assert result.da_not_coarsend.name == "da_not_coarsend"


@pytest.mark.slow
@pytest.mark.parametrize("dataset", (1, 2), indirect=True)
@pytest.mark.parametrize("window", (1, 2, 3, 4))
@pytest.mark.parametrize("name", ("sum", "mean", "std", "var", "min", "max", "median"))
def test_coarsen_reduce(dataset: Dataset, window, name) -> None:
    # Use boundary="trim" to accommodate all window sizes used in tests
    coarsen_obj = dataset.coarsen(time=window, boundary="trim")

    # add nan prefix to numpy methods to get similar behavior as bottleneck
    actual = coarsen_obj.reduce(getattr(np, f"nan{name}"))
    expected = getattr(coarsen_obj, name)()
    assert_allclose(actual, expected)

    # make sure the order of data_var are not changed.
    assert list(dataset.data_vars.keys()) == list(actual.data_vars.keys())

    # Make sure the dimension order is restored
    for key, src_var in dataset.data_vars.items():
        assert src_var.dims == actual[key].dims


@pytest.mark.parametrize(
    "funcname, argument",
    [
        ("reduce", (np.mean,)),
        ("mean", ()),
    ],
)
def test_coarsen_da_keep_attrs(funcname, argument) -> None:
    attrs_da = {"da_attr": "test"}
    attrs_coords = {"attrs_coords": "test"}

    data = np.linspace(10, 15, 100)
    coords = np.linspace(1, 10, 100)

    da = DataArray(
        data,
        dims=("coord"),
        coords={"coord": ("coord", coords, attrs_coords)},
        attrs=attrs_da,
        name="name",
    )

    # attrs are now kept per default
    func = getattr(da.coarsen(dim={"coord": 5}), funcname)
    result = func(*argument)
    assert result.attrs == attrs_da
    da.coord.attrs == attrs_coords
    assert result.name == "name"

    # discard attrs
    func = getattr(da.coarsen(dim={"coord": 5}), funcname)
    result = func(*argument, keep_attrs=False)
    assert result.attrs == {}
    da.coord.attrs == {}
    assert result.name == "name"

    # test discard attrs using global option
    func = getattr(da.coarsen(dim={"coord": 5}), funcname)
    with set_options(keep_attrs=False):
        result = func(*argument)
    assert result.attrs == {}
    da.coord.attrs == {}
    assert result.name == "name"

    # keyword takes precedence over global option
    func = getattr(da.coarsen(dim={"coord": 5}), funcname)
    with set_options(keep_attrs=False):
        result = func(*argument, keep_attrs=True)
    assert result.attrs == attrs_da
    da.coord.attrs == {}
    assert result.name == "name"

    func = getattr(da.coarsen(dim={"coord": 5}), funcname)
    with set_options(keep_attrs=True):
        result = func(*argument, keep_attrs=False)
    assert result.attrs == {}
    da.coord.attrs == {}
    assert result.name == "name"


@pytest.mark.parametrize("dataarray", (1, 2), indirect=True)
@pytest.mark.parametrize("window", (1, 2, 3, 4))
@pytest.mark.parametrize("name", ("sum", "mean", "std", "max"))
def test_coarsen_da_reduce(dataarray, window, name) -> None:
    if dataarray.isnull().sum() > 1 and window == 1:
        pytest.skip("These parameters lead to all-NaN slices")

    # Use boundary="trim" to accommodate all window sizes used in tests
    coarsen_obj = dataarray.coarsen(time=window, boundary="trim")

    # add nan prefix to numpy methods to get similar # behavior as bottleneck
    actual = coarsen_obj.reduce(getattr(np, f"nan{name}"))
    expected = getattr(coarsen_obj, name)()
    assert_allclose(actual, expected)


@pytest.mark.parametrize("dask", [True, False])
def test_coarsen_construct(dask: bool) -> None:

    ds = Dataset(
        {
            "vart": ("time", np.arange(48), {"a": "b"}),
            "varx": ("x", np.arange(10), {"a": "b"}),
            "vartx": (("x", "time"), np.arange(480).reshape(10, 48), {"a": "b"}),
            "vary": ("y", np.arange(12)),
        },
        coords={"time": np.arange(48), "y": np.arange(12)},
        attrs={"foo": "bar"},
    )

    if dask and has_dask:
        ds = ds.chunk({"x": 4, "time": 10})

    expected = xr.Dataset(attrs={"foo": "bar"})
    expected["vart"] = (("year", "month"), ds.vart.data.reshape((-1, 12)), {"a": "b"})
    expected["varx"] = (("x", "x_reshaped"), ds.varx.data.reshape((-1, 5)), {"a": "b"})
    expected["vartx"] = (
        ("x", "x_reshaped", "year", "month"),
        ds.vartx.data.reshape(2, 5, 4, 12),
        {"a": "b"},
    )
    expected["vary"] = ds.vary
    expected.coords["time"] = (("year", "month"), ds.time.data.reshape((-1, 12)))

    with raise_if_dask_computes():
        actual = ds.coarsen(time=12, x=5).construct(
            {"time": ("year", "month"), "x": ("x", "x_reshaped")}
        )
    assert_identical(actual, expected)

    with raise_if_dask_computes():
        actual = ds.coarsen(time=12, x=5).construct(
            time=("year", "month"), x=("x", "x_reshaped")
        )
    assert_identical(actual, expected)

    with raise_if_dask_computes():
        actual = ds.coarsen(time=12, x=5).construct(
            {"time": ("year", "month"), "x": ("x", "x_reshaped")}, keep_attrs=False
        )
        for var in actual:
            assert actual[var].attrs == {}
        assert actual.attrs == {}

    with raise_if_dask_computes():
        actual = ds.vartx.coarsen(time=12, x=5).construct(
            {"time": ("year", "month"), "x": ("x", "x_reshaped")}
        )
    assert_identical(actual, expected["vartx"])

    with pytest.raises(ValueError):
        ds.coarsen(time=12).construct(foo="bar")

    with pytest.raises(ValueError):
        ds.coarsen(time=12, x=2).construct(time=("year", "month"))

    with pytest.raises(ValueError):
        ds.coarsen(time=12).construct()

    with pytest.raises(ValueError):
        ds.coarsen(time=12).construct(time="bar")

    with pytest.raises(ValueError):
        ds.coarsen(time=12).construct(time=("bar",))
