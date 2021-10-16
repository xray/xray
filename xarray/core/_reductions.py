"""Mixin classes with reduction operations."""
# This file was generated using xarray.util.generate_reductions. Do not edit manually.

from . import duck_array_ops


class DatasetGroupByReductions:
    __slots__ = ()

    def count(self, dim=None, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `count` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `count` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `count` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.count,
            dim=dim,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def all(self, dim=None, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `all` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `all` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `all` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.array_all,
            dim=dim,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def any(self, dim=None, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `any` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `any` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `any` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.array_any,
            dim=dim,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def max(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `max` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `max` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `max` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.max,
            dim=dim,
            skipna=skipna,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def min(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `min` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `min` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `min` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.min,
            dim=dim,
            skipna=skipna,
            numeric_only=False,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def mean(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `mean` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `mean` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `mean` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.mean,
            dim=dim,
            skipna=skipna,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def prod(self, dim=None, skipna=True, min_count=None, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `prod` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `prod` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `prod` applied to its data and the
            indicated dimension(s) removed
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

    def sum(self, dim=None, skipna=True, min_count=None, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `sum` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `sum` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `sum` applied to its data and the
            indicated dimension(s) removed
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

    def std(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `std` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `std` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `std` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.std,
            dim=dim,
            skipna=skipna,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def var(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `var` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `var` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `var` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.var,
            dim=dim,
            skipna=skipna,
            numeric_only=True,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def median(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this Dataset's data by applying `median` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `median` on this object's data.

        Returns
        -------
        reduced : Dataset
            New Dataset with `median` applied to its data and the
            indicated dimension(s) removed
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

    def count(self, dim=None, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `count` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `count` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `count` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.count,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def all(self, dim=None, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `all` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `all` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `all` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.array_all,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def any(self, dim=None, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `any` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `any` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `any` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.array_any,
            dim=dim,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def max(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `max` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `max` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `max` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.max,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def min(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `min` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `min` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `min` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.min,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def mean(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `mean` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `mean` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `mean` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.mean,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def prod(self, dim=None, skipna=True, min_count=None, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `prod` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `prod` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `prod` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.prod,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def sum(self, dim=None, skipna=True, min_count=None, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `sum` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        min_count : int, default: None
            The required number of valid values to perform the operation. If
            fewer than min_count non-NA values are present the result will be
            NA. Only used if skipna is set to True or defaults to True for the
            array's dtype. Changed in version 0.17.0: if specified on an integer
            array and skipna=True, the result will be a float array.
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `sum` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `sum` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.sum,
            dim=dim,
            skipna=skipna,
            min_count=min_count,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def std(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `std` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `std` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `std` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.std,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def var(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `var` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `var` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `var` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.var,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )

    def median(self, dim=None, skipna=True, keep_attrs=None, **kwargs):
        """
        Reduce this DataArray's data by applying `median` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional

        skipna : bool, optional
            If True, skip missing values (as marked by NaN). By default, only
            skips missing values for float dtypes; other dtypes either do not
            have a sentinel missing value (int) or skipna=True has not been
            implemented (object, datetime64 or timedelta64).
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `median` on this object's data.

        Returns
        -------
        reduced : DataArray
            New DataArray with `median` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.median,
            dim=dim,
            skipna=skipna,
            keep_attrs=keep_attrs,
            **kwargs,
        )
