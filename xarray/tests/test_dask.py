import operator
import pickle
import sys
from contextlib import suppress
from distutils.version import LooseVersion
from textwrap import dedent

import numpy as np
import pandas as pd
import pytest

import xarray as xr
import xarray.ufuncs as xu
from xarray import DataArray, Dataset, Variable
from xarray.core import duck_array_ops
from xarray.testing import assert_chunks_equal
from xarray.tests import mock

from ..core.duck_array_ops import lazy_array_equiv
from . import (
    assert_allclose,
    assert_array_equal,
    assert_equal,
    assert_frame_equal,
    assert_identical,
    raises_regex,
    requires_scipy_or_netCDF4,
)
from .test_backends import create_tmp_file

dask = pytest.importorskip("dask")
da = pytest.importorskip("dask.array")
dd = pytest.importorskip("dask.dataframe")

ON_WINDOWS = sys.platform == "win32"


class CountingScheduler:
    """ Simple dask scheduler counting the number of computes.

    Reference: https://stackoverflow.com/questions/53289286/ """

    def __init__(self, max_computes=0):
        self.total_computes = 0
        self.max_computes = max_computes

    def __call__(self, dsk, keys, **kwargs):
        self.total_computes += 1
        if self.total_computes > self.max_computes:
            raise RuntimeError(
                "Too many computes. Total: %d > max: %d."
                % (self.total_computes, self.max_computes)
            )
        return dask.get(dsk, keys, **kwargs)


def raise_if_dask_computes(max_computes=0):
    scheduler = CountingScheduler(max_computes)
    return dask.config.set(scheduler=scheduler)


def test_raise_if_dask_computes():
    data = da.from_array(np.random.RandomState(0).randn(4, 6), chunks=(2, 2))
    with raises_regex(RuntimeError, "Too many computes"):
        with raise_if_dask_computes():
            data.compute()


class DaskTestCase:
    def assertLazyAnd(self, expected, actual, test):
        with dask.config.set(scheduler="synchronous"):
            test(actual, expected)

        if isinstance(actual, Dataset):
            for k, v in actual.variables.items():
                if k in actual.dims:
                    assert isinstance(v.data, np.ndarray)
                else:
                    assert isinstance(v.data, da.Array)
        elif isinstance(actual, DataArray):
            assert isinstance(actual.data, da.Array)
            for k, v in actual.coords.items():
                if k in actual.dims:
                    assert isinstance(v.data, np.ndarray)
                else:
                    assert isinstance(v.data, da.Array)
        elif isinstance(actual, Variable):
            assert isinstance(actual.data, da.Array)
        else:
            assert False


class TestVariable(DaskTestCase):
    def assertLazyAndIdentical(self, expected, actual):
        self.assertLazyAnd(expected, actual, assert_identical)

    def assertLazyAndAllClose(self, expected, actual):
        self.assertLazyAnd(expected, actual, assert_allclose)

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.values = np.random.RandomState(0).randn(4, 6)
        self.data = da.from_array(self.values, chunks=(2, 2))

        self.eager_var = Variable(("x", "y"), self.values)
        self.lazy_var = Variable(("x", "y"), self.data)

    def test_basics(self):
        v = self.lazy_var
        assert self.data is v.data
        assert self.data.chunks == v.chunks
        assert_array_equal(self.values, v)

    def test_copy(self):
        self.assertLazyAndIdentical(self.eager_var, self.lazy_var.copy())
        self.assertLazyAndIdentical(self.eager_var, self.lazy_var.copy(deep=True))

    def test_chunk(self):
        for chunks, expected in [
            (None, ((2, 2), (2, 2, 2))),
            (3, ((3, 1), (3, 3))),
            ({"x": 3, "y": 3}, ((3, 1), (3, 3))),
            ({"x": 3}, ((3, 1), (2, 2, 2))),
            ({"x": (3, 1)}, ((3, 1), (2, 2, 2))),
        ]:
            rechunked = self.lazy_var.chunk(chunks)
            assert rechunked.chunks == expected
            self.assertLazyAndIdentical(self.eager_var, rechunked)

    def test_indexing(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(u[0], v[0])
        self.assertLazyAndIdentical(u[:1], v[:1])
        self.assertLazyAndIdentical(u[[0, 1], [0, 1, 2]], v[[0, 1], [0, 1, 2]])
        with raises_regex(TypeError, "stored in a dask array"):
            v[:1] = 0

    def test_squeeze(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(u[0].squeeze(), v[0].squeeze())

    def test_equals(self):
        v = self.lazy_var
        assert v.equals(v)
        assert isinstance(v.data, da.Array)
        assert v.identical(v)
        assert isinstance(v.data, da.Array)

    def test_transpose(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(u.T, v.T)

    def test_shift(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(u.shift(x=2), v.shift(x=2))
        self.assertLazyAndIdentical(u.shift(x=-2), v.shift(x=-2))
        assert v.data.chunks == v.shift(x=1).data.chunks

    def test_roll(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(u.roll(x=2), v.roll(x=2))
        assert v.data.chunks == v.roll(x=1).data.chunks

    def test_unary_op(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(-u, -v)
        self.assertLazyAndIdentical(abs(u), abs(v))
        self.assertLazyAndIdentical(u.round(), v.round())

    def test_binary_op(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(2 * u, 2 * v)
        self.assertLazyAndIdentical(u + u, v + v)
        self.assertLazyAndIdentical(u[0] + u, v[0] + v)

    def test_repr(self):
        expected = dedent(
            """\
            <xarray.Variable (x: 4, y: 6)>
            {!r}""".format(
                self.lazy_var.data
            )
        )
        assert expected == repr(self.lazy_var)

    def test_pickle(self):
        # Test that pickling/unpickling does not convert the dask
        # backend to numpy
        a1 = Variable(["x"], build_dask_array("x"))
        a1.compute()
        assert not a1._in_memory
        assert kernel_call_count == 1
        a2 = pickle.loads(pickle.dumps(a1))
        assert kernel_call_count == 1
        assert_identical(a1, a2)
        assert not a1._in_memory
        assert not a2._in_memory

    def test_reduce(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndAllClose(u.mean(), v.mean())
        self.assertLazyAndAllClose(u.std(), v.std())
        with raise_if_dask_computes():
            actual = v.argmax(dim="x")
        self.assertLazyAndAllClose(u.argmax(dim="x"), actual)
        with raise_if_dask_computes():
            actual = v.argmin(dim="x")
        self.assertLazyAndAllClose(u.argmin(dim="x"), actual)
        self.assertLazyAndAllClose((u > 1).any(), (v > 1).any())
        self.assertLazyAndAllClose((u < 1).all("x"), (v < 1).all("x"))
        with raises_regex(NotImplementedError, "only works along an axis"):
            v.median()
        with raises_regex(NotImplementedError, "only works along an axis"):
            v.median(v.dims)
        with raise_if_dask_computes():
            v.reduce(duck_array_ops.mean)

    def test_missing_values(self):
        values = np.array([0, 1, np.nan, 3])
        data = da.from_array(values, chunks=(2,))

        eager_var = Variable("x", values)
        lazy_var = Variable("x", data)
        self.assertLazyAndIdentical(eager_var, lazy_var.fillna(lazy_var))
        self.assertLazyAndIdentical(Variable("x", range(4)), lazy_var.fillna(2))
        self.assertLazyAndIdentical(eager_var.count(), lazy_var.count())

    def test_concat(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndIdentical(u, Variable.concat([v[:2], v[2:]], "x"))
        self.assertLazyAndIdentical(u[:2], Variable.concat([v[0], v[1]], "x"))
        self.assertLazyAndIdentical(u[:2], Variable.concat([u[0], v[1]], "x"))
        self.assertLazyAndIdentical(u[:2], Variable.concat([v[0], u[1]], "x"))
        self.assertLazyAndIdentical(
            u[:3], Variable.concat([v[[0, 2]], v[[1]]], "x", positions=[[0, 2], [1]])
        )

    def test_missing_methods(self):
        v = self.lazy_var
        try:
            v.argsort()
        except NotImplementedError as err:
            assert "dask" in str(err)
        try:
            v[0].item()
        except NotImplementedError as err:
            assert "dask" in str(err)

    @pytest.mark.filterwarnings("ignore::PendingDeprecationWarning")
    def test_univariate_ufunc(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndAllClose(np.sin(u), xu.sin(v))

    @pytest.mark.filterwarnings("ignore::PendingDeprecationWarning")
    def test_bivariate_ufunc(self):
        u = self.eager_var
        v = self.lazy_var
        self.assertLazyAndAllClose(np.maximum(u, 0), xu.maximum(v, 0))
        self.assertLazyAndAllClose(np.maximum(u, 0), xu.maximum(0, v))

    def test_compute(self):
        u = self.eager_var
        v = self.lazy_var

        assert dask.is_dask_collection(v)
        (v2,) = dask.compute(v + 1)
        assert not dask.is_dask_collection(v2)

        assert ((u + 1).data == v2.data).all()

    def test_persist(self):
        u = self.eager_var
        v = self.lazy_var + 1

        (v2,) = dask.persist(v)
        assert v is not v2
        assert len(v2.__dask_graph__()) < len(v.__dask_graph__())
        assert v2.__dask_keys__() == v.__dask_keys__()
        assert dask.is_dask_collection(v)
        assert dask.is_dask_collection(v2)

        self.assertLazyAndAllClose(u + 1, v)
        self.assertLazyAndAllClose(u + 1, v2)


class TestDataArrayAndDataset(DaskTestCase):
    def assertLazyAndIdentical(self, expected, actual):
        self.assertLazyAnd(expected, actual, assert_identical)

    def assertLazyAndAllClose(self, expected, actual):
        self.assertLazyAnd(expected, actual, assert_allclose)

    def assertLazyAndEqual(self, expected, actual):
        self.assertLazyAnd(expected, actual, assert_equal)

    @pytest.fixture(autouse=True)
    def setUp(self):
        self.values = np.random.randn(4, 6)
        self.data = da.from_array(self.values, chunks=(2, 2))
        self.eager_array = DataArray(
            self.values, coords={"x": range(4)}, dims=("x", "y"), name="foo"
        )
        self.lazy_array = DataArray(
            self.data, coords={"x": range(4)}, dims=("x", "y"), name="foo"
        )

    def test_rechunk(self):
        chunked = self.eager_array.chunk({"x": 2}).chunk({"y": 2})
        assert chunked.chunks == ((2,) * 2, (2,) * 3)
        self.assertLazyAndIdentical(self.lazy_array, chunked)

    def test_new_chunk(self):
        chunked = self.eager_array.chunk()
        assert chunked.data.name.startswith("xarray-<this-array>")

    def test_lazy_dataset(self):
        lazy_ds = Dataset({"foo": (("x", "y"), self.data)})
        assert isinstance(lazy_ds.foo.variable.data, da.Array)

    def test_lazy_array(self):
        u = self.eager_array
        v = self.lazy_array

        self.assertLazyAndAllClose(u, v)
        self.assertLazyAndAllClose(-u, -v)
        self.assertLazyAndAllClose(u.T, v.T)
        self.assertLazyAndAllClose(u.mean(), v.mean())
        self.assertLazyAndAllClose(1 + u, 1 + v)

        actual = xr.concat([v[:2], v[2:]], "x")
        self.assertLazyAndAllClose(u, actual)

    def test_compute(self):
        u = self.eager_array
        v = self.lazy_array

        assert dask.is_dask_collection(v)
        (v2,) = dask.compute(v + 1)
        assert not dask.is_dask_collection(v2)

        assert ((u + 1).data == v2.data).all()

    def test_persist(self):
        u = self.eager_array
        v = self.lazy_array + 1

        (v2,) = dask.persist(v)
        assert v is not v2
        assert len(v2.__dask_graph__()) < len(v.__dask_graph__())
        assert v2.__dask_keys__() == v.__dask_keys__()
        assert dask.is_dask_collection(v)
        assert dask.is_dask_collection(v2)

        self.assertLazyAndAllClose(u + 1, v)
        self.assertLazyAndAllClose(u + 1, v2)

    def test_concat_loads_variables(self):
        # Test that concat() computes not-in-memory variables at most once
        # and loads them in the output, while leaving the input unaltered.
        d1 = build_dask_array("d1")
        c1 = build_dask_array("c1")
        d2 = build_dask_array("d2")
        c2 = build_dask_array("c2")
        d3 = build_dask_array("d3")
        c3 = build_dask_array("c3")
        # Note: c is a non-index coord.
        # Index coords are loaded by IndexVariable.__init__.
        ds1 = Dataset(data_vars={"d": ("x", d1)}, coords={"c": ("x", c1)})
        ds2 = Dataset(data_vars={"d": ("x", d2)}, coords={"c": ("x", c2)})
        ds3 = Dataset(data_vars={"d": ("x", d3)}, coords={"c": ("x", c3)})

        assert kernel_call_count == 0
        out = xr.concat(
            [ds1, ds2, ds3], dim="n", data_vars="different", coords="different"
        )
        # each kernel is computed exactly once
        assert kernel_call_count == 6
        # variables are loaded in the output
        assert isinstance(out["d"].data, np.ndarray)
        assert isinstance(out["c"].data, np.ndarray)

        out = xr.concat([ds1, ds2, ds3], dim="n", data_vars="all", coords="all")
        # no extra kernel calls
        assert kernel_call_count == 6
        assert isinstance(out["d"].data, dask.array.Array)
        assert isinstance(out["c"].data, dask.array.Array)

        out = xr.concat([ds1, ds2, ds3], dim="n", data_vars=["d"], coords=["c"])
        # no extra kernel calls
        assert kernel_call_count == 6
        assert isinstance(out["d"].data, dask.array.Array)
        assert isinstance(out["c"].data, dask.array.Array)

        out = xr.concat([ds1, ds2, ds3], dim="n", data_vars=[], coords=[])
        # variables are loaded once as we are validing that they're identical
        assert kernel_call_count == 12
        assert isinstance(out["d"].data, np.ndarray)
        assert isinstance(out["c"].data, np.ndarray)

        out = xr.concat(
            [ds1, ds2, ds3],
            dim="n",
            data_vars="different",
            coords="different",
            compat="identical",
        )
        # compat=identical doesn't do any more kernel calls than compat=equals
        assert kernel_call_count == 18
        assert isinstance(out["d"].data, np.ndarray)
        assert isinstance(out["c"].data, np.ndarray)

        # When the test for different turns true halfway through,
        # stop computing variables as it would not have any benefit
        ds4 = Dataset(data_vars={"d": ("x", [2.0])}, coords={"c": ("x", [2.0])})
        out = xr.concat(
            [ds1, ds2, ds4, ds3], dim="n", data_vars="different", coords="different"
        )
        # the variables of ds1 and ds2 were computed, but those of ds3 didn't
        assert kernel_call_count == 22
        assert isinstance(out["d"].data, dask.array.Array)
        assert isinstance(out["c"].data, dask.array.Array)
        # the data of ds1 and ds2 was loaded into numpy and then
        # concatenated to the data of ds3. Thus, only ds3 is computed now.
        out.compute()
        assert kernel_call_count == 24

        # Finally, test that originals are unaltered
        assert ds1["d"].data is d1
        assert ds1["c"].data is c1
        assert ds2["d"].data is d2
        assert ds2["c"].data is c2
        assert ds3["d"].data is d3
        assert ds3["c"].data is c3

        # now check that concat() is correctly using dask name equality to skip loads
        out = xr.concat(
            [ds1, ds1, ds1], dim="n", data_vars="different", coords="different"
        )
        assert kernel_call_count == 24
        # variables are not loaded in the output
        assert isinstance(out["d"].data, dask.array.Array)
        assert isinstance(out["c"].data, dask.array.Array)

        out = xr.concat(
            [ds1, ds1, ds1], dim="n", data_vars=[], coords=[], compat="identical"
        )
        assert kernel_call_count == 24
        # variables are not loaded in the output
        assert isinstance(out["d"].data, dask.array.Array)
        assert isinstance(out["c"].data, dask.array.Array)

        out = xr.concat(
            [ds1, ds2.compute(), ds3],
            dim="n",
            data_vars="all",
            coords="different",
            compat="identical",
        )
        # c1,c3 must be computed for comparison since c2 is numpy;
        # d2 is computed too
        assert kernel_call_count == 28

        out = xr.concat(
            [ds1, ds2.compute(), ds3],
            dim="n",
            data_vars="all",
            coords="all",
            compat="identical",
        )
        # no extra computes
        assert kernel_call_count == 30

        # Finally, test that originals are unaltered
        assert ds1["d"].data is d1
        assert ds1["c"].data is c1
        assert ds2["d"].data is d2
        assert ds2["c"].data is c2
        assert ds3["d"].data is d3
        assert ds3["c"].data is c3

    def test_groupby(self):
        u = self.eager_array
        v = self.lazy_array

        expected = u.groupby("x").mean(...)
        with raise_if_dask_computes():
            actual = v.groupby("x").mean(...)
        self.assertLazyAndAllClose(expected, actual)

    def test_rolling(self):
        u = self.eager_array
        v = self.lazy_array

        expected = u.rolling(x=2).mean()
        with raise_if_dask_computes():
            actual = v.rolling(x=2).mean()
        self.assertLazyAndAllClose(expected, actual)

    def test_groupby_first(self):
        u = self.eager_array
        v = self.lazy_array

        for coords in [u.coords, v.coords]:
            coords["ab"] = ("x", ["a", "a", "b", "b"])
        with raises_regex(NotImplementedError, "dask"):
            v.groupby("ab").first()
        expected = u.groupby("ab").first()
        with raise_if_dask_computes():
            actual = v.groupby("ab").first(skipna=False)
        self.assertLazyAndAllClose(expected, actual)

    def test_reindex(self):
        u = self.eager_array.assign_coords(y=range(6))
        v = self.lazy_array.assign_coords(y=range(6))

        for kwargs in [
            {"x": [2, 3, 4]},
            {"x": [1, 100, 2, 101, 3]},
            {"x": [2.5, 3, 3.5], "y": [2, 2.5, 3]},
        ]:
            expected = u.reindex(**kwargs)
            actual = v.reindex(**kwargs)
            self.assertLazyAndAllClose(expected, actual)

    def test_to_dataset_roundtrip(self):
        u = self.eager_array
        v = self.lazy_array

        expected = u.assign_coords(x=u["x"])
        self.assertLazyAndEqual(expected, v.to_dataset("x").to_array("x"))

    def test_merge(self):
        def duplicate_and_merge(array):
            return xr.merge([array, array.rename("bar")]).to_array()

        expected = duplicate_and_merge(self.eager_array)
        actual = duplicate_and_merge(self.lazy_array)
        self.assertLazyAndEqual(expected, actual)

    @pytest.mark.filterwarnings("ignore::PendingDeprecationWarning")
    def test_ufuncs(self):
        u = self.eager_array
        v = self.lazy_array
        self.assertLazyAndAllClose(np.sin(u), xu.sin(v))

    def test_where_dispatching(self):
        a = np.arange(10)
        b = a > 3
        x = da.from_array(a, 5)
        y = da.from_array(b, 5)
        expected = DataArray(a).where(b)
        self.assertLazyAndEqual(expected, DataArray(a).where(y))
        self.assertLazyAndEqual(expected, DataArray(x).where(b))
        self.assertLazyAndEqual(expected, DataArray(x).where(y))

    def test_simultaneous_compute(self):
        ds = Dataset({"foo": ("x", range(5)), "bar": ("x", range(5))}).chunk()

        count = [0]

        def counting_get(*args, **kwargs):
            count[0] += 1
            return dask.get(*args, **kwargs)

        ds.load(scheduler=counting_get)

        assert count[0] == 1

    def test_stack(self):
        data = da.random.normal(size=(2, 3, 4), chunks=(1, 3, 4))
        arr = DataArray(data, dims=("w", "x", "y"))
        stacked = arr.stack(z=("x", "y"))
        z = pd.MultiIndex.from_product([np.arange(3), np.arange(4)], names=["x", "y"])
        expected = DataArray(data.reshape(2, -1), {"z": z}, dims=["w", "z"])
        assert stacked.data.chunks == expected.data.chunks
        self.assertLazyAndEqual(expected, stacked)

    def test_dot(self):
        eager = self.eager_array.dot(self.eager_array[0])
        lazy = self.lazy_array.dot(self.lazy_array[0])
        self.assertLazyAndAllClose(eager, lazy)

    @pytest.mark.skipif(LooseVersion(dask.__version__) >= "2.0", reason="no meta")
    def test_dataarray_repr_legacy(self):
        data = build_dask_array("data")
        nonindex_coord = build_dask_array("coord")
        a = DataArray(data, dims=["x"], coords={"y": ("x", nonindex_coord)})
        expected = dedent(
            """\
            <xarray.DataArray 'data' (x: 1)>
            {!r}
            Coordinates:
                y        (x) int64 dask.array<chunksize=(1,), meta=np.ndarray>
            Dimensions without coordinates: x""".format(
                data
            )
        )
        assert expected == repr(a)
        assert kernel_call_count == 0  # should not evaluate dask array

    @pytest.mark.skipif(LooseVersion(dask.__version__) < "2.0", reason="needs meta")
    def test_dataarray_repr(self):
        data = build_dask_array("data")
        nonindex_coord = build_dask_array("coord")
        a = DataArray(data, dims=["x"], coords={"y": ("x", nonindex_coord)})
        expected = dedent(
            """\
            <xarray.DataArray 'data' (x: 1)>
            {!r}
            Coordinates:
                y        (x) int64 dask.array<chunksize=(1,), meta=np.ndarray>
            Dimensions without coordinates: x""".format(
                data
            )
        )
        assert expected == repr(a)
        assert kernel_call_count == 0  # should not evaluate dask array

    @pytest.mark.skipif(LooseVersion(dask.__version__) < "2.0", reason="needs meta")
    def test_dataset_repr(self):
        data = build_dask_array("data")
        nonindex_coord = build_dask_array("coord")
        ds = Dataset(data_vars={"a": ("x", data)}, coords={"y": ("x", nonindex_coord)})
        expected = dedent(
            """\
            <xarray.Dataset>
            Dimensions:  (x: 1)
            Coordinates:
                y        (x) int64 dask.array<chunksize=(1,), meta=np.ndarray>
            Dimensions without coordinates: x
            Data variables:
                a        (x) int64 dask.array<chunksize=(1,), meta=np.ndarray>"""
        )
        assert expected == repr(ds)
        assert kernel_call_count == 0  # should not evaluate dask array

    def test_dataarray_pickle(self):
        # Test that pickling/unpickling converts the dask backend
        # to numpy in neither the data variable nor the non-index coords
        data = build_dask_array("data")
        nonindex_coord = build_dask_array("coord")
        a1 = DataArray(data, dims=["x"], coords={"y": ("x", nonindex_coord)})
        a1.compute()
        assert not a1._in_memory
        assert not a1.coords["y"]._in_memory
        assert kernel_call_count == 2
        a2 = pickle.loads(pickle.dumps(a1))
        assert kernel_call_count == 2
        assert_identical(a1, a2)
        assert not a1._in_memory
        assert not a2._in_memory
        assert not a1.coords["y"]._in_memory
        assert not a2.coords["y"]._in_memory

    def test_dataset_pickle(self):
        # Test that pickling/unpickling converts the dask backend
        # to numpy in neither the data variables nor the non-index coords
        data = build_dask_array("data")
        nonindex_coord = build_dask_array("coord")
        ds1 = Dataset(data_vars={"a": ("x", data)}, coords={"y": ("x", nonindex_coord)})
        ds1.compute()
        assert not ds1["a"]._in_memory
        assert not ds1["y"]._in_memory
        assert kernel_call_count == 2
        ds2 = pickle.loads(pickle.dumps(ds1))
        assert kernel_call_count == 2
        assert_identical(ds1, ds2)
        assert not ds1["a"]._in_memory
        assert not ds2["a"]._in_memory
        assert not ds1["y"]._in_memory
        assert not ds2["y"]._in_memory

    def test_dataarray_getattr(self):
        # ipython/jupyter does a long list of getattr() calls to when trying to
        # represent an object.
        # Make sure we're not accidentally computing dask variables.
        data = build_dask_array("data")
        nonindex_coord = build_dask_array("coord")
        a = DataArray(data, dims=["x"], coords={"y": ("x", nonindex_coord)})
        with suppress(AttributeError):
            getattr(a, "NOTEXIST")
        assert kernel_call_count == 0

    def test_dataset_getattr(self):
        # Test that pickling/unpickling converts the dask backend
        # to numpy in neither the data variables nor the non-index coords
        data = build_dask_array("data")
        nonindex_coord = build_dask_array("coord")
        ds = Dataset(data_vars={"a": ("x", data)}, coords={"y": ("x", nonindex_coord)})
        with suppress(AttributeError):
            getattr(ds, "NOTEXIST")
        assert kernel_call_count == 0

    def test_values(self):
        # Test that invoking the values property does not convert the dask
        # backend to numpy
        a = DataArray([1, 2]).chunk()
        assert not a._in_memory
        assert a.values.tolist() == [1, 2]
        assert not a._in_memory

    def test_from_dask_variable(self):
        # Test array creation from Variable with dask backend.
        # This is used e.g. in broadcast()
        a = DataArray(self.lazy_array.variable, coords={"x": range(4)}, name="foo")
        self.assertLazyAndIdentical(self.lazy_array, a)


class TestToDaskDataFrame:
    def test_to_dask_dataframe(self):
        # Test conversion of Datasets to dask DataFrames
        x = da.from_array(np.random.randn(10), chunks=4)
        y = np.arange(10, dtype="uint8")
        t = list("abcdefghij")

        ds = Dataset({"a": ("t", x), "b": ("t", y), "t": ("t", t)})

        expected_pd = pd.DataFrame({"a": x, "b": y}, index=pd.Index(t, name="t"))

        # test if 1-D index is correctly set up
        expected = dd.from_pandas(expected_pd, chunksize=4)
        actual = ds.to_dask_dataframe(set_index=True)
        # test if we have dask dataframes
        assert isinstance(actual, dd.DataFrame)

        # use the .equals from pandas to check dataframes are equivalent
        assert_frame_equal(expected.compute(), actual.compute())

        # test if no index is given
        expected = dd.from_pandas(expected_pd.reset_index(drop=False), chunksize=4)

        actual = ds.to_dask_dataframe(set_index=False)

        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected.compute(), actual.compute())

    def test_to_dask_dataframe_2D(self):
        # Test if 2-D dataset is supplied
        w = da.from_array(np.random.randn(2, 3), chunks=(1, 2))
        ds = Dataset({"w": (("x", "y"), w)})
        ds["x"] = ("x", np.array([0, 1], np.int64))
        ds["y"] = ("y", list("abc"))

        # dask dataframes do not (yet) support multiindex,
        # but when it does, this would be the expected index:
        exp_index = pd.MultiIndex.from_arrays(
            [[0, 0, 0, 1, 1, 1], ["a", "b", "c", "a", "b", "c"]], names=["x", "y"]
        )
        expected = pd.DataFrame({"w": w.reshape(-1)}, index=exp_index)
        # so for now, reset the index
        expected = expected.reset_index(drop=False)
        actual = ds.to_dask_dataframe(set_index=False)

        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected, actual.compute())

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_to_dask_dataframe_2D_set_index(self):
        # This will fail until dask implements MultiIndex support
        w = da.from_array(np.random.randn(2, 3), chunks=(1, 2))
        ds = Dataset({"w": (("x", "y"), w)})
        ds["x"] = ("x", np.array([0, 1], np.int64))
        ds["y"] = ("y", list("abc"))

        expected = ds.compute().to_dataframe()
        actual = ds.to_dask_dataframe(set_index=True)
        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected, actual.compute())

    def test_to_dask_dataframe_coordinates(self):
        # Test if coordinate is also a dask array
        x = da.from_array(np.random.randn(10), chunks=4)
        t = da.from_array(np.arange(10) * 2, chunks=4)

        ds = Dataset({"a": ("t", x), "t": ("t", t)})

        expected_pd = pd.DataFrame({"a": x}, index=pd.Index(t, name="t"))
        expected = dd.from_pandas(expected_pd, chunksize=4)
        actual = ds.to_dask_dataframe(set_index=True)
        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected.compute(), actual.compute())

    def test_to_dask_dataframe_not_daskarray(self):
        # Test if DataArray is not a dask array
        x = np.random.randn(10)
        y = np.arange(10, dtype="uint8")
        t = list("abcdefghij")

        ds = Dataset({"a": ("t", x), "b": ("t", y), "t": ("t", t)})

        expected = pd.DataFrame({"a": x, "b": y}, index=pd.Index(t, name="t"))

        actual = ds.to_dask_dataframe(set_index=True)
        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected, actual.compute())

    def test_to_dask_dataframe_no_coordinate(self):
        x = da.from_array(np.random.randn(10), chunks=4)
        ds = Dataset({"x": ("dim_0", x)})

        expected = ds.compute().to_dataframe().reset_index()
        actual = ds.to_dask_dataframe()
        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected, actual.compute())

        expected = ds.compute().to_dataframe()
        actual = ds.to_dask_dataframe(set_index=True)
        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected, actual.compute())

    def test_to_dask_dataframe_dim_order(self):
        values = np.array([[1, 2], [3, 4]], dtype=np.int64)
        ds = Dataset({"w": (("x", "y"), values)}).chunk(1)

        expected = ds["w"].to_series().reset_index()
        actual = ds.to_dask_dataframe(dim_order=["x", "y"])
        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected, actual.compute())

        expected = ds["w"].T.to_series().reset_index()
        actual = ds.to_dask_dataframe(dim_order=["y", "x"])
        assert isinstance(actual, dd.DataFrame)
        assert_frame_equal(expected, actual.compute())

        with raises_regex(ValueError, "does not match the set of dimensions"):
            ds.to_dask_dataframe(dim_order=["x"])


@pytest.mark.parametrize("method", ["load", "compute"])
def test_dask_kwargs_variable(method):
    x = Variable("y", da.from_array(np.arange(3), chunks=(2,)))
    # args should be passed on to da.Array.compute()
    with mock.patch.object(
        da.Array, "compute", return_value=np.arange(3)
    ) as mock_compute:
        getattr(x, method)(foo="bar")
    mock_compute.assert_called_with(foo="bar")


@pytest.mark.parametrize("method", ["load", "compute", "persist"])
def test_dask_kwargs_dataarray(method):
    data = da.from_array(np.arange(3), chunks=(2,))
    x = DataArray(data)
    if method in ["load", "compute"]:
        dask_func = "dask.array.compute"
    else:
        dask_func = "dask.persist"
    # args should be passed on to "dask_func"
    with mock.patch(dask_func) as mock_func:
        getattr(x, method)(foo="bar")
    mock_func.assert_called_with(data, foo="bar")


@pytest.mark.parametrize("method", ["load", "compute", "persist"])
def test_dask_kwargs_dataset(method):
    data = da.from_array(np.arange(3), chunks=(2,))
    x = Dataset({"x": (("y"), data)})
    if method in ["load", "compute"]:
        dask_func = "dask.array.compute"
    else:
        dask_func = "dask.persist"
    # args should be passed on to "dask_func"
    with mock.patch(dask_func) as mock_func:
        getattr(x, method)(foo="bar")
    mock_func.assert_called_with(data, foo="bar")


kernel_call_count = 0


def kernel(name):
    """Dask kernel to test pickling/unpickling and __repr__.
    Must be global to make it pickleable.
    """
    global kernel_call_count
    kernel_call_count += 1
    return np.ones(1, dtype=np.int64)


def build_dask_array(name):
    global kernel_call_count
    kernel_call_count = 0
    return dask.array.Array(
        dask={(name, 0): (kernel, name)}, name=name, chunks=((1,),), dtype=np.int64
    )


@pytest.mark.parametrize(
    "persist", [lambda x: x.persist(), lambda x: dask.persist(x)[0]]
)
def test_persist_Dataset(persist):
    ds = Dataset({"foo": ("x", range(5)), "bar": ("x", range(5))}).chunk()
    ds = ds + 1
    n = len(ds.foo.data.dask)

    ds2 = persist(ds)

    assert len(ds2.foo.data.dask) == 1
    assert len(ds.foo.data.dask) == n  # doesn't mutate in place


@pytest.mark.parametrize(
    "persist", [lambda x: x.persist(), lambda x: dask.persist(x)[0]]
)
def test_persist_DataArray(persist):
    x = da.arange(10, chunks=(5,))
    y = DataArray(x)
    z = y + 1
    n = len(z.data.dask)

    zz = persist(z)

    assert len(z.data.dask) == n
    assert len(zz.data.dask) == zz.data.npartitions


def test_dataarray_with_dask_coords():
    import toolz

    x = xr.Variable("x", da.arange(8, chunks=(4,)))
    y = xr.Variable("y", da.arange(8, chunks=(4,)) * 2)
    data = da.random.random((8, 8), chunks=(4, 4)) + 1
    array = xr.DataArray(data, dims=["x", "y"])
    array.coords["xx"] = x
    array.coords["yy"] = y

    assert dict(array.__dask_graph__()) == toolz.merge(
        data.__dask_graph__(), x.__dask_graph__(), y.__dask_graph__()
    )

    (array2,) = dask.compute(array)
    assert not dask.is_dask_collection(array2)

    assert all(isinstance(v._variable.data, np.ndarray) for v in array2.coords.values())


def test_basic_compute():
    ds = Dataset({"foo": ("x", range(5)), "bar": ("x", range(5))}).chunk({"x": 2})
    for get in [dask.threaded.get, dask.multiprocessing.get, dask.local.get_sync, None]:
        with dask.config.set(scheduler=get):
            ds.compute()
            ds.foo.compute()
            ds.foo.variable.compute()


def test_dask_layers_and_dependencies():
    ds = Dataset({"foo": ("x", range(5)), "bar": ("x", range(5))}).chunk()

    x = dask.delayed(ds)
    assert set(x.__dask_graph__().dependencies).issuperset(
        ds.__dask_graph__().dependencies
    )
    assert set(x.foo.__dask_graph__().dependencies).issuperset(
        ds.__dask_graph__().dependencies
    )


def make_da():
    da = xr.DataArray(
        np.ones((10, 20)),
        dims=["x", "y"],
        coords={"x": np.arange(10), "y": np.arange(100, 120)},
        name="a",
    ).chunk({"x": 4, "y": 5})
    da.attrs["test"] = "test"
    da.coords["c2"] = 0.5
    da.coords["ndcoord"] = da.x * 2
    da.coords["cxy"] = (da.x * da.y).chunk({"x": 4, "y": 5})

    return da


def make_ds():
    map_ds = xr.Dataset()
    map_ds["a"] = make_da()
    map_ds["b"] = map_ds.a + 50
    map_ds["c"] = map_ds.x + 20
    map_ds = map_ds.chunk({"x": 4, "y": 5})
    map_ds["d"] = ("z", [1, 1, 1, 1])
    map_ds["z"] = [0, 1, 2, 3]
    map_ds["e"] = map_ds.x + map_ds.y
    map_ds.coords["c1"] = 0.5
    map_ds.coords["cx"] = ("x", np.arange(len(map_ds.x)))
    map_ds.coords["cx"].attrs["test2"] = "test2"
    map_ds.attrs["test"] = "test"
    map_ds.coords["xx"] = map_ds["a"] * map_ds.y

    return map_ds


# fixtures cannot be used in parametrize statements
# instead use this workaround
# https://docs.pytest.org/en/latest/deprecations.html#calling-fixtures-directly
@pytest.fixture
def map_da():
    return make_da()


@pytest.fixture
def map_ds():
    return make_ds()


def test_unify_chunks(map_ds):
    ds_copy = map_ds.copy()
    ds_copy["cxy"] = ds_copy.cxy.chunk({"y": 10})

    with raises_regex(ValueError, "inconsistent chunks"):
        ds_copy.chunks

    expected_chunks = {"x": (4, 4, 2), "y": (5, 5, 5, 5), "z": (4,)}
    with raise_if_dask_computes():
        actual_chunks = ds_copy.unify_chunks().chunks
    expected_chunks == actual_chunks
    assert_identical(map_ds, ds_copy.unify_chunks())


@pytest.mark.parametrize("obj", [make_ds(), make_da()])
@pytest.mark.parametrize(
    "transform", [lambda x: x.compute(), lambda x: x.unify_chunks()]
)
def test_unify_chunks_shallow_copy(obj, transform):
    obj = transform(obj)
    unified = obj.unify_chunks()
    assert_identical(obj, unified) and obj is not obj.unify_chunks()


def test_map_blocks_error(map_da, map_ds):
    def bad_func(darray):
        return (darray * darray.x + 5 * darray.y)[:1, :1]

    with raises_regex(ValueError, "Received dimension 'x' of length 1"):
        xr.map_blocks(bad_func, map_da).compute()

    def returns_numpy(darray):
        return (darray * darray.x + 5 * darray.y).values

    with raises_regex(TypeError, "Function must return an xarray DataArray"):
        xr.map_blocks(returns_numpy, map_da)

    with raises_regex(TypeError, "args must be"):
        xr.map_blocks(operator.add, map_da, args=10)

    with raises_regex(TypeError, "kwargs must be"):
        xr.map_blocks(operator.add, map_da, args=[10], kwargs=[20])

    def really_bad_func(darray):
        raise ValueError("couldn't do anything.")

    with raises_regex(Exception, "Cannot infer"):
        xr.map_blocks(really_bad_func, map_da)

    ds_copy = map_ds.copy()
    ds_copy["cxy"] = ds_copy.cxy.chunk({"y": 10})

    with raises_regex(ValueError, "inconsistent chunks"):
        xr.map_blocks(bad_func, ds_copy)

    with raises_regex(TypeError, "Cannot pass dask collections"):
        xr.map_blocks(bad_func, map_da, args=[map_da.chunk()])

    with raises_regex(TypeError, "Cannot pass dask collections"):
        xr.map_blocks(bad_func, map_da, kwargs=dict(a=map_da.chunk()))


@pytest.mark.parametrize("obj", [make_da(), make_ds()])
def test_map_blocks(obj):
    def func(obj):
        result = obj + obj.x + 5 * obj.y
        return result

    with raise_if_dask_computes():
        actual = xr.map_blocks(func, obj)
    expected = func(obj)
    assert_chunks_equal(expected.chunk(), actual)
    assert_identical(actual, expected)


@pytest.mark.parametrize("obj", [make_da(), make_ds()])
def test_map_blocks_convert_args_to_list(obj):
    expected = obj + 10
    with raise_if_dask_computes():
        actual = xr.map_blocks(operator.add, obj, [10])
    assert_chunks_equal(expected.chunk(), actual)
    assert_identical(actual, expected)


@pytest.mark.parametrize("obj", [make_da(), make_ds()])
def test_map_blocks_add_attrs(obj):
    def add_attrs(obj):
        obj = obj.copy(deep=True)
        obj.attrs["new"] = "new"
        obj.cxy.attrs["new2"] = "new2"
        return obj

    expected = add_attrs(obj)
    with raise_if_dask_computes():
        actual = xr.map_blocks(add_attrs, obj)

    assert_identical(actual, expected)


def test_map_blocks_change_name(map_da):
    def change_name(obj):
        obj = obj.copy(deep=True)
        obj.name = "new"
        return obj

    expected = change_name(map_da)
    with raise_if_dask_computes():
        actual = xr.map_blocks(change_name, map_da)

    assert_identical(actual, expected)


@pytest.mark.parametrize("obj", [make_da(), make_ds()])
def test_map_blocks_kwargs(obj):
    expected = xr.full_like(obj, fill_value=np.nan)
    with raise_if_dask_computes():
        actual = xr.map_blocks(xr.full_like, obj, kwargs=dict(fill_value=np.nan))
    assert_chunks_equal(expected.chunk(), actual)
    assert_identical(actual, expected)


def test_map_blocks_to_array(map_ds):
    with raise_if_dask_computes():
        actual = xr.map_blocks(lambda x: x.to_array(), map_ds)

    # to_array does not preserve name, so cannot use assert_identical
    assert_equal(actual, map_ds.to_array())


@pytest.mark.parametrize(
    "func",
    [
        lambda x: x,
        lambda x: x.to_dataset(),
        lambda x: x.drop_vars("x"),
        lambda x: x.expand_dims(k=[1, 2, 3]),
        lambda x: x.expand_dims(k=3),
        lambda x: x.assign_coords(new_coord=("y", x.y * 2)),
        lambda x: x.astype(np.int32),
        lambda x: x.x,
    ],
)
def test_map_blocks_da_transformations(func, map_da):
    with raise_if_dask_computes():
        actual = xr.map_blocks(func, map_da)

    assert_identical(actual, func(map_da))


@pytest.mark.parametrize(
    "func",
    [
        lambda x: x,
        lambda x: x.drop_vars("cxy"),
        lambda x: x.drop_vars("a"),
        lambda x: x.drop_vars("x"),
        lambda x: x.expand_dims(k=[1, 2, 3]),
        lambda x: x.expand_dims(k=3),
        lambda x: x.rename({"a": "new1", "b": "new2"}),
        lambda x: x.x,
    ],
)
def test_map_blocks_ds_transformations(func, map_ds):
    with raise_if_dask_computes():
        actual = xr.map_blocks(func, map_ds)

    assert_identical(actual, func(map_ds))


@pytest.mark.parametrize("obj", [make_da(), make_ds()])
def test_map_blocks_da_ds_with_template(obj):
    func = lambda x: x.isel(x=[1])
    template = obj.isel(x=[1, 5, 9])
    with raise_if_dask_computes():
        actual = xr.map_blocks(func, obj, template=template)
    assert_identical(actual, template)

    with raise_if_dask_computes():
        actual = obj.map_blocks(func, template=template)
    assert_identical(actual, template)


@pytest.mark.parametrize("obj", [make_da(), make_ds()])
def test_map_blocks_errors_bad_template(obj):
    with raises_regex(ValueError, "unexpected coordinate variables"):
        xr.map_blocks(lambda x: x.assign_coords(a=10), obj, template=obj).compute()
    with raises_regex(ValueError, "does not contain coordinate variables"):
        xr.map_blocks(lambda x: x.drop_vars("cxy"), obj, template=obj).compute()
    with raises_regex(ValueError, "Dimensions {'x'} missing"):
        xr.map_blocks(lambda x: x.isel(x=1), obj, template=obj).compute()
    with raises_regex(ValueError, "Received dimension 'x' of length 1"):
        xr.map_blocks(lambda x: x.isel(x=[1]), obj, template=obj).compute()
    with raises_regex(TypeError, "must be a DataArray"):
        xr.map_blocks(lambda x: x.isel(x=[1]), obj, template=(obj,)).compute()
    with raises_regex(ValueError, "map_blocks requires that one block"):
        xr.map_blocks(
            lambda x: x.isel(x=[1]).assign_coords(x=10), obj, template=obj.isel(x=[1])
        ).compute()
    with raises_regex(ValueError, "Expected index 'x' to be"):
        xr.map_blocks(
            lambda a: a.isel(x=[1]).assign_coords(x=[120]),  # assign bad index values
            obj,
            template=obj.isel(x=[1, 5, 9]),
        ).compute()


def test_map_blocks_errors_bad_template_2(map_ds):
    with raises_regex(ValueError, "unexpected data variables {'xyz'}"):
        xr.map_blocks(lambda x: x.assign(xyz=1), map_ds, template=map_ds).compute()


@pytest.mark.parametrize("obj", [make_da(), make_ds()])
def test_map_blocks_object_method(obj):
    def func(obj):
        result = obj + obj.x + 5 * obj.y
        return result

    with raise_if_dask_computes():
        expected = xr.map_blocks(func, obj)
        actual = obj.map_blocks(func)

    assert_identical(expected, actual)


def test_map_blocks_hlg_layers():
    # regression test for #3599
    ds = xr.Dataset(
        {
            "x": (("a",), dask.array.ones(10, chunks=(5,))),
            "z": (("b",), dask.array.ones(10, chunks=(5,))),
        }
    )
    mapped = ds.map_blocks(lambda x: x)

    xr.testing.assert_equal(mapped, ds)


def test_make_meta(map_ds):
    from ..core.parallel import make_meta

    meta = make_meta(map_ds)

    for variable in map_ds._coord_names:
        assert variable in meta._coord_names
        assert meta.coords[variable].shape == (0,) * meta.coords[variable].ndim

    for variable in map_ds.data_vars:
        assert variable in meta.data_vars
        assert meta.data_vars[variable].shape == (0,) * meta.data_vars[variable].ndim


def test_identical_coords_no_computes():
    lons2 = xr.DataArray(da.zeros((10, 10), chunks=2), dims=("y", "x"))
    a = xr.DataArray(
        da.zeros((10, 10), chunks=2), dims=("y", "x"), coords={"lons": lons2}
    )
    b = xr.DataArray(
        da.zeros((10, 10), chunks=2), dims=("y", "x"), coords={"lons": lons2}
    )
    with raise_if_dask_computes():
        c = a + b
    assert_identical(c, a)


@pytest.mark.parametrize(
    "obj", [make_da(), make_da().compute(), make_ds(), make_ds().compute()]
)
@pytest.mark.parametrize(
    "transform",
    [
        lambda x: x.reset_coords(),
        lambda x: x.reset_coords(drop=True),
        lambda x: x.isel(x=1),
        lambda x: x.attrs.update(new_attrs=1),
        lambda x: x.assign_coords(cxy=1),
        lambda x: x.rename({"x": "xnew"}),
        lambda x: x.rename({"cxy": "cxynew"}),
    ],
)
def test_token_changes_on_transform(obj, transform):
    with raise_if_dask_computes():
        assert dask.base.tokenize(obj) != dask.base.tokenize(transform(obj))


@pytest.mark.parametrize(
    "obj", [make_da(), make_da().compute(), make_ds(), make_ds().compute()]
)
def test_token_changes_when_data_changes(obj):
    with raise_if_dask_computes():
        t1 = dask.base.tokenize(obj)

    # Change data_var
    if isinstance(obj, DataArray):
        obj *= 2
    else:
        obj["a"] *= 2
    with raise_if_dask_computes():
        t2 = dask.base.tokenize(obj)
    assert t2 != t1

    # Change non-index coord
    obj.coords["ndcoord"] *= 2
    with raise_if_dask_computes():
        t3 = dask.base.tokenize(obj)
    assert t3 != t2

    # Change IndexVariable
    obj = obj.assign_coords(x=obj.x * 2)
    with raise_if_dask_computes():
        t4 = dask.base.tokenize(obj)
    assert t4 != t3


@pytest.mark.parametrize("obj", [make_da().compute(), make_ds().compute()])
def test_token_changes_when_buffer_changes(obj):
    with raise_if_dask_computes():
        t1 = dask.base.tokenize(obj)

    if isinstance(obj, DataArray):
        obj[0, 0] = 123
    else:
        obj["a"][0, 0] = 123
    with raise_if_dask_computes():
        t2 = dask.base.tokenize(obj)
    assert t2 != t1

    obj.coords["ndcoord"][0] = 123
    with raise_if_dask_computes():
        t3 = dask.base.tokenize(obj)
    assert t3 != t2


@pytest.mark.parametrize(
    "transform",
    [lambda x: x, lambda x: x.copy(deep=False), lambda x: x.copy(deep=True)],
)
@pytest.mark.parametrize("obj", [make_da(), make_ds(), make_ds().variables["a"]])
def test_token_identical(obj, transform):
    with raise_if_dask_computes():
        assert dask.base.tokenize(obj) == dask.base.tokenize(transform(obj))
    assert dask.base.tokenize(obj.compute()) == dask.base.tokenize(
        transform(obj.compute())
    )


def test_recursive_token():
    """Test that tokenization is invoked recursively, and doesn't just rely on the
    output of str()
    """
    a = np.ones(10000)
    b = np.ones(10000)
    b[5000] = 2
    assert str(a) == str(b)
    assert dask.base.tokenize(a) != dask.base.tokenize(b)

    # Test DataArray and Variable
    da_a = DataArray(a)
    da_b = DataArray(b)
    assert dask.base.tokenize(da_a) != dask.base.tokenize(da_b)

    # Test Dataset
    ds_a = da_a.to_dataset(name="x")
    ds_b = da_b.to_dataset(name="x")
    assert dask.base.tokenize(ds_a) != dask.base.tokenize(ds_b)

    # Test IndexVariable
    da_a = DataArray(a, dims=["x"], coords={"x": a})
    da_b = DataArray(a, dims=["x"], coords={"x": b})
    assert dask.base.tokenize(da_a) != dask.base.tokenize(da_b)


@requires_scipy_or_netCDF4
def test_normalize_token_with_backend(map_ds):
    with create_tmp_file(allow_cleanup_failure=ON_WINDOWS) as tmp_file:
        map_ds.to_netcdf(tmp_file)
        read = xr.open_dataset(tmp_file)
        assert not dask.base.tokenize(map_ds) == dask.base.tokenize(read)
        read.close()


@pytest.mark.parametrize(
    "compat", ["broadcast_equals", "equals", "identical", "no_conflicts"]
)
def test_lazy_array_equiv_variables(compat):
    var1 = xr.Variable(("y", "x"), da.zeros((10, 10), chunks=2))
    var2 = xr.Variable(("y", "x"), da.zeros((10, 10), chunks=2))
    var3 = xr.Variable(("y", "x"), da.zeros((20, 10), chunks=2))

    with raise_if_dask_computes():
        assert getattr(var1, compat)(var2, equiv=lazy_array_equiv)
    # values are actually equal, but we don't know that till we compute, return None
    with raise_if_dask_computes():
        assert getattr(var1, compat)(var2 / 2, equiv=lazy_array_equiv) is None

    # shapes are not equal, return False without computes
    with raise_if_dask_computes():
        assert getattr(var1, compat)(var3, equiv=lazy_array_equiv) is False

    # if one or both arrays are numpy, return None
    assert getattr(var1, compat)(var2.compute(), equiv=lazy_array_equiv) is None
    assert (
        getattr(var1.compute(), compat)(var2.compute(), equiv=lazy_array_equiv) is None
    )

    with raise_if_dask_computes():
        assert getattr(var1, compat)(var2.transpose("y", "x"))


@pytest.mark.parametrize(
    "compat", ["broadcast_equals", "equals", "identical", "no_conflicts"]
)
def test_lazy_array_equiv_merge(compat):
    da1 = xr.DataArray(da.zeros((10, 10), chunks=2), dims=("y", "x"))
    da2 = xr.DataArray(da.zeros((10, 10), chunks=2), dims=("y", "x"))
    da3 = xr.DataArray(da.ones((20, 10), chunks=2), dims=("y", "x"))

    with raise_if_dask_computes():
        xr.merge([da1, da2], compat=compat)
    # shapes are not equal; no computes necessary
    with raise_if_dask_computes(max_computes=0):
        with pytest.raises(ValueError):
            xr.merge([da1, da3], compat=compat)
    with raise_if_dask_computes(max_computes=2):
        xr.merge([da1, da2 / 2], compat=compat)


@pytest.mark.filterwarnings("ignore::FutureWarning")  # transpose_coords
@pytest.mark.parametrize("obj", [make_da(), make_ds()])
@pytest.mark.parametrize(
    "transform",
    [
        lambda a: a.assign_attrs(new_attr="anew"),
        lambda a: a.assign_coords(cxy=a.cxy),
        lambda a: a.copy(),
        lambda a: a.isel(x=np.arange(a.sizes["x"])),
        lambda a: a.isel(x=slice(None)),
        lambda a: a.loc[dict(x=slice(None))],
        lambda a: a.loc[dict(x=np.arange(a.sizes["x"]))],
        lambda a: a.loc[dict(x=a.x)],
        lambda a: a.sel(x=a.x),
        lambda a: a.sel(x=a.x.values),
        lambda a: a.transpose(...),
        lambda a: a.squeeze(),  # no dimensions to squeeze
        lambda a: a.sortby("x"),  # "x" is already sorted
        lambda a: a.reindex(x=a.x),
        lambda a: a.reindex_like(a),
        lambda a: a.rename({"cxy": "cnew"}).rename({"cnew": "cxy"}),
        lambda a: a.pipe(lambda x: x),
        lambda a: xr.align(a, xr.zeros_like(a))[0],
        # assign
        # swap_dims
        # set_index / reset_index
    ],
)
def test_transforms_pass_lazy_array_equiv(obj, transform):
    with raise_if_dask_computes():
        assert_equal(obj, transform(obj))


def test_more_transforms_pass_lazy_array_equiv(map_da, map_ds):
    with raise_if_dask_computes():
        assert_equal(map_ds.cxy.broadcast_like(map_ds.cxy), map_ds.cxy)
        assert_equal(xr.broadcast(map_ds.cxy, map_ds.cxy)[0], map_ds.cxy)
        assert_equal(map_ds.map(lambda x: x), map_ds)
        assert_equal(map_ds.set_coords("a").reset_coords("a"), map_ds)
        assert_equal(map_ds.update({"a": map_ds.a}), map_ds)

        # fails because of index error
        # assert_equal(
        #     map_ds.rename_dims({"x": "xnew"}).rename_dims({"xnew": "x"}), map_ds
        # )

        assert_equal(
            map_ds.rename_vars({"cxy": "cnew"}).rename_vars({"cnew": "cxy"}), map_ds
        )

        assert_equal(map_da._from_temp_dataset(map_da._to_temp_dataset()), map_da)
        assert_equal(map_da.astype(map_da.dtype), map_da)
        assert_equal(map_da.transpose("y", "x", transpose_coords=False).cxy, map_da.cxy)
