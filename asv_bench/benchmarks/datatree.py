import numpy as np

import xarray as xr
from xarray.core.datatree import DataTree

from . import parameterized


class Datatree:
    def setup(self):
        run1 = DataTree.from_dict({"run1": xr.Dataset({"a": 1})})
        self.d = {"run1": run1}

    @parameterized(["copy"], [(True, False)])
    def time_from_dict(self, copy: bool):
        DataTree.from_dict(self.d, copy=copy)
