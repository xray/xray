
from xarray.backends.api import _get_default_engine
from . import requires_netCDF4, requires_pynio, requires_scipy


@requires_netCDF4
@requires_scipy
@requires_pynio
def test__get_default_engine():
    engine_remote = _get_default_engine('http://example.org/test.nc',
                                        allow_remote=True)
    assert engine_remote == 'netcdf4'

    engine_gz = _get_default_engine('/example.gz')
    assert engine_gz == 'scipy'

    engine_grib = _get_default_engine('/example.grib')
    assert engine_grib == 'pynio'

    engine_default = _get_default_engine('/example')
    assert engine_default == 'netcdf4'
