# flake8: noqa
import sys

import numpy as np

integer_types = (int, np.integer, )

try:
    # solely for isinstance checks
    import dask.array
    dask_array_type = (dask.array.Array,)
except ImportError:  # pragma: no cover
    dask_array_type = ()

USE_TYPING = sys.version >= '3.5.3'
