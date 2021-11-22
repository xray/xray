"""Generate module and stub file for arithmetic operators of various xarray classes.

For internal xarray development use only.

Usage:
    python xarray/util/generate_reductions.py > xarray/core/_reductions.py
    pytest --doctest-modules xarray/core/_reductions.py --accept || true
    pytest --doctest-modules xarray/core/_reductions.py --accept

This requires [pytest-accept](https://github.com/max-sixty/pytest-accept).
The second run of pytest is deliberate, since the first will return an error
while replacing the doctests.

"""
import collections
import textwrap
from dataclasses import dataclass

MODULE_PREAMBLE = '''\
"""Mixin classes with reduction operations."""
# This file was generated using xarray.util.generate_reductions. Do not edit manually.

import sys
from typing import Any, Callable, Hashable, Optional, Sequence, Union

from . import duck_array_ops
from .options import OPTIONS
from .types import T_DataArray, T_Dataset
from .utils import contains_only_dask_or_numpy

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol


try:
    import flox
except ImportError:
    flox = None'''

OBJ_PREAMBLE = """

class {obj}Reduce(Protocol):
    def reduce(
        self,
        func: Callable[..., Any],
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        axis: Union[None, int, Sequence[int]] = None,
        keep_attrs: bool = None,
        keepdims: bool = False,
        **kwargs: Any,
    ) -> T_{obj}:
        ...


class {obj}GroupByReduce(Protocol):
    _obj: T_{obj}

    def reduce(
        self,
        func: Callable[..., Any],
        dim: Union[None, Hashable, Sequence[Hashable]] = None,
        axis: Union[None, int, Sequence[int]] = None,
        keep_attrs: bool = None,
        keepdims: bool = False,
        **kwargs: Any,
    ) -> T_{obj}:
        ...

    def _flox_reduce(
        self,
        dim: Union[None, Hashable, Sequence[Hashable]],
        **kwargs,
    ) -> T_{obj}:
        ..."""


CLASS_PREAMBLE = """

class {obj}{cls}Reductions:
    __slots__ = ()"""

TEMPLATE_REDUCTION_SIGNATURE = '''
    def {method}(
        self: {self_type},
        dim: Union[None, Hashable, Sequence[Hashable]] = None,{extra_kwargs}
        keep_attrs: bool = None,
        **kwargs,
    ) -> T_{obj}:
        """
        Reduce this {obj}'s data by applying ``{method}`` along some dimension(s).

        Parameters
        ----------'''

TEMPLATE_RETURNS = """
        Returns
        -------
        reduced : {obj}
            New {obj} with ``{method}`` applied to its data and the
            indicated dimension(s) removed"""

TEMPLATE_SEE_ALSO = """
        See Also
        --------
        numpy.{method}
        dask.array.{method}
        {see_also_obj}.{method}
        :ref:`{docref}`
            User guide on {docref_description}."""

TEMPLATE_NOTES = """
        Notes
        -----
        {notes}"""

_DIM_DOCSTRING = """dim : hashable or iterable of hashable, optional
    Name of dimension[s] along which to apply ``{method}``. For e.g. ``dim="x"``
    or ``dim=["x", "y"]``. If None, will reduce over all dimensions."""

_SKIPNA_DOCSTRING = """skipna : bool, default: None
    If True, skip missing values (as marked by NaN). By default, only
    skips missing values for float dtypes; other dtypes either do not
    have a sentinel missing value (int) or ``skipna=True`` has not been
    implemented (object, datetime64 or timedelta64)."""

_MINCOUNT_DOCSTRING = """min_count : int, default: None
    The required number of valid values to perform the operation. If
    fewer than min_count non-NA values are present the result will be
    NA. Only used if skipna is set to True or defaults to True for the
    array's dtype. Changed in version 0.17.0: if specified on an integer
    array and skipna=True, the result will be a float array."""

_DDOF_DOCSTRING = """ddof : int, default: 0
    “Delta Degrees of Freedom”: the divisor used in the calculation is ``N - ddof``,
    where ``N`` represents the number of elements."""

_KEEP_ATTRS_DOCSTRING = """keep_attrs : bool, optional
    If True, ``attrs`` will be copied from the original
    object to the new one.  If False (default), the new object will be
    returned without attributes."""

_KWARGS_DOCSTRING = """**kwargs : dict
    Additional keyword arguments passed on to the appropriate array
    function for calculating ``{method}`` on this object's data.
    These could include dask-specific kwargs like ``split_every``."""

NAN_CUM_METHODS = ["cumsum", "cumprod"]

NUMERIC_ONLY_METHODS = [
    "cumsum",
    "cumprod",
]
_NUMERIC_ONLY_NOTES = "Non-numeric variables will be removed prior to reducing."

extra_kwarg = collections.namedtuple("extra_kwarg", "docs kwarg call example")
skipna = extra_kwarg(
    docs=_SKIPNA_DOCSTRING,
    kwarg="skipna: bool = None,",
    call="skipna=skipna,",
    example="""\n
        Use ``skipna`` to control whether NaNs are ignored.

        >>> {calculation}(skipna=False)""",
)
min_count = extra_kwarg(
    docs=_MINCOUNT_DOCSTRING,
    kwarg="min_count: Optional[int] = None,",
    call="min_count=min_count,",
    example="""\n
        Specify ``min_count`` for finer control over when NaNs are ignored.

        >>> {calculation}(skipna=True, min_count=2)""",
)
ddof = extra_kwarg(
    docs=_DDOF_DOCSTRING,
    kwarg="ddof: int = 0,",
    call="ddof=ddof,",
    example="""\n
        Specify ``ddof=1`` for an unbiased estimate.

        >>> {calculation}(skipna=True, ddof=1)""",
)


class Method:
    def __init__(
        self,
        name,
        bool_reduce=False,
        extra_kwargs=tuple(),
        numeric_only=False,
    ):
        self.name = name
        self.extra_kwargs = extra_kwargs
        self.numeric_only = numeric_only

        if bool_reduce:
            self.array_method = f"array_{name}"
            self.np_example_array = """
        ...     np.array([True, True, True, True, True, False], dtype=bool),"""

        else:
            self.array_method = name
            self.np_example_array = """
        ...     np.array([1, 2, 3, 1, 2, np.nan]),"""


class ReductionGenerator:
    def __init__(
        self,
        cls,
        datastructure,
        self_type,
        methods,
        docref,
        docref_description,
        example_call_preamble,
        see_also_obj=None,
    ):
        self.datastructure = datastructure
        self.self_type = self_type
        self.cls = cls
        self.methods = methods
        self.docref = docref
        self.docref_description = docref_description
        self.example_call_preamble = example_call_preamble
        self.preamble = CLASS_PREAMBLE.format(obj=datastructure.name, cls=cls)
        if not see_also_obj:
            self.see_also_obj = self.datastructure.name
        else:
            self.see_also_obj = see_also_obj

    def generate_methods(self):
        yield [self.preamble]
        for method in self.methods:
            yield self.generate_method(method)

    def generate_method(self, method):
        template_kwargs = dict(obj=self.datastructure.name, method=method.name)

        if method.extra_kwargs:
            extra_kwargs = "\n        " + "\n        ".join(
                [kwarg.kwarg for kwarg in method.extra_kwargs if kwarg.kwarg]
            )
        else:
            extra_kwargs = ""

        yield TEMPLATE_REDUCTION_SIGNATURE.format(
            **template_kwargs,
            extra_kwargs=extra_kwargs,
            self_type=self.self_type,
        )

        for text in [
            _DIM_DOCSTRING.format(method=method.name),
            *(kwarg.docs for kwarg in method.extra_kwargs if kwarg.docs),
            _KEEP_ATTRS_DOCSTRING,
            _KWARGS_DOCSTRING.format(method=method.name),
        ]:
            if text:
                yield textwrap.indent(text, 8 * " ")

        yield TEMPLATE_RETURNS.format(**template_kwargs)

        yield TEMPLATE_SEE_ALSO.format(
            **template_kwargs,
            docref=self.docref,
            docref_description=self.docref_description,
            see_also_obj=self.see_also_obj,
        )

        if method.numeric_only:
            yield TEMPLATE_NOTES.format(notes=_NUMERIC_ONLY_NOTES)

        yield textwrap.indent(self.generate_example(method=method), "")

        yield '        """'

        yield self.generate_code(method)

    def generate_example(self, method):
        create_da = f"""
        >>> da = xr.DataArray({method.np_example_array}
        ...     dims="time",
        ...     coords=dict(
        ...         time=("time", pd.date_range("01-01-2001", freq="M", periods=6)),
        ...         labels=("time", np.array(["a", "b", "c", "c", "b", "a"])),
        ...     ),
        ... )"""

        calculation = f"{self.datastructure.example_var_name}{self.example_call_preamble}.{method.name}"
        if method.extra_kwargs:
            extra_examples = "".join(
                kwarg.example for kwarg in method.extra_kwargs if kwarg.example
            ).format(calculation=calculation, method=method.name)
        else:
            extra_examples = ""

        return f"""
        Examples
        --------{create_da}{self.datastructure.docstring_create}

        >>> {calculation}(){extra_examples}"""


class GenericReductionGenerator(ReductionGenerator):
    def generate_code(self, method):
        extra_kwargs = [kwarg.call for kwarg in method.extra_kwargs if kwarg.call]

        if self.datastructure.numeric_only:
            extra_kwargs.append(f"numeric_only={method.numeric_only},")

        if extra_kwargs:
            extra_kwargs = "\n            " + "\n            ".join(extra_kwargs)
        else:
            extra_kwargs = ""
        return f"""        return self.reduce(
            duck_array_ops.{method.array_method},
            dim=dim,{extra_kwargs}
            keep_attrs=keep_attrs,
            **kwargs,
        )"""


class GroupByReductionGenerator(ReductionGenerator):
    def generate_code(self, method):
        extra_kwargs = [kwarg.call for kwarg in method.extra_kwargs if kwarg.call]

        if self.datastructure.numeric_only:
            extra_kwargs.append(f"numeric_only={method.numeric_only},")

        # numpy_groupies & flox do not support median
        if method.name == "median":
            indent = 12
        else:
            indent = 16

        if extra_kwargs:
            extra_kwargs = textwrap.indent("\n" + "\n".join(extra_kwargs), indent * " ")
        else:
            extra_kwargs = ""

        if method.name == "median":
            return f"""        return self.reduce(
            duck_array_ops.{method.array_method},
            dim=dim,{extra_kwargs}
            keep_attrs=keep_attrs,
            **kwargs,
        )"""

        else:
            return f"""
        if (
            flox
            and OPTIONS["use_numpy_groupies"]
            and contains_only_dask_or_numpy(self._obj)
        ):
            return self._flox_reduce(
                func="{method.name}",
                dim=dim,{extra_kwargs}
                # fill_value=fill_value,
                keep_attrs=keep_attrs,
                **kwargs,
            )
        else:
            return self.reduce(
                duck_array_ops.{method.array_method},
                dim=dim,{extra_kwargs}
                keep_attrs=keep_attrs,
                **kwargs,
            )"""


REDUCTION_METHODS = (
    Method("count"),
    Method("all", bool_reduce=True),
    Method("any", bool_reduce=True),
    Method("max", extra_kwargs=(skipna,)),
    Method("min", extra_kwargs=(skipna,)),
    Method("mean", extra_kwargs=(skipna,), numeric_only=True),
    Method("prod", extra_kwargs=(skipna, min_count), numeric_only=True),
    Method("sum", extra_kwargs=(skipna, min_count), numeric_only=True),
    Method("std", extra_kwargs=(skipna, ddof), numeric_only=True),
    Method("var", extra_kwargs=(skipna, ddof), numeric_only=True),
    Method("median", extra_kwargs=(skipna,), numeric_only=True),
)


@dataclass
class DataStructure:
    name: str
    docstring_create: str
    example_var_name: str
    numeric_only: bool = False


DatasetObject = DataStructure(
    name="Dataset",
    docstring_create="""
        >>> ds = xr.Dataset(dict(da=da))
        >>> ds""",
    example_var_name="ds",
    numeric_only=True,
)
DataArrayObject = DataStructure(
    name="DataArray",
    docstring_create="""
        >>> da""",
    example_var_name="da",
    numeric_only=False,
)

DatasetGenerator = GenericReductionGenerator(
    cls="",
    datastructure=DatasetObject,
    methods=REDUCTION_METHODS,
    docref="agg",
    docref_description="reduction or aggregation operations",
    example_call_preamble="",
    see_also_obj="DataArray",
    self_type="DatasetReduce",
)
DataArrayGenerator = GenericReductionGenerator(
    cls="",
    datastructure=DataArrayObject,
    methods=REDUCTION_METHODS,
    docref="agg",
    docref_description="reduction or aggregation operations",
    example_call_preamble="",
    see_also_obj="Dataset",
    self_type="DataArrayReduce",
)

DataArrayGroupByGenerator = GroupByReductionGenerator(
    cls="GroupBy",
    datastructure=DataArrayObject,
    methods=REDUCTION_METHODS,
    docref="groupby",
    docref_description="groupby operations",
    example_call_preamble='.groupby("labels")',
    self_type="DataArrayGroupByReduce",
)
DataArrayResampleGenerator = GroupByReductionGenerator(
    cls="Resample",
    datastructure=DataArrayObject,
    methods=REDUCTION_METHODS,
    docref="resampling",
    docref_description="resampling operations",
    example_call_preamble='.resample(time="3M")',
    self_type="DataArrayGroupByReduce",
)
DatasetGroupByGenerator = GroupByReductionGenerator(
    cls="GroupBy",
    datastructure=DatasetObject,
    methods=REDUCTION_METHODS,
    docref="groupby",
    docref_description="groupby operations",
    example_call_preamble='.groupby("labels")',
    self_type="DatasetGroupByReduce",
)
DatasetResampleGenerator = GroupByReductionGenerator(
    cls="Resample",
    datastructure=DatasetObject,
    methods=REDUCTION_METHODS,
    docref="resampling",
    docref_description="resampling operations",
    example_call_preamble='.resample(time="3M")',
    self_type="DatasetGroupByReduce",
)


if __name__ == "__main__":
    print(MODULE_PREAMBLE)
    print(OBJ_PREAMBLE.format(obj="Dataset"))
    print(OBJ_PREAMBLE.format(obj="DataArray"))
    for gen in [
        DatasetGenerator,
        DataArrayGenerator,
        DatasetGroupByGenerator,
        DatasetResampleGenerator,
        DataArrayGroupByGenerator,
        DataArrayResampleGenerator,
    ]:
        for lines in gen.generate_methods():
            for line in lines:
                print(line)
