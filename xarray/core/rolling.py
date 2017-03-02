from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import numpy as np
import warnings
from distutils.version import LooseVersion

from .pycompat import OrderedDict, zip
from .common import (ImplementsRollingArrayReduce,
                     ImplementsRollingDatasetReduce, full_like)
from .combine import concat
from .ops import inject_bottleneck_rolling_methods, has_bottleneck, bn


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
                raise ValueError('min_periods must be greater than zero or None')

            self._min_periods = min_periods
        self.center = center
        self.dim = dim

        if hasattr(obj, 'get_axis_num'):
            self._axis_num = self.obj.get_axis_num(self.dim)

        self._windows = None
        self._valid_windows = None
        self.window_indices = None
        self.window_labels = None

        self._setup_windows()

    def __repr__(self):
        """provide a nice str repr of our rolling object"""

        attrs = ["{k}->{v}".format(k=k, v=getattr(self, k))
                 for k in self._attributes if getattr(self, k, None) is not None]
        return "{klass} [{attrs}]".format(klass=self.__class__.__name__,
                                          attrs=','.join(attrs))

    @property
    def windows(self):
        if self._windows is None:
            self._windows = OrderedDict(zip(self.window_labels,
                                            self.window_indices))
        return self._windows

    def __len__(self):
        return len(self.obj[self.dim])

    def __iter__(self):
        for (label, indices, valid) in zip(self.window_labels,
                                           self.window_indices,
                                           self._valid_windows):

            window = self.obj.isel(**{self.dim: indices})

            if not valid:
                window = full_like(window, fill_value=True, dtype=bool)

            yield (label, window)

    def _setup_windows(self):
        """
        Find the indices and labels for each window
        """
        from .dataarray import DataArray

        self.window_labels = self.obj[self.dim]

        window = int(self.window)

        dim_size = self.obj[self.dim].size

        stops = np.arange(dim_size) + 1
        starts = np.maximum(stops - window, 0)

        if self._min_periods > 1:
            valid_windows = (stops - starts) >= self._min_periods
        else:
            # No invalid windows
            valid_windows = np.ones(dim_size, dtype=bool)
        self._valid_windows = DataArray(valid_windows, dims=(self.dim, ),
                                        coords=self.obj[self.dim].coords)

        self.window_indices = [slice(start, stop)
                               for start, stop in zip(starts, stops)]

    def _center_result(self, result):
        """center result"""
        shift = (-self.window // 2) + 1
        return result.shift(**{self.dim: shift})

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

        windows = [window.reduce(func, dim=self.dim, **kwargs)
                   for _, window in self]

        # Find valid windows based on count
        concat_dim = self.window_labels if self.dim in self.obj else self.dim
        counts = concat([window.count(dim=self.dim) for _, window in self],
                        dim=concat_dim)
        result = concat(windows, dim=concat_dim)
        # restore dim order
        result = result.transpose(*self.obj.dims)

        result = result.where(counts >= self._min_periods)

        if self.center:
            result = self._center_result(result)

        return result


class DataArrayRolling(Rolling, ImplementsRollingArrayReduce):
    """Rolling object for DataArrays"""


class DatasetRolling(Rolling, ImplementsRollingDatasetReduce):
    """An object that implements the moving window pattern for Dataset.

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
        from .dataset import Dataset
        dim, window = next(iter(windows.items()))
        # DataArrays not depending on the rolling-axis are kept aside from obj
        self.fixed_ds = Dataset({key: da for key, da in obj.data_vars.items()
                                 if dim not in da.dims},
                                obj.coords)
        # drop them from obj, then call parent's initializer.
        obj = obj.drop(self.fixed_ds.data_vars.keys())
        Rolling.__init__(self, obj, min_periods, center, **windows)

    def reduce(self, func, **kwargs):
        if self.center:
            fixed = self._center_result(self.fixed_ds)
        else:
            fixed = self.fixed_ds
        # merge the fixed DataArrays
        return Rolling.reduce(self, func, **kwargs).merge(fixed, join='inner')


inject_bottleneck_rolling_methods(DataArrayRolling)
inject_bottleneck_rolling_methods(DatasetRolling)
