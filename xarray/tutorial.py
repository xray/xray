"""
Useful for:

* users learning xarray
* building tutorials in the documentation.

"""
import hashlib
import pathlib
import shutil
import tempfile
from contextlib import contextmanager, suppress

import numpy as np
import requests

from .backends.api import open_dataset as _open_dataset
from .backends.rasterio_ import open_rasterio as _open_rasterio
from .core.dataarray import DataArray
from .core.dataset import Dataset
from .vendor import appdirs

_default_cache_dir = pathlib.Path(appdirs.user_cache_dir("xarray_tutorial_data"))


def check_md5sum(content, checksum):
    md5 = hashlib.md5()
    md5.update(content)
    md5sum = md5.hexdigest()

    return md5sum == checksum


# based on https://stackoverflow.com/a/29491523
@contextmanager
def open_atomic(path, mode=None):
    folder = path.parent
    prefix = f".{path.name}"

    try:
        f = tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, delete=False)
        temporary_path = pathlib.Path(f.name)

        yield f

        temporary_path.rename(path)
    except Exception:
        # switch to path.unlink(missing_ok=True) for Python 3.8+
        with suppress(FileNotFoundError):
            temporary_path.unlink()
        raise


def download_to(url, path):
    # based on https://stackoverflow.com/a/39217788
    with open_atomic(path, mode="wb") as f:
        with requests.get(url, stream=True) as r:
            if r.status_code != requests.codes.ok:
                raise OSError(f"download failed: {r.reason}")

            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)


def open_rasterio(
    name,
    cache=True,
    cache_dir=_default_cache_dir,
    github_url="https://github.com/mapbox/rasterio",
    branch="master",
    **kws,
):
    """
    Open a rasterio dataset from rasterio's online repository (requires internet).

    If a local copy is found then always use that to avoid network traffic.

    Parameters
    ----------
    name : str
        Name of the file containing the dataset. If no suffix is given, assumed
        to be TIF ('.tif' is appended)
        e.g. 'RGB.byte'
    cache_dir : path-like, optional
        The directory in which to search for and write cached data.
    cache : boolean, optional
        If True, then cache data locally for use on subsequent calls
    github_url : string
        Github repository where the data is stored
    branch : string
        The git branch to download from
    kws : dict, optional
        Passed to xarray.open_dataset

    See Also
    --------
    xarray.open_rasterio
    xarray.tutorial.open_dataset

    """
    if isinstance(cache_dir, str):
        cache_dir = pathlib.Path(cache_dir)

    if not cache_dir.is_dir():
        cache_dir.mkdir()

    default_extension = ".tif"

    if cache:
        path = cache_dir / name
        # need to always do that, otherwise we might close the
        # path using the context manager
        cache_dir = pathlib.Path(cache_dir)
    else:
        cache_dir = tempfile.TemporaryDirectory()
        path = pathlib.Path(cache_dir.name) / name

    if not path.suffix:
        path = path.with_suffix(default_extension)
    elif path.suffix == ".byte":
        path = path.with_name(name + default_extension)

    if cache and path.is_file():
        return _open_rasterio(path, **kws)

    url = f"{github_url}/raw/{branch}/tests/data/{path.name}"
    # if cache_dir points to a temporary directory, make sure it is
    # deleted afterwards
    with cache_dir:
        download_to(url, path)
        return _open_rasterio(path, **kws)


# idea borrowed from Seaborn
def open_dataset(
    name,
    cache=True,
    cache_dir=_default_cache_dir,
    github_url="https://github.com/pydata/xarray-data",
    branch="master",
    **kws,
):
    """
    Open a dataset from the online repository (requires internet).

    If a local copy is found then always use that to avoid network traffic.

    Parameters
    ----------
    name : str
        Name of the file containing the dataset. If no suffix is given, assumed
        to be netCDF ('.nc' is appended)
        e.g. 'air_temperature'
    cache_dir : path-like, optional
        The directory in which to search for and write cached data.
    cache : boolean, optional
        If True, then cache data locally for use on subsequent calls
    github_url : string
        Github repository where the data is stored
    branch : string
        The git branch to download from
    kws : dict, optional
        Passed to xarray.open_dataset

    See Also
    --------
    xarray.open_dataset
    xarray.tutorial.open_rasterio

    """
    if isinstance(cache_dir, str):
        cache_dir = pathlib.Path(cache_dir)

    def construct_url(full_name):
        return f"{github_url}/raw/{branch}/{full_name}"

    if not cache_dir.is_dir():
        cache_dir.mkdir()

    default_extension = ".nc"

    if cache:
        path = cache_dir / name
        # need to always do that, otherwise we might close the
        # path using the context manager
        cache_dir = pathlib.Path(cache_dir)
    else:
        cache_dir = tempfile.TemporaryDirectory()
        path = pathlib.Path(cache_dir.name) / name

    if not path.suffix:
        path = path.with_suffix(default_extension)

    if cache and path.is_file():
        return _open_dataset(path, **kws)

    # if cache_dir points to a temporary directory, make sure it is
    # deleted afterwards
    with cache_dir:
        download_to(construct_url(path.name), path)

        # verify the checksum (md5 guards only against transport corruption)
        md5_path = path.with_name(path.name + ".md5")
        download_to(construct_url(md5_path.name), md5_path)
        if not check_md5sum(path.read_bytes(), md5_path.read_text()):
            path.unlink()
            md5_path.unlink()
            msg = """
            MD5 checksum does not match, try downloading dataset again.
            """
            raise OSError(msg)

        return _open_dataset(path, **kws)


def load_dataset(*args, **kwargs):
    """
    Open, load into memory, and close a dataset from the online repository
    (requires internet).

    See Also
    --------
    open_dataset
    """
    with open_dataset(*args, **kwargs) as ds:
        return ds.load()


def scatter_example_dataset():
    A = DataArray(
        np.zeros([3, 11, 4, 4]),
        dims=["x", "y", "z", "w"],
        coords=[
            np.arange(3),
            np.linspace(0, 1, 11),
            np.arange(4),
            0.1 * np.random.randn(4),
        ],
    )
    B = 0.1 * A.x ** 2 + A.y ** 2.5 + 0.1 * A.z * A.w
    A = -0.1 * A.x + A.y / (5 + A.z) + A.w
    ds = Dataset({"A": A, "B": B})
    ds["w"] = ["one", "two", "three", "five"]

    ds.x.attrs["units"] = "xunits"
    ds.y.attrs["units"] = "yunits"
    ds.z.attrs["units"] = "zunits"
    ds.w.attrs["units"] = "wunits"

    ds.A.attrs["units"] = "Aunits"
    ds.B.attrs["units"] = "Bunits"

    return ds
