"""Generate module and stub file for arithmetic operators of various xarray classes.

For internal xarray development use only.

Usage:
    python xarray/util/generate_reductions.py > xarray/core/_reductions.py
"""

import textwrap
from typing import Optional

MODULE_PREAMBLE = '''\
"""Mixin classes with reduction operations."""
# This file was generated using xarray.util.generate_reductions. Do not edit manually.

from . import duck_array_ops'''

CLASS_PREAMBLE = """

class {cls}GroupByReductions:
    __slots__ = ()"""

_SKIPNA_DOCSTRING = """
skipna : bool, optional
    If True, skip missing values (as marked by NaN). By default, only
    skips missing values for float dtypes; other dtypes either do not
    have a sentinel missing value (int) or skipna=True has not been
    implemented (object, datetime64 or timedelta64)."""

_MINCOUNT_DOCSTRING = """
min_count : int, default: None
    The required number of valid values to perform the operation. If
    fewer than min_count non-NA values are present the result will be
    NA. Only used if skipna is set to True or defaults to True for the
    array's dtype. Changed in version 0.17.0: if specified on an integer
    array and skipna=True, the result will be a float array."""


REDUCE_METHODS = ["all", "any"]
NAN_REDUCE_METHODS = [
    "max",
    "min",
    "mean",
    "prod",
    "sum",
    "std",
    "var",
    "median",
]
NAN_CUM_METHODS = ["cumsum", "cumprod"]
MIN_COUNT_METHODS = ["prod", "sum"]
NUMERIC_ONLY_METHODS = [
    "mean",
    "std",
    "var",
    "sum",
    "prod",
    "median",
    "cumsum",
    "cumprod",
]

TEMPLATE_REDUCTION = '''
    def {method}(self, dim=None, {skip_na_kwarg}{min_count_kwarg}keep_attrs=None, **kwargs):
        """
        Reduce this {cls}'s data by applying `{method}` along some dimension(s).

        Parameters
        ----------
        dim : hashable, optional
{extra_args}{skip_na_docs}{min_count_docs}
        keep_attrs : bool, optional
            If True, the attributes (`attrs`) will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating `{method}` on this object's data.

        Returns
        -------
        reduced : {cls}
            New {cls} with `{method}` applied to its data and the
            indicated dimension(s) removed
        """
        return self.reduce(
            duck_array_ops.{array_method},
            dim=dim,{skip_na_reduce}{min_count_reduce}{numeric_only_reduce}
            keep_attrs=keep_attrs,
            **kwargs,
        )
'''


def generate_method(
    cls: str,
    method: str,
    skipna: bool,
    array_method: Optional[str] = None,
):
    if not array_method:
        array_method = method

    if cls == "Dataset":
        if method in NUMERIC_ONLY_METHODS:
            numeric_only_reduce = "numeric_only=True,"
        else:
            numeric_only_reduce = "numeric_only=False,"
    else:
        numeric_only_reduce = ""

    if skipna:
        skip_na_docs = textwrap.indent(_SKIPNA_DOCSTRING, "        ")
        skip_na_kwarg = "skipna=True, "
        skip_na_reduce = "skipna=skipna,"
    else:
        skip_na_docs = ""
        skip_na_kwarg = ""
        skip_na_reduce = ""

    if method in MIN_COUNT_METHODS:
        min_count_docs = textwrap.indent(_MINCOUNT_DOCSTRING, "        ")
        min_count_kwarg = "min_count=None, "
        min_count_reduce = "min_count=min_count,"
    else:
        min_count_docs = ""
        min_count_kwarg = ""
        min_count_reduce = ""

    return TEMPLATE_REDUCTION.format(
        cls=cls,
        method=method,
        array_method=array_method,
        extra_args="",
        skip_na_docs=skip_na_docs,
        skip_na_kwarg=skip_na_kwarg,
        skip_na_reduce=skip_na_reduce,
        min_count_docs=min_count_docs,
        min_count_kwarg=min_count_kwarg,
        min_count_reduce=min_count_reduce,
        numeric_only_reduce=numeric_only_reduce,
    )


def render(cls):
    yield CLASS_PREAMBLE.format(cls=cls)
    yield generate_method(cls, "count", skipna=False)
    for method in REDUCE_METHODS:
        yield generate_method(
            cls,
            method,
            skipna=False,
            array_method=f"array_{method}",
        )
    for method in NAN_REDUCE_METHODS:
        yield generate_method(cls, method, skipna=True)


if __name__ == "__main__":
    print(MODULE_PREAMBLE)
    for cls in ["Dataset", "DataArray"]:
        for line in render(cls=cls):
            print(line)
