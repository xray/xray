from numbers import Number

import numpy as np
import pytest

import xarray as xr
from xarray.backends.api import _get_default_engine

from . import (
    assert_identical,
    assert_no_warnings,
    requires_dask,
    requires_netCDF4,
    requires_scipy,
)


@requires_netCDF4
@requires_scipy
def test__get_default_engine() -> None:
    engine_remote = _get_default_engine("http://example.org/test.nc", allow_remote=True)
    assert engine_remote == "netcdf4"

    engine_gz = _get_default_engine("/example.gz")
    assert engine_gz == "scipy"

    engine_default = _get_default_engine("/example")
    assert engine_default == "netcdf4"


def test_custom_engine() -> None:
    expected = xr.Dataset(
        dict(a=2 * np.arange(5)), coords=dict(x=("x", np.arange(5), dict(units="s")))
    )

    class CustomBackend(xr.backends.BackendEntrypoint):
        def open_dataset(
            self,
            filename_or_obj,
            drop_variables=None,
            **kwargs,
        ) -> xr.Dataset:
            return expected.copy(deep=True)

    actual = xr.open_dataset("fake_filename", engine=CustomBackend)
    assert_identical(expected, actual)


class PassThroughBackendEntrypoint(xr.backends.BackendEntrypoint):
    """Access an object passed to the `open_dataset` method."""

    def open_dataset(self, dataset, *, drop_variables=None):
        """Return the first argument."""
        return dataset


def explicit_chunks(chunks, shape):
    """Return explicit chunks, expanding any integer member to a tuple of integers."""
    # Emulate `dask.array.core.normalize_chunks` but for simpler inputs.
    return tuple(
        (
            (size // chunk) * (chunk,)
            + ((size % chunk,) if size % chunk or size == 0 else ())
        )
        if isinstance(chunk, Number)
        else chunk
        for chunk, size in zip(chunks, shape)
    )


@requires_dask
class TestPreferredChunks:
    """Test behaviors related to the backend's preferred chunks."""

    var_name = "data"

    def create_dataset(self, shape, pref_chunks):
        """Return a dataset with a variable with the given shape and preferred chunks."""
        dims = tuple(f"dim_{idx}" for idx in range(len(shape)))
        return xr.Dataset(
            {
                self.var_name: xr.Variable(
                    dims,
                    np.empty(shape, dtype=np.dtype("V1")),
                    encoding={"preferred_chunks": dict(zip(dims, pref_chunks))},
                )
            }
        )

    def check_dataset(self, initial, final, expected_chunks):
        assert_identical(initial, final)
        assert final[self.var_name].chunks == expected_chunks

    @pytest.mark.parametrize(
        "shape,pref_chunks",
        [
            # Represent preferred chunking with int.
            ((5,), (2,)),
            # Represent preferred chunking with tuple.
            pytest.param(
                (5,),
                ((2, 2, 1),),
                marks=pytest.mark.xfail(raises=TypeError, strict=True),
            ),
            # Represent preferred chunking with int in two dims.
            ((5, 6), (4, 2)),
            # Represent preferred chunking with tuple in second dim.
            pytest.param(
                (5, 6),
                (4, (2, 2, 2)),
                marks=pytest.mark.xfail(raises=TypeError, strict=True),
            ),
        ],
    )
    @pytest.mark.parametrize("request_with_empty_map", [False, True])
    def test_honor_chunks(self, shape, pref_chunks, request_with_empty_map):
        """Honor the backend's preferred chunks when opening a dataset."""
        initial = self.create_dataset(shape, pref_chunks)
        # To keep the backend's preferred chunks, the `chunks` argument must be an
        # empty mapping or map dimensions to `None`.
        chunks = (
            {}
            if request_with_empty_map
            else dict.fromkeys(initial[self.var_name].dims, None)
        )
        final = xr.open_dataset(
            initial, engine=PassThroughBackendEntrypoint, chunks=chunks
        )
        self.check_dataset(initial, final, explicit_chunks(pref_chunks, shape))

    @pytest.mark.parametrize(
        "shape,pref_chunks,req_chunks",
        [
            # Preferred chunking is int; requested chunking is int.
            ((5,), (2,), (3,)),
            # Preferred chunking is int; requested chunking is tuple.
            ((5,), (2,), ((2, 1, 1, 1),)),
            # Preferred chunking is tuple; requested chunking is int.
            pytest.param(
                (5,),
                ((2, 2, 1),),
                (3,),
                marks=pytest.mark.xfail(raises=TypeError, strict=True),
            ),
            # Preferred chunking is tuple; requested chunking is tuple.
            pytest.param(
                (5,),
                ((2, 2, 1),),
                ((2, 1, 1, 1),),
                marks=pytest.mark.xfail(raises=TypeError, strict=True),
            ),
            # Split chunks along a dimension other than the first.
            ((1, 5), (1, 2), (1, 3)),
        ],
    )
    def test_split_chunks(self, shape, pref_chunks, req_chunks):
        """Warn when the requested chunks separate the backend's preferred chunks."""
        initial = self.create_dataset(shape, pref_chunks)
        with pytest.warns(UserWarning):
            final = xr.open_dataset(
                initial,
                engine=PassThroughBackendEntrypoint,
                chunks=dict(zip(initial[self.var_name].dims, req_chunks)),
            )
        self.check_dataset(initial, final, explicit_chunks(req_chunks, shape))

    @pytest.mark.parametrize(
        "shape,pref_chunks,req_chunks",
        [
            # Keep preferred chunks using int representation.
            ((5,), (2,), (2,)),
            # Keep preferred chunks using tuple representation.
            ((5,), (2,), ((2, 2, 1),)),
            # Join chunks, leaving a final short chunk.
            ((5,), (2,), (4,)),
            # Join all chunks with an int larger than the dimension size.
            ((5,), (2,), (6,)),
            # Join one chunk using tuple representation.
            ((5,), (1,), ((1, 1, 2, 1),)),
            # Join one chunk using int representation.
            pytest.param(
                (5,),
                ((1, 1, 2, 1),),
                (2,),
                marks=pytest.mark.xfail(raises=TypeError, strict=True),
            ),
            # Join multiple chunks using tuple representation.
            pytest.param(
                (5,),
                ((1, 1, 2, 1),),
                ((2, 3),),
                marks=pytest.mark.xfail(raises=TypeError, strict=True),
            ),
            # Join chunks in multiple dimensions.
            pytest.param(
                (5, 5),
                (2, (1, 1, 2, 1)),
                (4, (2, 3)),
                marks=pytest.mark.xfail(raises=TypeError, strict=True),
            ),
        ],
    )
    def test_join_chunks(self, shape, pref_chunks, req_chunks):
        """Don't warn when the requested chunks join or keep the preferred chunks."""
        initial = self.create_dataset(shape, pref_chunks)
        with assert_no_warnings():
            final = xr.open_dataset(
                initial,
                engine=PassThroughBackendEntrypoint,
                chunks=dict(zip(initial[self.var_name].dims, req_chunks)),
            )
        self.check_dataset(initial, final, explicit_chunks(req_chunks, shape))
