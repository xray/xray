import sys
import warnings

# TODO: Remove this check once python 3.7 is not supported:
if sys.version_info >= (3, 8):
    from typing import TYPE_CHECKING, Union
    from typing_extensions import TypedDict

    if TYPE_CHECKING:
        try:
            from matplotlib.colors import Colormap
        except ImportError:
            Colormap = str

    class T_Options(TypedDict):
        arithmetic_join: str
        cmap_divergent: Union[str, "Colormap"]
        cmap_sequential: Union[str, "Colormap"]
        display_max_rows: int
        display_style: str
        display_width: int
        display_expand_attrs: str
        display_expand_coords: str
        display_expand_data_vars: str
        display_expand_data: str
        enable_cftimeindex: bool
        file_cache_maxsize: int
        keep_attrs: str
        warn_for_unclosed_files: bool
        use_bottleneck: bool


else:
    # See GH5624, this is a convoluted way to allow type-checking to use
    # `TypedDict` without requiring typing_extensions as a required dependency
    #  to _run_ the code (it is required to type-check).
    try:
        from typing import TYPE_CHECKING, Union
        from typing_extensions import TypedDict

        if TYPE_CHECKING:
            try:
                from matplotlib.colors import Colormap
            except ImportError:
                Colormap = str

        class T_Options(TypedDict):
            arithmetic_join: str
            cmap_divergent: Union[str, "Colormap"]
            cmap_sequential: Union[str, "Colormap"]
            display_max_rows: int
            display_style: str
            display_width: int
            display_expand_attrs: str
            display_expand_coords: str
            display_expand_data_vars: str
            display_expand_data: str
            enable_cftimeindex: bool
            file_cache_maxsize: int
            keep_attrs: str
            warn_for_unclosed_files: bool
            use_bottleneck: bool

    except ImportError:
        from typing import TYPE_CHECKING, Any, Dict, Hashable

        if TYPE_CHECKING:
            raise
        else:
            T_Options = Dict[Hashable, Any]


OPTIONS: T_Options = {
    "arithmetic_join": "inner",
    "cmap_divergent": "RdBu_r",
    "cmap_sequential": "viridis",
    "display_max_rows": 12,
    "display_style": "html",
    "display_width": 80,
    "display_expand_attrs": "default",
    "display_expand_coords": "default",
    "display_expand_data_vars": "default",
    "display_expand_data": "default",
    "enable_cftimeindex": True,
    "file_cache_maxsize": 128,
    "keep_attrs": "default",
    "warn_for_unclosed_files": False,
    "use_bottleneck": True,
}

_JOIN_OPTIONS = frozenset(["inner", "outer", "left", "right", "exact"])
_DISPLAY_OPTIONS = frozenset(["text", "html"])


def _positive_integer(value):
    return isinstance(value, int) and value > 0


_VALIDATORS = {
    "arithmetic_join": _JOIN_OPTIONS.__contains__,
    "display_max_rows": _positive_integer,
    "display_style": _DISPLAY_OPTIONS.__contains__,
    "display_width": _positive_integer,
    "display_expand_attrs": lambda choice: choice in [True, False, "default"],
    "display_expand_coords": lambda choice: choice in [True, False, "default"],
    "display_expand_data_vars": lambda choice: choice in [True, False, "default"],
    "display_expand_data": lambda choice: choice in [True, False, "default"],
    "enable_cftimeindex": lambda value: isinstance(value, bool),
    "file_cache_maxsize": _positive_integer,
    "keep_attrs": lambda choice: choice in [True, False, "default"],
    "warn_for_unclosed_files": lambda value: isinstance(value, bool),
    "use_bottleneck": lambda choice: choice in [True, False],
}


def _set_file_cache_maxsize(value):
    from ..backends.file_manager import FILE_CACHE

    FILE_CACHE.maxsize = value


def _warn_on_setting_enable_cftimeindex(enable_cftimeindex):
    warnings.warn(
        "The enable_cftimeindex option is now a no-op "
        "and will be removed in a future version of xarray.",
        FutureWarning,
    )


_SETTERS = {
    "enable_cftimeindex": _warn_on_setting_enable_cftimeindex,
    "file_cache_maxsize": _set_file_cache_maxsize,
}


def _get_boolean_with_default(option, default):
    global_choice = OPTIONS[option]

    if global_choice == "default":
        return default
    elif global_choice in [True, False]:
        return global_choice
    else:
        raise ValueError(
            f"The global option {option} must be one of True, False or 'default'."
        )


def _get_keep_attrs(default):
    return _get_boolean_with_default("keep_attrs", default)


class set_options:
    """Set options for xarray in a controlled context.

    Currently supported options:

    - ``display_width``: maximum display width for ``repr`` on xarray objects.
      Default: ``80``.
    - ``display_max_rows``: maximum display rows. Default: ``12``.
    - ``arithmetic_join``: DataArray/Dataset alignment in binary operations.
      Default: ``'inner'``.
    - ``file_cache_maxsize``: maximum number of open files to hold in xarray's
      global least-recently-usage cached. This should be smaller than your
      system's per-process file descriptor limit, e.g., ``ulimit -n`` on Linux.
      Default: 128.
    - ``warn_for_unclosed_files``: whether or not to issue a warning when
      unclosed files are deallocated (default False). This is mostly useful
      for debugging.
    - ``cmap_sequential``: colormap to use for nondivergent data plots.
      Default: ``viridis``. If string, must be matplotlib built-in colormap.
      Can also be a Colormap object (e.g. mpl.cm.magma)
    - ``cmap_divergent``: colormap to use for divergent data plots.
      Default: ``RdBu_r``. If string, must be matplotlib built-in colormap.
      Can also be a Colormap object (e.g. mpl.cm.magma)
    - ``keep_attrs``: rule for whether to keep attributes on xarray
      Datasets/dataarrays after operations. Either ``True`` to always keep
      attrs, ``False`` to always discard them, or ``'default'`` to use original
      logic that attrs should only be kept in unambiguous circumstances.
      Default: ``'default'``.
    - ``use_bottleneck``: allow using bottleneck. Either ``True`` to accelerate
      operations using bottleneck if it is installed or ``False`` to never use it.
      Default: ``True``
    - ``display_style``: display style to use in jupyter for xarray objects.
      Default: ``'html'``. Other options are ``'text'``.
    - ``display_expand_attrs``: whether to expand the attributes section for
      display of ``DataArray`` or ``Dataset`` objects. Can be ``True`` to always
      expand, ``False`` to always collapse, or ``default`` to expand unless over
      a pre-defined limit. Default: ``default``.
    - ``display_expand_coords``: whether to expand the coordinates section for
      display of ``DataArray`` or ``Dataset`` objects. Can be ``True`` to always
      expand, ``False`` to always collapse, or ``default`` to expand unless over
      a pre-defined limit. Default: ``default``.
    - ``display_expand_data``: whether to expand the data section for display
      of ``DataArray`` objects. Can be ``True`` to always expand, ``False`` to
      always collapse, or ``default`` to expand unless over a pre-defined limit.
      Default: ``default``.
    - ``display_expand_data_vars``: whether to expand the data variables section
      for display of ``Dataset`` objects. Can be ``True`` to always
      expand, ``False`` to always collapse, or ``default`` to expand unless over
      a pre-defined limit. Default: ``default``.


    You can use ``set_options`` either as a context manager:

    >>> ds = xr.Dataset({"x": np.arange(1000)})
    >>> with xr.set_options(display_width=40):
    ...     print(ds)
    ...
    <xarray.Dataset>
    Dimensions:  (x: 1000)
    Coordinates:
      * x        (x) int64 0 1 2 ... 998 999
    Data variables:
        *empty*

    Or to set global options:

    >>> xr.set_options(display_width=80)  # doctest: +ELLIPSIS
    <xarray.core.options.set_options object at 0x...>
    """

    def __init__(self, **kwargs):
        self.old = {}
        for k, v in kwargs.items():
            if k not in OPTIONS:
                raise ValueError(
                    f"argument name {k!r} is not in the set of valid options {set(OPTIONS)!r}"
                )
            if k in _VALIDATORS and not _VALIDATORS[k](v):
                if k == "arithmetic_join":
                    expected = f"Expected one of {_JOIN_OPTIONS!r}"
                elif k == "display_style":
                    expected = f"Expected one of {_DISPLAY_OPTIONS!r}"
                else:
                    expected = ""
                raise ValueError(
                    f"option {k!r} given an invalid value: {v!r}. " + expected
                )
            self.old[k] = OPTIONS[k]
        self._apply_update(kwargs)

    def _apply_update(self, options_dict):
        for k, v in options_dict.items():
            if k in _SETTERS:
                _SETTERS[k](v)
        OPTIONS.update(options_dict)

    def __enter__(self):
        return

    def __exit__(self, type, value, traceback):
        self._apply_update(self.old)
