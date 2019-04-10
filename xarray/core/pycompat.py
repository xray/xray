import sys
from collections import abc

import numpy as np

integer_types = (int, np.integer, )

try:
    # solely for isinstance checks
    import dask.array
    dask_array_type = (dask.array.Array,)
except ImportError:  # pragma: no cover
    dask_array_type = ()


if sys.version < '3.5.3':
    TYPE_CHECKING = False

    class _ABCDummyBrackets(type(abc.Mapping)):  # abc.ABCMeta
        def __getitem__(cls, name):
            return cls

    class Mapping(abc.Mapping, metaclass=_ABCDummyBrackets):
        pass

    class MutableMapping(abc.MutableMapping, metaclass=_ABCDummyBrackets):
        pass

    class MutableSet(abc.MutableSet, metaclass=_ABCDummyBrackets):
        pass

else:
    from typing import TYPE_CHECKING  # noqa: F401

    # from typing import Mapping, MutableMapping, MutableSet

    # The above confuses mypy 0.700. To workaround, use instead
    # from typing import Mapping, MutableMapping, MutableSet
    # try:
    #     from .pycompat import Mapping, MutableMapping, MutableSet
    # except ImportError:
    #      pass
