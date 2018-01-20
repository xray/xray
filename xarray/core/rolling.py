from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import numpy as np
import warnings
from distutils.version import LooseVersion

from .pycompat import OrderedDict, zip, dask_array_type
from .common import full_like
from .ops import (inject_bottleneck_rolling_methods,
                  inject_datasetrolling_methods, has_bottleneck, bn)
from .dask_array_ops import dask_rolling_wrapper


class Rolling(object):
    """A object that implements the moving window pattern.

    See Also
    --------
    Dataset.groupby
    DataArray.groupby
    Dataset.rolling
    DataArray.rolling
    """

    _attributes = ['window', 'min_periods', 'center', 'dim']

    def __init__(self, obj, min_periods=None, center=False, **windows):
        """
        Moving window object.

        Parameters
        ----------
        obj : Dataset or DataArray
            Object to window.
        min_periods : int, default None
            Minimum number of observations in window required to have a value
            (otherwise result is NA). The default, None, is equivalent to
            setting min_periods equal to the size of the window.
        center : boolean, default False
            Set the labels at the center of the window.
        **windows : dim=window
            dim : str
                Name of the dimension to create the rolling iterator
                along (e.g., `time`).
            window : int
                Size of the moving window.

        Returns
        -------
        rolling : type of input argument
        """

        if (has_bottleneck and
                (LooseVersion(bn.__version__) < LooseVersion('1.0'))):
            warnings.warn('xarray requires bottleneck version of 1.0 or '
                          'greater for rolling operations. Rolling '
                          'aggregation methods will use numpy instead'
                          'of bottleneck.')

        if len(windows) != 1:
            raise ValueError('exactly one dim/window should be provided')

        dim, window = next(iter(windows.items()))

        if window <= 0:
            raise ValueError('window must be > 0')

        self.obj = obj

        # attributes
        self.window = window
        self.min_periods = min_periods
        if min_periods is None:
            self._min_periods = window
        else:
            if min_periods <= 0:
                raise ValueError(
                    'min_periods must be greater than zero or None')

            self._min_periods = min_periods
        self.center = center
        self.dim = dim

    def __repr__(self):
        """provide a nice str repr of our rolling object"""

        attrs = ["{k}->{v}".format(k=k, v=getattr(self, k))
                 for k in self._attributes
                 if getattr(self, k, None) is not None]
        return "{klass} [{attrs}]".format(klass=self.__class__.__name__,
                                          attrs=','.join(attrs))

    def __len__(self):
        return self.obj.sizes[self.dim]


class DataArrayRolling(Rolling):
    """
    This class adds the following class methods;
    + _reduce_method(cls, func)
    + _bottleneck_reduce(cls, func)

    These class methods will be used to inject numpy or bottleneck function
    by doing

    >>> func = cls._reduce_method(f)
    >>> func.__name__ = name
    >>> setattr(cls, name, func)

    in ops.inject_bottleneck_rolling_methods.

    After the injection, the Rolling object will have `name` (such as `mean` or
    `median`) methods,
    e.g. it enables the following call,
    >>> data.rolling().mean()

    If bottleneck is installed, some bottleneck methods will be used instdad of
    the numpy method.

    see also
    + rolling.DataArrayRolling
    + ops.inject_bottleneck_rolling_methods
    """

    def __init__(self, obj, min_periods=None, center=False, **windows):
        super(DataArrayRolling, self).__init__(obj, min_periods=min_periods,
                                               center=center, **windows)
        self.window_indices = None
        self.window_labels = None

        self._setup_windows()

    def __iter__(self):
        min_periods = self.min_periods if self.min_periods else self.window
        for (label, indices) in zip(self.window_labels, self.window_indices):
            window = self.obj.isel(**{self.dim: indices})

            counts = window.count(dim=self.dim)
            window = window.where(counts >= self._min_periods)

            yield (label, window)

    def _setup_windows(self):
        """
        Find the indices and labels for each window
        """
        self.window_labels = self.obj[self.dim]
        window = int(self.window)
        dim_size = self.obj[self.dim].size

        stops = np.arange(dim_size) + 1
        starts = np.maximum(stops - window, 0)

        self.window_indices = [slice(start, stop)
                               for start, stop in zip(starts, stops)]

    def to_dataarray(self, window_dim):
        """
        Convert this rolling object to xr.DataArray,
        where the window dimension is stacked as a new dimension

        Parameters
        ----------
        window_dim: str
            New name of the window dimension.

        Returns
        -------
        DataArray that is a view of the original array.

        Note
        ----
        The return array is not writeable.

        Examples
        --------
        >>> da = DataArray(np.arange(8).reshape(2, 4), dims=('a', 'b'))

        >>> da.rolling_window(x, 'b', 4, 'window_dim')
        <xarray.DataArray (a: 2, b: 4, window_dim: 3)>
        array([[[np.nan, np.nan, 0], [np.nan, 0, 1], [0, 1, 2], [1, 2, 3]],
               [[np.nan, np.nan, 4], [np.nan, 4, 5], [4, 5, 6], [5, 6, 7]]])
        Dimensions without coordinates: a, b, window_dim

        >>> da.rolling_window(x, 'b', 4, 'window_dim', center=True)
        <xarray.DataArray (a: 2, b: 4, window_dim: 3)>
        array([[[np.nan, 0, 1], [0, 1, 2], [1, 2, 3], [2, 3, np.nan]],
               [[np.nan, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7, np.nan]]])
        Dimensions without coordinates: a, b, window_dim
        """

        from .dataarray import DataArray

        window = self.obj.variable.rolling_window(self.dim, self.window,
                                                  window_dim, self.center)
        return DataArray(window, dims=self.obj.dims + (window_dim,),
                         coords=self.obj.coords)

    def reduce(self, func, **kwargs):
        """Reduce the items in this group by applying `func` along some
        dimension(s).

        Parameters
        ----------
        func : function
            Function which can be called in the form
            `func(x, **kwargs)` to return the result of collapsing an
            np.ndarray over an the rolling dimension.
        **kwargs : dict
            Additional keyword arguments passed on to `func`.

        Returns
        -------
        reduced : DataArray
            Array with summarized data.
        """

        windows = self.to_dataarray('_rolling_window_dim')
        result = windows.reduce(func, dim='_rolling_window_dim', **kwargs)

        # Find valid windows based on count.
        # We do not use `reduced.count()` because it constructs a larger array
        # (notice that `windows` is just a view)
        counts = (~self.obj.isnull()).rolling(
            center=self.center, **{self.dim: self.window}).to_dataarray(
                '_rolling_window_dim').sum(dim='_rolling_window_dim')
        result = result.where(counts >= self._min_periods)
        # restore dim order
        return result.transpose(*self.obj.dims)

    @classmethod
    def _reduce_method(cls, func):
        """
        Methods to return a wrapped function for any function `func` for
        numpy methods.
        """

        def wrapped_func(self, **kwargs):
            return self.reduce(func, **kwargs)
        return wrapped_func

    @classmethod
    def _bottleneck_reduce(cls, func):
        """
        Methods to return a wrapped function for any function `func` for
        bottoleneck method, except for `median`.
        """

        def wrapped_func(self, **kwargs):
            from .dataarray import DataArray

            # bottleneck doesn't allow min_count to be 0, although it should
            # work the same as if min_count = 1
            if self.min_periods is not None and self.min_periods == 0:
                min_count = 1
            else:
                min_count = self.min_periods

            axis = self.obj.get_axis_num(self.dim)

            padded = self.obj.variable
            if self.center:
                shift = (-self.window // 2) + 1
                padded = padded.pad_with_fill_value(**{self.dim: (0, -shift)})
                valid = (slice(None), ) * axis + (slice(-shift, None), )

            if isinstance(padded.data, dask_array_type):
                values = dask_rolling_wrapper(func, self.obj.data,
                                              window=self.window,
                                              min_count=min_count,
                                              axis=axis)
            else:
                values = func(padded.data, window=self.window,
                              min_count=min_count, axis=axis)

            if self.center:
                values = values[valid]
            result = DataArray(values, self.obj.coords)

            return result
        return wrapped_func


class DatasetRolling(Rolling):
    """An object that implements the moving window pattern for Dataset.

    This class has an OrderedDict named self.rollings, that is a collection of
    DataArrayRollings for all the DataArrays in the Dataset, except for those
    not depending on rolling dimension.

    reduce() method returns a new Dataset generated from a set of
    self.rollings[key].reduce().

    See Also
    --------
    Dataset.groupby
    DataArray.groupby
    Dataset.rolling
    DataArray.rolling
    """

    def __init__(self, obj, min_periods=None, center=False, **windows):
        """
        Moving window object for Dataset.

        Parameters
        ----------
        obj : Dataset
            Object to window.
        min_periods : int, default None
            Minimum number of observations in window required to have a value
            (otherwise result is NA). The default, None, is equivalent to
            setting min_periods equal to the size of the window.
        center : boolean, default False
            Set the labels at the center of the window.
        **windows : dim=window
            dim : str
                Name of the dimension to create the rolling iterator
                along (e.g., `time`).
            window : int
                Size of the moving window.

        Returns
        -------
        rolling : type of input argument
        """
        super(DatasetRolling, self).__init__(obj,
                                             min_periods, center, **windows)
        if self.dim not in self.obj.dims:
            raise KeyError(self.dim)
        # Keep each Rolling object as an OrderedDict
        self.rollings = OrderedDict()
        for key, da in self.obj.data_vars.items():
            # keeps rollings only for the dataset depending on slf.dim
            if self.dim in da.dims:
                self.rollings[key] = DataArrayRolling(da, min_periods,
                                                      center, **windows)

    def reduce(self, func, **kwargs):
        """Reduce the items in this group by applying `func` along some
        dimension(s).

        Parameters
        ----------
        func : function
            Function which can be called in the form
            `func(x, **kwargs)` to return the result of collapsing an
            np.ndarray over an the rolling dimension.
        **kwargs : dict
            Additional keyword arguments passed on to `func`.

        Returns
        -------
        reduced : DataArray
            Array with summarized data.
        """
        from .dataset import Dataset
        reduced = OrderedDict()
        for key, da in self.obj.data_vars.items():
            if self.dim in da.dims:
                reduced[key] = self.rollings[key].reduce(func, **kwargs)
            else:
                reduced[key] = self.obj[key]
        return Dataset(reduced, coords=self.obj.coords)

    @classmethod
    def _reduce_method(cls, func):
        """
        Return a wrapped function for injecting numpy and bottoleneck methods.
        see ops.inject_datasetrolling_methods
        """

        def wrapped_func(self, **kwargs):
            from .dataset import Dataset
            reduced = OrderedDict()
            for key, da in self.obj.data_vars.items():
                if self.dim in da.dims:
                    reduced[key] = getattr(self.rollings[key],
                                           func.__name__)(**kwargs)
                else:
                    reduced[key] = self.obj[key]
            return Dataset(reduced, coords=self.obj.coords)
        return wrapped_func

    def to_dataset(self, window_dim):
        """
        Convert this rolling object to xr.Dataset,
        where the window dimension is stacked as a new dimension

        Parameters
        ----------
        window_dim: str
            New name of the window dimension.

        Returns
        -------
        Dataset with variables converted from rolling object.
        """

        from .dataset import Dataset

        dataset = OrderedDict()
        for key, da in self.obj.data_vars.items():
            if self.dim in da.dims:
                dataset[key] = self.rollings[key].to_dataarray(window_dim)
            else:
                dataset[key] = da
        return Dataset(dataset, coords=self.obj.coords)


inject_bottleneck_rolling_methods(DataArrayRolling)
inject_datasetrolling_methods(DatasetRolling)
