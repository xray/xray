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
import inspect
import os
import pathlib
import subprocess
import sys
from contextlib import suppress
from textwrap import dedent, indent

import sphinx_autosummary_accessors
import yaml
from sphinx.application import Sphinx
from sphinx.util import logging

import xarray

LOGGER = logging.getLogger("conf")

allowed_failures = set()

print("python exec:", sys.executable)
print("sys.path:", sys.path)

if "CONDA_DEFAULT_ENV" in os.environ or "conda" in sys.executable:
    print("conda environment:")
    subprocess.run([os.environ.get("CONDA_EXE", "conda"), "list"])
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

nbsphinx_allow_errors = True

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
    "sphinx.ext.linkcode",
    "sphinxext.opengraph",
    "sphinx_copybutton",
    "sphinxext.rediraffe",
    "sphinx_design",
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
nbsphinx_prolog = """
{% set docname = env.doc2path(env.docname, base=None) %}

You can run this notebook in a `live session <https://mybinder.org/v2/gh/pydata/xarray/doc/examples/main?urlpath=lab/tree/doc/{{ docname }}>`_ |Binder| or view it `on Github <https://github.com/pydata/xarray/blob/main/doc/{{ docname }}>`_.

.. |Binder| image:: https://mybinder.org/badge.svg
   :target: https://mybinder.org/v2/gh/pydata/xarray/main?urlpath=lab/tree/doc/{{ docname }}
"""

autosummary_generate = True
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
    "path-like": ":term:`path-like <path-like object>`",
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
    "matplotlib colormap name": ":doc:`matplotlib colormap name <matplotlib:gallery/color/colormap_reference>`",
    "matplotlib axes object": ":py:class:`matplotlib axes object <matplotlib.axes.Axes>`",
    "colormap": ":py:class:`colormap <matplotlib.colors.Colormap>`",
    # objects without namespace: xarray
    "DataArray": "~xarray.DataArray",
    "Dataset": "~xarray.Dataset",
    "Variable": "~xarray.Variable",
    "DatasetGroupBy": "~xarray.core.groupby.DatasetGroupBy",
    "DataArrayGroupBy": "~xarray.core.groupby.DataArrayGroupBy",
    # objects without namespace: numpy
    "ndarray": "~numpy.ndarray",
    "MaskedArray": "~numpy.ma.MaskedArray",
    "dtype": "~numpy.dtype",
    "ComplexWarning": "~numpy.ComplexWarning",
    # objects without namespace: pandas
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


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates", sphinx_autosummary_accessors.templates_path]

# The suffix of source filenames.
# source_suffix = ".rst"


# The master toctree document.
master_doc = "index"

# General information about the project.
project = "xarray"
copyright = f"2014-{datetime.datetime.now().year}, xarray Developers"

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
    "github_version": "main",
    "doc_path": "doc",
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = dict(
    # analytics_id=''  this is configured in rtfd.io
    # canonical_url="",
    repository_url="https://github.com/pydata/xarray",
    repository_branch="main",
    path_to_docs="doc",
    use_edit_page_button=True,
    use_repository_button=True,
    use_issues_button=True,
    home_page_in_toc=False,
    extra_navbar="",
    navbar_footer_text="",
    extra_footer="""<p>Xarray is a fiscally sponsored project of <a href="https://numfocus.org">NumFOCUS</a>,
    a nonprofit dedicated to supporting the open-source scientific computing community.<br>
    Theme by the <a href="https://ebp.jupyterbook.org">Executable Book Project</a></p>""",
    twitter_url="https://twitter.com/xarray_devs",
)


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
html_css_files = ["style.css"]


# configuration for sphinxext.opengraph
ogp_site_url = "https://docs.xarray.dev/en/latest/"
ogp_image = "https://docs.xarray.dev/en/stable/_static/dataset-diagram-logo.png"
ogp_custom_meta_tags = [
    '<meta name="twitter:card" content="summary_large_image" />',
    '<meta property="twitter:site" content="@xarray_dev" />',
    '<meta name="image" property="og:image" content="https://docs.xarray.dev/en/stable/_static/dataset-diagram-logo.png" />',
]

# Redirects for pages that were moved to new locations

rediraffe_redirects = {
    "terminology.rst": "user-guide/terminology.rst",
    "data-structures.rst": "user-guide/data-structures.rst",
    "indexing.rst": "user-guide/indexing.rst",
    "interpolation.rst": "user-guide/interpolation.rst",
    "computation.rst": "user-guide/computation.rst",
    "groupby.rst": "user-guide/groupby.rst",
    "reshaping.rst": "user-guide/reshaping.rst",
    "combining.rst": "user-guide/combining.rst",
    "time-series.rst": "user-guide/time-series.rst",
    "weather-climate.rst": "user-guide/weather-climate.rst",
    "pandas.rst": "user-guide/pandas.rst",
    "io.rst": "user-guide/io.rst",
    "dask.rst": "user-guide/dask.rst",
    "plotting.rst": "user-guide/plotting.rst",
    "duckarrays.rst": "user-guide/duckarrays.rst",
    "related-projects.rst": "ecosystem.rst",
    "faq.rst": "getting-started-guide/faq.rst",
    "why-xarray.rst": "getting-started-guide/why-xarray.rst",
    "installing.rst": "getting-started-guide/installing.rst",
    "quick-overview.rst": "getting-started-guide/quick-overview.rst",
}

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
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "numba": ("https://numba.readthedocs.io/en/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "dask": ("https://docs.dask.org/en/latest", None),
    "cftime": ("https://unidata.github.io/cftime", None),
    "rasterio": ("https://rasterio.readthedocs.io/en/latest", None),
    "sparse": ("https://sparse.pydata.org/en/latest/", None),
}


# based on numpy doc/source/conf.py
def linkcode_resolve(domain, info):
    """
    Determine the URL corresponding to Python object
    """
    if domain != "py":
        return None

    modname = info["module"]
    fullname = info["fullname"]

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split("."):
        try:
            obj = getattr(obj, part)
        except AttributeError:
            return None

    try:
        fn = inspect.getsourcefile(inspect.unwrap(obj))
    except TypeError:
        fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except OSError:
        lineno = None

    if lineno:
        linespec = f"#L{lineno}-L{lineno + len(source) - 1}"
    else:
        linespec = ""

    fn = os.path.relpath(fn, start=os.path.dirname(xarray.__file__))

    if "+" in xarray.__version__:
        return f"https://github.com/pydata/xarray/blob/main/xarray/{fn}{linespec}"
    else:
        return (
            f"https://github.com/pydata/xarray/blob/"
            f"v{xarray.__version__}/xarray/{fn}{linespec}"
        )


def html_page_context(app, pagename, templatename, context, doctree):
    # Disable edit button for docstring generated pages
    if "generated" in pagename:
        context["theme_use_edit_page_button"] = False


def update_gallery(app: Sphinx):
    """Update the gallery page."""

    LOGGER.info("Updating gallery page...")

    gallery = yaml.safe_load(pathlib.Path(app.srcdir, "gallery.yml").read_bytes())

    for key in gallery:
        items = [
            f"""
         .. grid-item-card::
            :text-align: center
            :link: {item['path']}

            .. image:: {item['thumbnail']}
                :alt: {item['title']}
            +++
            {item['title']}
            """
            for item in gallery[key]
        ]

        items_md = indent(dedent("\n".join(items)), prefix="    ")
        markdown = f"""
.. grid:: 1 2 2 2
    :gutter: 2

    {items_md}
    """
        pathlib.Path(app.srcdir, f"{key}-gallery.txt").write_text(markdown)
        LOGGER.info(f"{key} gallery page updated.")
    LOGGER.info("Gallery page updated.")


def update_videos(app: Sphinx):
    """Update the videos page."""

    LOGGER.info("Updating videos page...")

    videos = yaml.safe_load(pathlib.Path(app.srcdir, "videos.yml").read_bytes())

    items = []
    for video in videos:
        authors = " | ".join(video["authors"])
        item = f"""
.. grid-item-card:: {" ".join(video["title"].split())}
    :text-align: center

    .. raw:: html

        {video['src']}
    +++
    {authors}
        """
        items.append(item)

    items_md = indent(dedent("\n".join(items)), prefix="    ")
    markdown = f"""
.. grid:: 1 2 2 2
    :gutter: 2

    {items_md}
    """
    pathlib.Path(app.srcdir, "videos-gallery.txt").write_text(markdown)
    LOGGER.info("Videos page updated.")


def setup(app: Sphinx):
    app.connect("html-page-context", html_page_context)
    app.connect("builder-inited", update_gallery)
    app.connect("builder-inited", update_videos)
