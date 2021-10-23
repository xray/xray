"""Generate module and stub file for arithmetic operators of various xarray classes.

For internal xarray development use only.

Usage:
    python xarray/util/generate_reductions.py > xarray/core/_reductions.py
"""

import collections
import textwrap
from typing import Callable, Optional

MODULE_PREAMBLE = '''\
"""Mixin classes with reduction operations."""
# This file was generated using xarray.util.generate_reductions. Do not edit manually.

from typing import Optional

from . import duck_array_ops
from .types import T_DataArray, T_Dataset'''

CLASS_PREAMBLE = """

class {obj}{cls}Reductions:
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


BOOL_REDUCE_METHODS = ["all", "any"]
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
    def {method}(
        self,
        dim=None, {skip_na.kwarg}{min_count.kwarg}
        keep_attrs=None,
        **kwargs,
    ) -> T_{obj}:
        """
        Reduce this {obj}'s data by applying ``{method}`` along some dimension(s).

        Parameters
        ----------
        dim : hashable or iterable of hashable, optional
            Name of dimension[s] along which to apply ``{method}``.{extra_args}{skip_na.docs}{min_count.docs}
        keep_attrs : bool, optional
            If True, ``attrs`` will be copied from the original
            object to the new one.  If False (default), the new object will be
            returned without attributes.
        **kwargs : dict
            Additional keyword arguments passed on to the appropriate array
            function for calculating ``{method}`` on this object's data.

        Returns
        -------
        reduced : {obj}
            New {obj} with ``{method}`` applied to its data and the
            indicated dimension(s) removed

        Examples
        --------{example}

        See Also
        --------
        :ref:`{docref}`
            User guide on {docref} operations.
        """
        return self.reduce(
            duck_array_ops.{array_method},
            dim=dim,{skip_na.call}{min_count.call}{numeric_only_call}
            keep_attrs=keep_attrs,
            **kwargs,
        )
'''


def generate_groupby_example(obj, method):
    """Generate examples for method."""
    dx = "ds" if obj == "Dataset" else "da"
    calculation = f'{dx}.groupby("labels").{method}()'

    if method in BOOL_REDUCE_METHODS:
        create_da = """
        >>> da = xr.DataArray(
        ...     np.array([True, True, True, True, True, False], dtype=bool),
        ...     dims="x",
        ...     coords=dict(labels=("x", np.array(["a", "b", "c", "c", "b", "a"]))),
        ... )"""
    else:
        create_da = """
        >>> da = xr.DataArray(
        ...     [1, 2, 3, 1, 2, np.nan],
        ...     dims="x",
        ...     coords=dict(labels=("x", np.array(["a", "b", "c", "c", "b", "a"]))),
        ... )"""

    if obj == "Dataset":
        maybe_dataset = """
        >>> ds = xr.Dataset(dict(da=da))"""
    else:
        maybe_dataset = ""

    if method in NAN_REDUCE_METHODS:
        maybe_skipna = f"""
        >>> {dx}.groupby("labels").{method}(skipna=False)"""
    else:
        maybe_skipna = ""

    return f"""{create_da}{maybe_dataset}
        >>> {calculation}{maybe_skipna}"""


def generate_resample_example(obj: str, method: str):
    """Generate examples for method."""
    dx = "ds" if obj == "Dataset" else "da"
    calculation = f'{dx}.resample(time="3M").{method}()'

    if method in BOOL_REDUCE_METHODS:
        np_array = """
        ...     np.array([True, True, True, True, True, False], dtype=bool),"""

    else:
        np_array = """
        ...     np.array([1, 2, 3, 1, 2, np.nan], dtype=bool),"""

    create_da = f"""
        >>> da = xr.DataArray({np_array}
        ...     dims="time",
        ...     coords=dict(time=("time", pd.date_range("01-01-2001", freq="M", periods=6))),
        ... )"""

    if obj == "Dataset":
        maybe_dataset = ">>> ds = xr.Dataset(dict(da=da))"
    else:
        maybe_dataset = ""

    if method in NAN_REDUCE_METHODS:
        maybe_skipna = f"""
        >>> {dx}.resample(time="3M").{method}(skipna=False)"""
    else:
        maybe_skipna = ""

    return f"""{create_da}
        {maybe_dataset}
        >>> {calculation}{maybe_skipna}"""


def generate_method(
    obj: str,
    docref: str,
    method: str,
    skipna: bool,
    example_generator: Callable,
    array_method: Optional[str] = None,
):
    if not array_method:
        array_method = method

    if obj == "Dataset":
        if method in NUMERIC_ONLY_METHODS:
            numeric_only_call = "numeric_only=True,"
        else:
            numeric_only_call = "numeric_only=False,"
    else:
        numeric_only_call = ""

    kwarg = collections.namedtuple("kwarg", "docs kwarg call")
    if skipna:
        skip_na = kwarg(
            docs=textwrap.indent(_SKIPNA_DOCSTRING, "        "),
            kwarg="skipna: bool=True, ",
            call="skipna=skipna,",
        )
    else:
        skip_na = kwarg(docs="", kwarg="", call="")

    if method in MIN_COUNT_METHODS:
        min_count = kwarg(
            docs=textwrap.indent(_MINCOUNT_DOCSTRING, "        "),
            kwarg="min_count: Optional[int]=None, ",
            call="min_count=min_count,",
        )
    else:
        min_count = kwarg(docs="", kwarg="", call="")

    return TEMPLATE_REDUCTION.format(
        obj=obj,
        docref=docref,
        method=method,
        array_method=array_method,
        extra_args="",
        skip_na=skip_na,
        min_count=min_count,
        numeric_only_call=numeric_only_call,
        example=example_generator(obj, method),
    )


def render(obj: str, cls: str, docref: str, example_generator: Callable):
    yield CLASS_PREAMBLE.format(obj=obj, cls=cls)
    yield generate_method(
        obj,
        method="count",
        docref=docref,
        skipna=False,
        example_generator=example_generator,
    )
    for method in BOOL_REDUCE_METHODS:
        yield generate_method(
            obj,
            method=method,
            docref=docref,
            skipna=False,
            array_method=f"array_{method}",
            example_generator=example_generator,
        )
    for method in NAN_REDUCE_METHODS:
        yield generate_method(
            obj,
            method=method,
            docref=docref,
            skipna=True,
            example_generator=example_generator,
        )


if __name__ == "__main__":
    print(MODULE_PREAMBLE)
    for obj in ["Dataset", "DataArray"]:
        for cls, docref, examplegen in (
            ("GroupBy", "groupby", generate_groupby_example),
            ("Resample", "resampling", generate_resample_example),
        ):
            for line in render(
                obj=obj, cls=cls, docref=docref, example_generator=examplegen
            ):
                print(line)
