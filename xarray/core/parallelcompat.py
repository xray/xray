"""
The code in this module is an experiment in going from N=1 to N=2 parallel computing frameworks in xarray.
It could later be used as the basis for a public interface allowing any N frameworks to interoperate with xarray,
but for now it is just a private experiment.
"""
from __future__ import annotations

import functools
import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence
from importlib.metadata import EntryPoint, entry_points
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
)

import numpy as np

from xarray.core.pycompat import is_chunked_array

T_ChunkedArray = TypeVar("T_ChunkedArray")

# TODO importing TypeAlias is a pain on python 3.9 without typing_extensions in the CI
# T_Chunks: TypeAlias = tuple[tuple[int, ...], ...]
T_Chunks = Any


@functools.lru_cache(maxsize=1)
def list_chunkmanagers() -> dict[str, "ChunkManagerEntrypoint"]:
    """
    Return a dictionary of available chunk managers and their ChunkManagerEntrypoint objects.

    Notes
    -----
    # New selection mechanism introduced with Python 3.10. See GH6514.
    """
    if sys.version_info >= (3, 10):
        entrypoints = entry_points(group="xarray.chunkmanagers")
    else:
        entrypoints = entry_points().get("xarray.chunkmanagers", ())

    return load_chunkmanagers(entrypoints)


def load_chunkmanagers(
    entrypoints: Sequence[EntryPoint],
) -> dict[str, "ChunkManagerEntrypoint"]:
    """Load entrypoints and instantiate chunkmanagers only once."""

    loaded_entrypoints = {
        entrypoint.name: entrypoint.load() for entrypoint in entrypoints
    }

    available_chunkmanagers = {
        name: chunkmanager()
        for name, chunkmanager in loaded_entrypoints.items()
        if chunkmanager.available
    }
    return available_chunkmanagers


def guess_chunkmanager(
    manager: Union[str, "ChunkManagerEntrypoint", None]
) -> "ChunkManagerEntrypoint":
    """
    Get namespace of chunk-handling methods, guessing from what's available.

    If the name of a specific ChunkManager is given (e.g. "dask"), then use that.
    Else use whatever is installed, defaulting to dask if there are multiple options.
    """

    chunkmanagers = list_chunkmanagers()

    if manager is None:
        if len(chunkmanagers) == 1:
            # use the only option available
            manager = next(iter(chunkmanagers.keys()))
        else:
            # default to trying to use dask
            manager = "dask"

    if isinstance(manager, str):
        if manager not in chunkmanagers:
            raise ValueError(
                f"unrecognized chunk manager {manager} - must be one of: {list(chunkmanagers)}"
            )

        return chunkmanagers[manager]
    elif isinstance(manager, ChunkManagerEntrypoint):
        # already a valid ChunkManager so just pass through
        return manager
    else:
        raise TypeError(
            f"manager must be a string or instance of ChunkManagerEntryPoint, but received type {type(manager)}"
        )


def get_chunked_array_type(*args) -> "ChunkManagerEntrypoint":
    """
    Detects which parallel backend should be used for given set of arrays.

    Also checks that all arrays are of same chunking type (i.e. not a mix of cubed and dask).
    """

    # TODO this list is probably redundant with something inside xarray.apply_ufunc
    ALLOWED_NON_CHUNKED_TYPES = {int, float, np.ndarray}

    chunked_arrays = [
        a
        for a in args
        if is_chunked_array(a) and type(a) not in ALLOWED_NON_CHUNKED_TYPES
    ]

    # Asserts all arrays are the same type (or numpy etc.)
    chunked_array_types = {type(a) for a in chunked_arrays}
    if len(chunked_array_types) > 1:
        raise TypeError(
            f"Mixing chunked array types is not supported, but received multiple types: {chunked_array_types}"
        )
    elif len(chunked_array_types) == 0:
        raise TypeError("Expected a chunked array but none were found")

    # iterate over defined chunk managers, seeing if each recognises this array type
    chunked_arr = chunked_arrays[0]
    chunkmanagers = list_chunkmanagers()
    for chunkmanager in chunkmanagers.values():
        if chunkmanager.is_chunked_array(chunked_arr):
            return chunkmanager

    raise TypeError(
        f"Could not find a Chunk Manager which recognises type {type(chunked_arr)}"
    )


class ChunkManagerEntrypoint(ABC, Generic[T_ChunkedArray]):
    """
    Adapter between a particular parallel computing framework and xarray.

    Attributes
    ----------
    array_cls
        Type of the array class this parallel computing framework provides.

        Parallel frameworks need to provide an array class that supports the array API standard.
        Used for type checking.
    """

    array_cls: type[T_ChunkedArray]
    available: bool = True

    @abstractmethod
    def __init__(self):
        ...

    def is_chunked_array(self, data: Any) -> bool:
        return isinstance(data, self.array_cls)

    @abstractmethod
    def chunks(self, data: T_ChunkedArray) -> T_Chunks:
        ...

    @abstractmethod
    def normalize_chunks(
        self,
        chunks: Union[tuple, int, dict, str],
        shape: Union[tuple[int], None] = None,
        limit: Union[int, None] = None,
        dtype: Union[np.dtype, None] = None,
        previous_chunks: Union[tuple[tuple[int, ...], ...], None] = None,
    ) -> tuple[tuple[int, ...], ...]:
        """Called by open_dataset"""
        ...

    @abstractmethod
    def from_array(
        self, data: np.ndarray, chunks: T_Chunks, **kwargs
    ) -> T_ChunkedArray:
        """Called when .chunk is called on an xarray object that is not already chunked."""
        ...

    def rechunk(
        self, data: T_ChunkedArray, chunks: T_Chunks, **kwargs
    ) -> T_ChunkedArray:
        """Called when .chunk is called on an xarray object that is already chunked."""
        return data.rechunk(chunks, **kwargs)  # type: ignore[attr-defined]

    @abstractmethod
    def compute(self, data: T_ChunkedArray, **kwargs) -> np.ndarray:
        ...

    @property
    def array_api(self) -> Any:
        """Return the array_api namespace following the python array API standard."""
        raise NotImplementedError()

    def reduction(
        self,
        arr: T_ChunkedArray,
        func: Callable,
        combine_func: Optional[Callable] = None,
        aggregate_func: Optional[Callable] = None,
        axis: Optional[Union[int, Sequence[int]]] = None,
        dtype: Optional[np.dtype] = None,
        keepdims: bool = False,
    ) -> T_ChunkedArray:
        """Used in some reductions like nanfirst, which is used by groupby.first"""
        raise NotImplementedError()

    @abstractmethod
    def apply_gufunc(
        self,
        func,
        signature,
        *args,
        axes=None,
        keepdims=False,
        output_dtypes=None,
        vectorize=None,
        **kwargs,
    ):
        """
        Called inside xarray.apply_ufunc, so must be supplied for vast majority of xarray computations to be supported.
        """
        ...

    def map_blocks(
        self,
        func,
        *args,
        dtype=None,
        chunks=None,
        drop_axis=[],
        new_axis=None,
        **kwargs,
    ):
        """Currently only called in a couple of really niche places in xarray. Not even called in xarray.map_blocks."""
        raise NotImplementedError()

    def blockwise(
        self,
        func,
        out_ind,
        *args,
        adjust_chunks=None,
        new_axes=None,
        align_arrays=True,
        **kwargs,
    ):
        """Called by some niche functions in xarray."""
        raise NotImplementedError()

    def unify_chunks(
        self, *args, **kwargs
    ) -> tuple[dict[str, T_Chunks], list[T_ChunkedArray]]:
        """Called by xr.unify_chunks."""
        raise NotImplementedError()

    def store(
        self,
        sources: Union[T_ChunkedArray, Sequence[T_ChunkedArray]],
        targets: Any,
        **kwargs: dict[str, Any],
    ):
        """Used when writing to any backend."""
        raise NotImplementedError()
