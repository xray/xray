#
# xarray documentation build configuration file, created by
# sphinx-quickstart on Thu Feb  6 18:57:54 2014.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.


import datetime
import os
import pathlib
import subprocess
import sys
from contextlib import suppress

import sphinx_autosummary_accessors
from jinja2.defaults import DEFAULT_FILTERS

import xarray

allowed_failures = set()

print("python exec:", sys.executable)
print("sys.path:", sys.path)

if "conda" in sys.executable:
    print("conda environment:")
    subprocess.run(["conda", "list"])
else:
    print("pip environment:")
    subprocess.run([sys.executable, "-m", "pip", "list"])

print(f"xarray: {xarray.__version__}, {xarray.__file__}")

with suppress(ImportError):
    import matplotlib

    matplotlib.use("Agg")

try:
    import rasterio  # noqa: F401
except ImportError:
    allowed_failures.update(
        ["gallery/plot_rasterio_rgb.py", "gallery/plot_rasterio.py"]
    )

try:
    import cartopy  # noqa: F401
except ImportError:
    allowed_failures.update(
        [
            "gallery/plot_cartopy_facetgrid.py",
            "gallery/plot_rasterio_rgb.py",
            "gallery/plot_rasterio.py",
        ]
    )

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "IPython.sphinxext.ipython_directive",
    "IPython.sphinxext.ipython_console_highlighting",
    "nbsphinx",
    "sphinx_autosummary_accessors",
    "scanpydoc.rtd_github_links",
    "sphinx_panels",
    "sphinxext.opengraph",
    "sphinx_copybutton",
]

extlinks = {
    "issue": ("https://github.com/pydata/xarray/issues/%s", "GH"),
    "pull": ("https://github.com/pydata/xarray/pull/%s", "PR"),
}

# sphinx-copybutton configurations
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# nbsphinx configurations

nbsphinx_timeout = 600
nbsphinx_execute = "always"
# nbsphinx_prolog = """
# {% set docname = env.doc2path(env.docname, base=None) %}
# You can run this notebook in a `live session <https://mybinder.org/v2/gh/pydata/xarray/doc/examples/master?urlpath=lab/tree/doc/{{ docname }}>`_ |Binder| or view it `on Github <https://github.com/pydata/xarray/blob/master/doc/{{ docname }}>`_.
# .. |Binder| image:: https://mybinder.org/badge.svg
#    :target: https://mybinder.org/v2/gh/pydata/xarray/master?urlpath=lab/tree/doc/{{ docname }}
# """


autosummary_generate = True

# for scanpydoc's jinja filter
project_dir = pathlib.Path(__file__).parent.parent


autodoc_typehints = "none"

# Napoleon configurations

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_preprocess_types = True
napoleon_type_aliases = {
    # general terms
    "sequence": ":term:`sequence`",
    "iterable": ":term:`iterable`",
    "callable": ":py:func:`callable`",
    "dict_like": ":term:`dict-like <mapping>`",
    "dict-like": ":term:`dict-like <mapping>`",
    "mapping": ":term:`mapping`",
    "file-like": ":term:`file-like <file-like object>`",
    # special terms
    # "same type as caller": "*same type as caller*",  # does not work, yet
    # "same type as values": "*same type as values*",  # does not work, yet
    # stdlib type aliases
    "MutableMapping": "~collections.abc.MutableMapping",
    "sys.stdout": ":obj:`sys.stdout`",
    "timedelta": "~datetime.timedelta",
    "string": ":class:`string <str>`",
    # numpy terms
    "array_like": ":term:`array_like`",
    "array-like": ":term:`array-like <array_like>`",
    "scalar": ":term:`scalar`",
    "array": ":term:`array`",
    "hashable": ":term:`hashable <name>`",
    # matplotlib terms
    "color-like": ":py:func:`color-like <matplotlib.colors.is_color_like>`",
    "matplotlib colormap name": ":doc:matplotlib colormap name <Colormap reference>",
    "matplotlib axes object": ":py:class:`matplotlib axes object <matplotlib.axes.Axes>`",
    "colormap": ":py:class:`colormap <matplotlib.colors.Colormap>`",
    # objects without namespace
    "DataArray": "~xarray.DataArray",
    "Dataset": "~xarray.Dataset",
    "Variable": "~xarray.Variable",
    "ndarray": "~numpy.ndarray",
    "MaskedArray": "~numpy.ma.MaskedArray",
    "dtype": "~numpy.dtype",
    "ComplexWarning": "~numpy.ComplexWarning",
    "Index": "~pandas.Index",
    "MultiIndex": "~pandas.MultiIndex",
    "CategoricalIndex": "~pandas.CategoricalIndex",
    "TimedeltaIndex": "~pandas.TimedeltaIndex",
    "DatetimeIndex": "~pandas.DatetimeIndex",
    "Series": "~pandas.Series",
    "DataFrame": "~pandas.DataFrame",
    "Categorical": "~pandas.Categorical",
    "Path": "~~pathlib.Path",
    # objects with abbreviated namespace (from pandas)
    "pd.Index": "~pandas.Index",
    "pd.NaT": "~pandas.NaT",
}


# Numpydoc configurations

numpydoc_class_members_toctree = True
numpydoc_show_class_members = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates", sphinx_autosummary_accessors.templates_path]

# The suffix of source filenames.
# source_suffix = ".rst"


# The master toctree document.
master_doc = "index"

# General information about the project.
project = "xarray"
copyright = "2014-%s, xarray Developers" % datetime.datetime.now().year

# The short X.Y version.
version = xarray.__version__.split("+")[0]
# The full version, including alpha/beta/rc tags.
release = xarray.__version__

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = "%Y-%m-%d"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "**.ipynb_checkpoints"]


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output ----------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_book_theme"
html_title = ""

html_context = {
    "github_user": "pydata",
    "github_repo": "xarray",
    "github_version": "master",
    "doc_path": "doc",
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = dict(
    # analytics_id=''  this is configured in rtfd.io
    # canonical_url="",
    repository_url="https://github.com/pydata/xarray",
    use_edit_page_button=True,
    use_repository_button=True,
    use_issues_button=True,
    path_to_docs="doc/",
    home_page_in_toc=False,
    extra_navbar="",
    navbar_footer_text="",
    extra_footer='Theme by the <a href="https://ebp.jupyterbook.org">Executable Book Project</a>',
    twitter_url="https://twitter.com/xarray_devs",
    launch_buttons={"binderhub_url": "https://mybinder.org"},
)


# html_sidebars = {
#     "**": ["sbt-sidebar-footer.html", "sbt-sidebar-nav.html", "sidebar-search-bs.html"]
# }

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/dataset-diagram-logo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# redirects = {}

# configuration for sphinxext.opengraph
ogp_site_url = "https://xarray.pydata.org/en/latest/"
ogp_image = "https://xarray.pydata.org/en/stable/_static/dataset-diagram-logo.png"
ogp_custom_meta_tags = [
    '<meta name="twitter:card" content="summary_large_image" />',
    '<meta property="twitter:site" content="@xarray_dev />',
    '<meta name="image" property="og:image" content="https://xarray.pydata.org/en/stable/_static/dataset-diagram-logo.png">',
]

# myst_enable_extensions = [
#     "amsmath",
#     "colon_fence",
#     "deflist",
#     "dollarmath",
#     "html_image",
# ]
# myst_url_schemes = ("http", "https", "mailto")
# panels_add_bootstrap_css = False


# Sometimes the savefig directory doesn't exist and needs to be created
# https://github.com/ipython/ipython/issues/8733
# becomes obsolete when we can pin ipython>=5.2; see ci/requirements/doc.yml
ipython_savefig_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_build", "html", "_static"
)
if not os.path.exists(ipython_savefig_dir):
    os.makedirs(ipython_savefig_dir)


# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = today_fmt

# Output file base name for HTML help builder.
htmlhelp_basename = "xarraydoc"


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "iris": ("https://scitools-iris.readthedocs.io/en/latest", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "numba": ("https://numba.pydata.org/numba-doc/latest", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "dask": ("https://docs.dask.org/en/latest", None),
    "cftime": ("https://unidata.github.io/cftime", None),
    "rasterio": ("https://rasterio.readthedocs.io/en/latest", None),
    "sparse": ("https://sparse.pydata.org/en/latest/", None),
}


def escape_underscores(string):
    return string.replace("_", r"\_")


def setup(app):
    DEFAULT_FILTERS["escape_underscores"] = escape_underscores
    return dict(version=version, parallel_read_safe=False, parallel_write_safe=True)
