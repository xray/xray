"""Mixin classes with reduction operations."""
# This file was generated using xarray.util.generate_reductions. Do not edit manually.

import sys
from typing import Any, Callable, Hashable, Mapping, Optional, Sequence, Union

from . import duck_array_ops
from .options import OPTIONS
from .types import T_DataArray, T_Dataset
from .utils import contains_only_dask_or_numpy

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol


try:
    import dask_groupby
except ImportError:
    dask_groupby = None


class DatasetReduce(Protocol):
    def reduce(
        self,
        func: Callable[..., Any],
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        axis: Union[None, int, Sequence[int]] = None,
        keep_attrs: bool = None,
        keepdims: bool = False,
        **kwargs: Any,
    ) -> T_Dataset:
        ...


class DatasetGroupByReduce(Protocol):
    _obj: T_Dataset
    _dask_groupby_kwargs: Mapping

    def reduce(
        self,
        func: Callable[..., Any],
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        axis: Union[None, int, Sequence[int]] = None,
        keep_attrs: bool = None,
        keepdims: bool = False,
        **kwargs: Any,
    ) -> T_Dataset:
        ...

    def _dask_groupby_reduce(
        self,
        dim: Union[None, Hashable, Sequence[Hashable]],
        **kwargs,
    ) -> T_Dataset:
        ...


class DataArrayReduce(Protocol):
    def reduce(
        self,
        func: Callable[..., Any],
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        axis: Union[None, int, Sequence[int]] = None,
        keep_attrs: bool = None,
        keepdims: bool = False,
        **kwargs: Any,
    ) -> T_DataArray:
        ...


class DataArrayGroupByReduce(Protocol):
    _obj: T_DataArray
    _dask_groupby_kwargs: Mapping

    def reduce(
        self,
        func: Callable[..., Any],
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        axis: Union[None, int, Sequence[int]] = None,
        keep_attrs: bool = None,
        keepdims: bool = False,
        **kwargs: Any,
    ) -> T_DataArray:
        ...

    def _dask_groupby_reduce(
        self,
        dim: Union[None, Hashable, Sequence[Hashable]],
        **kwargs,
    ) -> T_DataArray:
        ...


class DatasetReductions:
    __slots__ = ()

    def count(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``count`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``count``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``count`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``count`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.count
        dask.array.count
        DataArray.count
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.count()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       int64 5
        """
        return self.reduce(
            duck_array_ops.count,
            dim=dim,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def all(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``all`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``all``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``all`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``all`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.all
        dask.array.all
        DataArray.all
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) bool True True True True True False

        >>> ds.all()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       bool False
        """
        return self.reduce(
            duck_array_ops.array_all,
            dim=dim,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def any(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``any`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``any``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``any`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``any`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.any
        dask.array.any
        DataArray.any
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) bool True True True True True False

        >>> ds.any()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       bool True
        """
        return self.reduce(
            duck_array_ops.array_any,
            dim=dim,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def max(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``max`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``max``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``max`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``max`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.max
        dask.array.max
        DataArray.max
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.max()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 3.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.max(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan
        """
        return self.reduce(
            duck_array_ops.max,
            dim=dim,
            skipna=skipna,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def min(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``min`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``min``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``min`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``min`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.min
        dask.array.min
        DataArray.min
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.min()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 1.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.min(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan
        """
        return self.reduce(
            duck_array_ops.min,
            dim=dim,
            skipna=skipna,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def mean(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``mean`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``mean``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``mean`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``mean`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.mean
        dask.array.mean
        DataArray.mean
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.mean()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 1.8

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.mean(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan
        """
        return self.reduce(
            duck_array_ops.mean,
            dim=dim,
            skipna=skipna,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def prod(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``prod`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``prod``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``prod`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``prod`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.prod
        dask.array.prod
        DataArray.prod
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.prod()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 12.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.prod(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> ds.prod(skipna=True, min_count=2)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 12.0
        """
        return self.reduce(
            duck_array_ops.prod,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def sum(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``sum`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``sum``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``sum`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``sum`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.sum
        dask.array.sum
        DataArray.sum
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.sum()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 9.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.sum(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> ds.sum(skipna=True, min_count=2)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 9.0
        """
        return self.reduce(
            duck_array_ops.sum,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def std(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``std`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``std``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``std`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``std`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.std
        dask.array.std
        DataArray.std
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.std()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 0.7483

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.std(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan

        Specify ``ddof=1`` for an unbiased estimate.

        >>> ds.std(skipna=True, ddof=1)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 0.8367
        """
        return self.reduce(
            duck_array_ops.std,
            dim=dim,
            skipna=skipna,
            ddof=ddof,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def var(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``var`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``var``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``var`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``var`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.var
        dask.array.var
        DataArray.var
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.var()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 0.56

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.var(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan

        Specify ``ddof=1`` for an unbiased estimate.

        >>> ds.var(skipna=True, ddof=1)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 0.7
        """
        return self.reduce(
            duck_array_ops.var,
            dim=dim,
            skipna=skipna,
            ddof=ddof,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def median(
        self: DatasetReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``median`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``median``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``median`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``median`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.median
        dask.array.median
        DataArray.median
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.median()
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.median(skipna=False)
        <xarray.Dataset>
        Dimensions:  ()
        Data variables:
            da       float64 nan
        """
        return self.reduce(
            duck_array_ops.median,
            dim=dim,
            skipna=skipna,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )


class DataArrayReductions:
    __slots__ = ()

    def count(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``count`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``count``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``count`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``count`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.count
        dask.array.count
        Dataset.count
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.count()
        <xarray.DataArray ()>
        array(5)
        """
        return self.reduce(
            duck_array_ops.count,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def all(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``all`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``all``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``all`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``all`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.all
        dask.array.all
        Dataset.all
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ True,  True,  True,  True,  True, False])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.all()
        <xarray.DataArray ()>
        array(False)
        """
        return self.reduce(
            duck_array_ops.array_all,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def any(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``any`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``any``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``any`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``any`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.any
        dask.array.any
        Dataset.any
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ True,  True,  True,  True,  True, False])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.any()
        <xarray.DataArray ()>
        array(True)
        """
        return self.reduce(
            duck_array_ops.array_any,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def max(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``max`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``max``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``max`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``max`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.max
        dask.array.max
        Dataset.max
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.max()
        <xarray.DataArray ()>
        array(3.)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.max(skipna=False)
        <xarray.DataArray ()>
        array(nan)
        """
        return self.reduce(
            duck_array_ops.max,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def min(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``min`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``min``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``min`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``min`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.min
        dask.array.min
        Dataset.min
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.min()
        <xarray.DataArray ()>
        array(1.)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.min(skipna=False)
        <xarray.DataArray ()>
        array(nan)
        """
        return self.reduce(
            duck_array_ops.min,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def mean(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``mean`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``mean``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``mean`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``mean`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.mean
        dask.array.mean
        Dataset.mean
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.mean()
        <xarray.DataArray ()>
        array(1.8)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.mean(skipna=False)
        <xarray.DataArray ()>
        array(nan)
        """
        return self.reduce(
            duck_array_ops.mean,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def prod(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``prod`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``prod``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``prod`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``prod`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.prod
        dask.array.prod
        Dataset.prod
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.prod()
        <xarray.DataArray ()>
        array(12.)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.prod(skipna=False)
        <xarray.DataArray ()>
        array(nan)

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> da.prod(skipna=True, min_count=2)
        <xarray.DataArray ()>
        array(12.)
        """
        return self.reduce(
            duck_array_ops.prod,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def sum(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``sum`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``sum``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``sum`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``sum`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.sum
        dask.array.sum
        Dataset.sum
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.sum()
        <xarray.DataArray ()>
        array(9.)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.sum(skipna=False)
        <xarray.DataArray ()>
        array(nan)

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> da.sum(skipna=True, min_count=2)
        <xarray.DataArray ()>
        array(9.)
        """
        return self.reduce(
            duck_array_ops.sum,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def std(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``std`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``std``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``std`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``std`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.std
        dask.array.std
        Dataset.std
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.std()
        <xarray.DataArray ()>
        array(0.74833148)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.std(skipna=False)
        <xarray.DataArray ()>
        array(nan)

        Specify ``ddof=1`` for an unbiased estimate.

        >>> da.std(skipna=True, ddof=1)
        <xarray.DataArray ()>
        array(0.83666003)
        """
        return self.reduce(
            duck_array_ops.std,
            dim=dim,
            skipna=skipna,
            ddof=ddof,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def var(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``var`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``var``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``var`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``var`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.var
        dask.array.var
        Dataset.var
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.var()
        <xarray.DataArray ()>
        array(0.56)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.var(skipna=False)
        <xarray.DataArray ()>
        array(nan)

        Specify ``ddof=1`` for an unbiased estimate.

        >>> da.var(skipna=True, ddof=1)
        <xarray.DataArray ()>
        array(0.7)
        """
        return self.reduce(
            duck_array_ops.var,
            dim=dim,
            skipna=skipna,
            ddof=ddof,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def median(
        self: DataArrayReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``median`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``median``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``median`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``median`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.median
        dask.array.median
        Dataset.median
        :ref:`agg`
            User guide on reduction or aggregation operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.median()
        <xarray.DataArray ()>
        array(2.)

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.median(skipna=False)
        <xarray.DataArray ()>
        array(nan)
        """
        return self.reduce(
            duck_array_ops.median,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )


class DatasetGroupByReductions:
    __slots__ = ()

    def count(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``count`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``count``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``count`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``count`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.count
        dask.array.count
        Dataset.count
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").count()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) int64 1 2 2
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="count",
                dim=dim,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.count,
                dim=dim,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def all(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``all`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``all``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``all`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``all`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.all
        dask.array.all
        Dataset.all
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) bool True True True True True False

        >>> ds.groupby("labels").all()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) bool False True True
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="all",
                dim=dim,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.array_all,
                dim=dim,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def any(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``any`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``any``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``any`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``any`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.any
        dask.array.any
        Dataset.any
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) bool True True True True True False

        >>> ds.groupby("labels").any()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) bool True True True
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="any",
                dim=dim,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.array_any,
                dim=dim,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def max(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``max`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``max``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``max`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``max`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.max
        dask.array.max
        Dataset.max
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").max()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 1.0 2.0 3.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").max(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 2.0 3.0
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="max",
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.max,
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def min(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``min`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``min``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``min`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``min`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.min
        dask.array.min
        Dataset.min
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").min()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 1.0 2.0 1.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").min(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 2.0 1.0
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="min",
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.min,
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def mean(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``mean`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``mean``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``mean`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``mean`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.mean
        dask.array.mean
        Dataset.mean
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").mean()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 1.0 2.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").mean(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 2.0 2.0
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="mean",
                dim=dim,
                skipna=skipna,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.mean,
                dim=dim,
                skipna=skipna,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def prod(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``prod`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``prod``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``prod`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``prod`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.prod
        dask.array.prod
        Dataset.prod
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").prod()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 1.0 4.0 3.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").prod(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 4.0 3.0

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> ds.groupby("labels").prod(skipna=True, min_count=2)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 4.0 3.0
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="prod",
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.prod,
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def sum(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``sum`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``sum``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``sum`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``sum`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.sum
        dask.array.sum
        Dataset.sum
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").sum()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 1.0 4.0 4.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").sum(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 4.0 4.0

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> ds.groupby("labels").sum(skipna=True, min_count=2)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 4.0 4.0
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="sum",
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.sum,
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def std(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``std`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``std``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``std`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``std`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.std
        dask.array.std
        Dataset.std
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").std()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 0.0 0.0 1.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").std(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 0.0 1.0

        Specify ``ddof=1`` for an unbiased estimate.

        >>> ds.groupby("labels").std(skipna=True, ddof=1)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 0.0 1.414
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="std",
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.std,
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def var(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``var`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``var``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``var`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``var`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.var
        dask.array.var
        Dataset.var
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").var()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 0.0 0.0 1.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").var(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 0.0 1.0

        Specify ``ddof=1`` for an unbiased estimate.

        >>> ds.groupby("labels").var(skipna=True, ddof=1)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 0.0 2.0
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="var",
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.var,
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def median(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``median`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``median``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``median`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``median`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.median
        dask.array.median
        Dataset.median
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.groupby("labels").median()
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 1.0 2.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.groupby("labels").median(skipna=False)
        <xarray.Dataset>
        Dimensions:  (labels: 3)
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        Data variables:
            da       (labels) float64 nan 2.0 2.0
        """
        return self.reduce(
            duck_array_ops.median,
            dim=dim,
            skipna=skipna,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )


class DatasetResampleReductions:
    __slots__ = ()

    def count(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``count`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``count``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``count`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``count`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.count
        dask.array.count
        Dataset.count
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").count()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) int64 1 3 1
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="count",
                dim=dim,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.count,
                dim=dim,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def all(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``all`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``all``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``all`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``all`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.all
        dask.array.all
        Dataset.all
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) bool True True True True True False

        >>> ds.resample(time="3M").all()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) bool True True False
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="all",
                dim=dim,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.array_all,
                dim=dim,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def any(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``any`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``any``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``any`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``any`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.any
        dask.array.any
        Dataset.any
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) bool True True True True True False

        >>> ds.resample(time="3M").any()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) bool True True True
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="any",
                dim=dim,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.array_any,
                dim=dim,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def max(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``max`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``max``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``max`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``max`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.max
        dask.array.max
        Dataset.max
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").max()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 3.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").max(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 3.0 nan
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="max",
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.max,
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def min(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``min`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``min``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``min`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``min`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.min
        dask.array.min
        Dataset.min
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").min()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 1.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").min(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 1.0 nan
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="min",
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.min,
                dim=dim,
                skipna=skipna,
                numeric_only=False,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def mean(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``mean`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``mean``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``mean`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``mean`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.mean
        dask.array.mean
        Dataset.mean
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").mean()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 2.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").mean(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 2.0 nan
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="mean",
                dim=dim,
                skipna=skipna,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.mean,
                dim=dim,
                skipna=skipna,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def prod(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``prod`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``prod``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``prod`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``prod`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.prod
        dask.array.prod
        Dataset.prod
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").prod()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 6.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").prod(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 6.0 nan

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> ds.resample(time="3M").prod(skipna=True, min_count=2)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 nan 6.0 nan
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="prod",
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.prod,
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def sum(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``sum`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``sum``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``sum`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``sum`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.sum
        dask.array.sum
        Dataset.sum
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").sum()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 6.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").sum(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 6.0 nan

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> ds.resample(time="3M").sum(skipna=True, min_count=2)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 nan 6.0 nan
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="sum",
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.sum,
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def std(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``std`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``std``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``std`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``std`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.std
        dask.array.std
        Dataset.std
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").std()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 0.0 0.8165 0.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").std(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 0.0 0.8165 nan

        Specify ``ddof=1`` for an unbiased estimate.

        >>> ds.resample(time="3M").std(skipna=True, ddof=1)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 nan 1.0 nan
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="std",
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.std,
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def var(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``var`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``var``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``var`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``var`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.var
        dask.array.var
        Dataset.var
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").var()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 0.0 0.6667 0.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").var(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 0.0 0.6667 nan

        Specify ``ddof=1`` for an unbiased estimate.

        >>> ds.resample(time="3M").var(skipna=True, ddof=1)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 nan 1.0 nan
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="var",
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.var,
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                numeric_only=True,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def median(
        self: DatasetGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_Dataset:
        """
        Reduce this Dataset's data by applying ``median`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``median``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``median`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : Dataset
            New Dataset with ``median`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.median
        dask.array.median
        Dataset.median
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds
        <xarray.Dataset>
        Dimensions:  (time: 6)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'
        Data variables:
            da       (time) float64 1.0 2.0 3.0 1.0 2.0 nan

        >>> ds.resample(time="3M").median()
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 2.0 2.0

        Use ``skipna`` to control whether NaNs are ignored.

        >>> ds.resample(time="3M").median(skipna=False)
        <xarray.Dataset>
        Dimensions:  (time: 3)
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        Data variables:
            da       (time) float64 1.0 2.0 nan
        """
        return self.reduce(
            duck_array_ops.median,
            dim=dim,
            skipna=skipna,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )


class DataArrayGroupByReductions:
    __slots__ = ()

    def count(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``count`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``count``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``count`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``count`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.count
        dask.array.count
        DataArray.count
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").count()
        <xarray.DataArray (labels: 3)>
        array([1, 2, 2])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="count",
                dim=dim,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.count,
                dim=dim,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def all(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``all`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``all``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``all`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``all`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.all
        dask.array.all
        DataArray.all
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ True,  True,  True,  True,  True, False])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").all()
        <xarray.DataArray (labels: 3)>
        array([False,  True,  True])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="all",
                dim=dim,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.array_all,
                dim=dim,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def any(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``any`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``any``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``any`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``any`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.any
        dask.array.any
        DataArray.any
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ True,  True,  True,  True,  True, False])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").any()
        <xarray.DataArray (labels: 3)>
        array([ True,  True,  True])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="any",
                dim=dim,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.array_any,
                dim=dim,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def max(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``max`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``max``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``max`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``max`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.max
        dask.array.max
        DataArray.max
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").max()
        <xarray.DataArray (labels: 3)>
        array([1., 2., 3.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").max(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  2.,  3.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="max",
                dim=dim,
                skipna=skipna,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.max,
                dim=dim,
                skipna=skipna,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def min(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``min`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``min``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``min`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``min`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.min
        dask.array.min
        DataArray.min
        :ref:`groupby`
            User guide on groupby operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").min()
        <xarray.DataArray (labels: 3)>
        array([1., 2., 1.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").min(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  2.,  1.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="min",
                dim=dim,
                skipna=skipna,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.min,
                dim=dim,
                skipna=skipna,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def mean(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``mean`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``mean``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``mean`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``mean`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.mean
        dask.array.mean
        DataArray.mean
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").mean()
        <xarray.DataArray (labels: 3)>
        array([1., 2., 2.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").mean(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  2.,  2.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="mean",
                dim=dim,
                skipna=skipna,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.mean,
                dim=dim,
                skipna=skipna,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def prod(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``prod`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``prod``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``prod`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``prod`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.prod
        dask.array.prod
        DataArray.prod
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").prod()
        <xarray.DataArray (labels: 3)>
        array([1., 4., 3.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").prod(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  4.,  3.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> da.groupby("labels").prod(skipna=True, min_count=2)
        <xarray.DataArray (labels: 3)>
        array([nan,  4.,  3.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="prod",
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.prod,
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def sum(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``sum`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``sum``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``sum`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``sum`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.sum
        dask.array.sum
        DataArray.sum
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").sum()
        <xarray.DataArray (labels: 3)>
        array([1., 4., 4.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").sum(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  4.,  4.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> da.groupby("labels").sum(skipna=True, min_count=2)
        <xarray.DataArray (labels: 3)>
        array([nan,  4.,  4.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="sum",
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.sum,
                dim=dim,
                skipna=skipna,
                min_count=min_count,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def std(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``std`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``std``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``std`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``std`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.std
        dask.array.std
        DataArray.std
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").std()
        <xarray.DataArray (labels: 3)>
        array([0., 0., 1.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").std(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  0.,  1.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Specify ``ddof=1`` for an unbiased estimate.

        >>> da.groupby("labels").std(skipna=True, ddof=1)
        <xarray.DataArray (labels: 3)>
        array([       nan, 0.        , 1.41421356])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="std",
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.std,
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def var(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``var`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``var``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``var`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``var`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.var
        dask.array.var
        DataArray.var
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").var()
        <xarray.DataArray (labels: 3)>
        array([0., 0., 1.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").var(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  0.,  1.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Specify ``ddof=1`` for an unbiased estimate.

        >>> da.groupby("labels").var(skipna=True, ddof=1)
        <xarray.DataArray (labels: 3)>
        array([nan,  0.,  2.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """

        if (
            dask_groupby
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._dask_groupby_reduce(
                func="var",
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.var,
                dim=dim,
                skipna=skipna,
                ddof=ddof,
                keep_attrs=keep_attrs,
                **kwargs,
            )

    def median(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``median`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``median``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``median`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``median`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.median
        dask.array.median
        DataArray.median
        :ref:`groupby`
            User guide on groupby operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.groupby("labels").median()
        <xarray.DataArray (labels: 3)>
        array([1., 2., 2.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.groupby("labels").median(skipna=False)
        <xarray.DataArray (labels: 3)>
        array([nan,  2.,  2.])
        Coordinates:
          * labels   (labels) object 'a' 'b' 'c'
        """
        return self.reduce(
            duck_array_ops.median,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )


class DataArrayResampleReductions:
    __slots__ = ()

    def count(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``count`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``count``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``count`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``count`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.count
        dask.array.count
        DataArray.count
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").count()
        <xarray.DataArray (time: 3)>
        array([1, 3, 1])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.count,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def all(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``all`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``all``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``all`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``all`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.all
        dask.array.all
        DataArray.all
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ True,  True,  True,  True,  True, False])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").all()
        <xarray.DataArray (time: 3)>
        array([ True,  True, False])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.array_all,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def any(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``any`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``any``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``any`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``any`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.any
        dask.array.any
        DataArray.any
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ True,  True,  True,  True,  True, False])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").any()
        <xarray.DataArray (time: 3)>
        array([ True,  True,  True])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.array_any,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def max(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``max`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``max``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``max`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``max`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.max
        dask.array.max
        DataArray.max
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").max()
        <xarray.DataArray (time: 3)>
        array([1., 3., 2.])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").max(skipna=False)
        <xarray.DataArray (time: 3)>
        array([ 1.,  3., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.max,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def min(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``min`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``min``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``min`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``min`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.min
        dask.array.min
        DataArray.min
        :ref:`resampling`
            User guide on resampling operations.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").min()
        <xarray.DataArray (time: 3)>
        array([1., 1., 2.])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").min(skipna=False)
        <xarray.DataArray (time: 3)>
        array([ 1.,  1., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.min,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def mean(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``mean`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``mean``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``mean`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``mean`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.mean
        dask.array.mean
        DataArray.mean
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").mean()
        <xarray.DataArray (time: 3)>
        array([1., 2., 2.])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").mean(skipna=False)
        <xarray.DataArray (time: 3)>
        array([ 1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.mean,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def prod(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``prod`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``prod``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``prod`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``prod`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.prod
        dask.array.prod
        DataArray.prod
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").prod()
        <xarray.DataArray (time: 3)>
        array([1., 6., 2.])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").prod(skipna=False)
        <xarray.DataArray (time: 3)>
        array([ 1.,  6., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> da.resample(time="3M").prod(skipna=True, min_count=2)
        <xarray.DataArray (time: 3)>
        array([nan,  6., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.prod,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def sum(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        min_count: Optional[int] = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``sum`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``sum``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``sum`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``sum`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.sum
        dask.array.sum
        DataArray.sum
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").sum()
        <xarray.DataArray (time: 3)>
        array([1., 6., 2.])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").sum(skipna=False)
        <xarray.DataArray (time: 3)>
        array([ 1.,  6., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> da.resample(time="3M").sum(skipna=True, min_count=2)
        <xarray.DataArray (time: 3)>
        array([nan,  6., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.sum,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def std(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``std`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``std``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``std`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``std`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.std
        dask.array.std
        DataArray.std
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").std()
        <xarray.DataArray (time: 3)>
        array([0.        , 0.81649658, 0.        ])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").std(skipna=False)
        <xarray.DataArray (time: 3)>
        array([0.        , 0.81649658,        nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Specify ``ddof=1`` for an unbiased estimate.

        >>> da.resample(time="3M").std(skipna=True, ddof=1)
        <xarray.DataArray (time: 3)>
        array([nan,  1., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.std,
            dim=dim,
            skipna=skipna,
            ddof=ddof,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def var(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        ddof: int = 0,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``var`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``var``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        ddof : int, default: 0
            “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
            where ``N`` represents the number of elements.
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``var`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``var`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.var
        dask.array.var
        DataArray.var
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").var()
        <xarray.DataArray (time: 3)>
        array([0.        , 0.66666667, 0.        ])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").var(skipna=False)
        <xarray.DataArray (time: 3)>
        array([0.        , 0.66666667,        nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Specify ``ddof=1`` for an unbiased estimate.

        >>> da.resample(time="3M").var(skipna=True, ddof=1)
        <xarray.DataArray (time: 3)>
        array([nan,  1., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.var,
            dim=dim,
            skipna=skipna,
            ddof=ddof,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def median(
        self: DataArrayGroupByReduce,
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        skipna: bool = None,
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_DataArray:
        """
        Reduce this DataArray's data by applying ``median`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``median``. For e.g. ``dim="x"``
            or ``dim=["x", "y"]``. If None, will reduce over all dimensions.
        skipna : bool, default: None
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or ``skipna=True`` has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``median`` on this object's data.
            These could include dask-specific kwargs like ``split_every``.

        Returns
        -------
        reduced : DataArray
            New DataArray with ``median`` applied to its data and the
            indicated dimension(s) removed

        See Also
        --------
        numpy.median
        dask.array.median
        DataArray.median
        :ref:`resampling`
            User guide on resampling operations.

        Notes
        -----
        Non-numeric variables will be removed prior to reducing.

        Examples
        --------
        >>> da = xr.DataArray(
        ...     np.array([1, 2, 3, 1, 2, np.nan]),
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )
        >>> da
        <xarray.DataArray (time: 6)>
        array([ 1.,  2.,  3.,  1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-06-30
            labels   (time) <U1 'a' 'b' 'c' 'c' 'b' 'a'

        >>> da.resample(time="3M").median()
        <xarray.DataArray (time: 3)>
        array([1., 2., 2.])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31

        Use ``skipna`` to control whether NaNs are ignored.

        >>> da.resample(time="3M").median(skipna=False)
        <xarray.DataArray (time: 3)>
        array([ 1.,  2., nan])
        Coordinates:
          * time     (time) datetime64[ns] 2001-01-31 2001-04-30 2001-07-31
        """
        return self.reduce(
            duck_array_ops.median,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )
