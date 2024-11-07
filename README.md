# xarray: N-D labeled arrays and datasets

[![CI](https://github.com/pydata/xarray/workflows/CI/badge.svg?branch=main)](https://github.com/pydata/xarray/actions?query=workflow%3ACI)
[![Code coverage](https://codecov.io/gh/pydata/xarray/branch/main/graph/badge.svg?flag=unittests)](https://codecov.io/gh/pydata/xarray)
[![Docs](https://readthedocs.org/projects/xray/badge/?version=latest)](https://docs.xarray.dev/)
[![Benchmarked with asv](https://img.shields.io/badge/benchmarked%20by-asv-green.svg?style=flat)](https://pandas.pydata.org/speed/xarray/)
[![Available on pypi](https://img.shields.io/pypi/v/xarray.svg)](https://pypi.python.org/pypi/xarray/)
[![Formatted with black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11183201.svg)](https://doi.org/10.5281/zenodo.11183201)
[![Examples on binder](https://img.shields.io/badge/launch-binder-579ACA.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFkAAABZCAMAAABi1XidAAAB8lBMVEX///9XmsrmZYH1olJXmsr1olJXmsrmZYH1olJXmsr1olJXmsrmZYH1olL1olJXmsr1olJXmsrmZYH1olL1olJXmsrmZYH1olJXmsr1olL1olJXmsrmZYH1olL1olJXmsrmZYH1olL1olL0nFf1olJXmsrmZYH1olJXmsq8dZb1olJXmsrmZYH1olJXmspXmspXmsr1olL1olJXmsrmZYH1olJXmsr1olL1olJXmsrmZYH1olL1olLeaIVXmsrmZYH1olL1olL1olJXmsrmZYH1olLna31Xmsr1olJXmsr1olJXmsrmZYH1olLqoVr1olJXmsr1olJXmsrmZYH1olL1olKkfaPobXvviGabgadXmsqThKuofKHmZ4Dobnr1olJXmsr1olJXmspXmsr1olJXmsrfZ4TuhWn1olL1olJXmsqBi7X1olJXmspZmslbmMhbmsdemsVfl8ZgmsNim8Jpk8F0m7R4m7F5nLB6jbh7jbiDirOEibOGnKaMhq+PnaCVg6qWg6qegKaff6WhnpKofKGtnomxeZy3noG6dZi+n3vCcpPDcpPGn3bLb4/Mb47UbIrVa4rYoGjdaIbeaIXhoWHmZYHobXvpcHjqdHXreHLroVrsfG/uhGnuh2bwj2Hxk17yl1vzmljzm1j0nlX1olL3AJXWAAAAbXRSTlMAEBAQHx8gICAuLjAwMDw9PUBAQEpQUFBXV1hgYGBkcHBwcXl8gICAgoiIkJCQlJicnJ2goKCmqK+wsLC4usDAwMjP0NDQ1NbW3Nzg4ODi5+3v8PDw8/T09PX29vb39/f5+fr7+/z8/Pz9/v7+zczCxgAABC5JREFUeAHN1ul3k0UUBvCb1CTVpmpaitAGSLSpSuKCLWpbTKNJFGlcSMAFF63iUmRccNG6gLbuxkXU66JAUef/9LSpmXnyLr3T5AO/rzl5zj137p136BISy44fKJXuGN/d19PUfYeO67Znqtf2KH33Id1psXoFdW30sPZ1sMvs2D060AHqws4FHeJojLZqnw53cmfvg+XR8mC0OEjuxrXEkX5ydeVJLVIlV0e10PXk5k7dYeHu7Cj1j+49uKg7uLU61tGLw1lq27ugQYlclHC4bgv7VQ+TAyj5Zc/UjsPvs1sd5cWryWObtvWT2EPa4rtnWW3JkpjggEpbOsPr7F7EyNewtpBIslA7p43HCsnwooXTEc3UmPmCNn5lrqTJxy6nRmcavGZVt/3Da2pD5NHvsOHJCrdc1G2r3DITpU7yic7w/7Rxnjc0kt5GC4djiv2Sz3Fb2iEZg41/ddsFDoyuYrIkmFehz0HR2thPgQqMyQYb2OtB0WxsZ3BeG3+wpRb1vzl2UYBog8FfGhttFKjtAclnZYrRo9ryG9uG/FZQU4AEg8ZE9LjGMzTmqKXPLnlWVnIlQQTvxJf8ip7VgjZjyVPrjw1te5otM7RmP7xm+sK2Gv9I8Gi++BRbEkR9EBw8zRUcKxwp73xkaLiqQb+kGduJTNHG72zcW9LoJgqQxpP3/Tj//c3yB0tqzaml05/+orHLksVO+95kX7/7qgJvnjlrfr2Ggsyx0eoy9uPzN5SPd86aXggOsEKW2Prz7du3VID3/tzs/sSRs2w7ovVHKtjrX2pd7ZMlTxAYfBAL9jiDwfLkq55Tm7ifhMlTGPyCAs7RFRhn47JnlcB9RM5T97ASuZXIcVNuUDIndpDbdsfrqsOppeXl5Y+XVKdjFCTh+zGaVuj0d9zy05PPK3QzBamxdwtTCrzyg/2Rvf2EstUjordGwa/kx9mSJLr8mLLtCW8HHGJc2R5hS219IiF6PnTusOqcMl57gm0Z8kanKMAQg0qSyuZfn7zItsbGyO9QlnxY0eCuD1XL2ys/MsrQhltE7Ug0uFOzufJFE2PxBo/YAx8XPPdDwWN0MrDRYIZF0mSMKCNHgaIVFoBbNoLJ7tEQDKxGF0kcLQimojCZopv0OkNOyWCCg9XMVAi7ARJzQdM2QUh0gmBozjc3Skg6dSBRqDGYSUOu66Zg+I2fNZs/M3/f/Grl/XnyF1Gw3VKCez0PN5IUfFLqvgUN4C0qNqYs5YhPL+aVZYDE4IpUk57oSFnJm4FyCqqOE0jhY2SMyLFoo56zyo6becOS5UVDdj7Vih0zp+tcMhwRpBeLyqtIjlJKAIZSbI8SGSF3k0pA3mR5tHuwPFoa7N7reoq2bqCsAk1HqCu5uvI1n6JuRXI+S1Mco54YmYTwcn6Aeic+kssXi8XpXC4V3t7/ADuTNKaQJdScAAAAAElFTkSuQmCC)](https://mybinder.org/v2/gh/pydata/xarray/main?urlpath=lab/tree/doc/examples/weather-data.ipynb)
[![Twitter](https://img.shields.io/twitter/follow/xarray_dev?style=social)](https://twitter.com/xarray_dev)
[![Gurubase](https://img.shields.io/badge/Gurubase-Ask%20xarray%20Guru-006BFF)](https://gurubase.io/g/xarray)

**xarray** (pronounced "ex-array", formerly known as **xray**) is an open source project and Python
package that makes working with labelled multi-dimensional arrays
simple, efficient, and fun!

Xarray introduces labels in the form of dimensions, coordinates and
attributes on top of raw [NumPy](https://www.numpy.org)-like arrays,
which allows for a more intuitive, more concise, and less error-prone
developer experience. The package includes a large and growing library
of domain-agnostic functions for advanced analytics and visualization
with these data structures.

Xarray was inspired by and borrows heavily from
[pandas](https://pandas.pydata.org), the popular data analysis package
focused on labelled tabular data. It is particularly tailored to working
with [netCDF](https://www.unidata.ucar.edu/software/netcdf) files, which
were the source of xarray\'s data model, and integrates tightly with
[dask](https://dask.org) for parallel computing.

## Why xarray?

Multi-dimensional (a.k.a. N-dimensional, ND) arrays (sometimes called
"tensors") are an essential part of computational science. They are
encountered in a wide range of fields, including physics, astronomy,
geoscience, bioinformatics, engineering, finance, and deep learning. In
Python, [NumPy](https://www.numpy.org) provides the fundamental data
structure and API for working with raw ND arrays. However, real-world
datasets are usually more than just raw numbers; they have labels which
encode information about how the array values map to locations in space,
time, etc.

Xarray doesn\'t just keep track of labels on arrays \-- it uses them to
provide a powerful and concise interface. For example:

- Apply operations over dimensions by name: `x.sum('time')`.
- Select values by label instead of integer location:
  `x.loc['2014-01-01']` or `x.sel(time='2014-01-01')`.
- Mathematical operations (e.g., `x - y`) vectorize across multiple
  dimensions (array broadcasting) based on dimension names, not shape.
- Flexible split-apply-combine operations with groupby:
  `x.groupby('time.dayofyear').mean()`.
- Database like alignment based on coordinate labels that smoothly
  handles missing values: `x, y = xr.align(x, y, join='outer')`.
- Keep track of arbitrary metadata in the form of a Python dictionary:
  `x.attrs`.

## Documentation

Learn more about xarray in its official documentation at
<https://docs.xarray.dev/>.

Try out an [interactive Jupyter
notebook](https://mybinder.org/v2/gh/pydata/xarray/main?urlpath=lab/tree/doc/examples/weather-data.ipynb).

## Contributing

You can find information about contributing to xarray at our
[Contributing
page](https://docs.xarray.dev/en/stable/contributing.html).

## Get in touch

- Ask usage questions ("How do I?") on
  [GitHub Discussions](https://github.com/pydata/xarray/discussions).
- Report bugs, suggest features or view the source code [on
  GitHub](https://github.com/pydata/xarray).
- For less well defined questions or ideas, or to announce other
  projects of interest to xarray users, use the [mailing
  list](https://groups.google.com/forum/#!forum/xarray).

## NumFOCUS

<img src="https://numfocus.org/wp-content/uploads/2017/07/NumFocus_LRG.png" width="200" href="https://numfocus.org/">

Xarray is a fiscally sponsored project of
[NumFOCUS](https://numfocus.org), a nonprofit dedicated to supporting
the open source scientific computing community. If you like Xarray and
want to support our mission, please consider making a
[donation](https://numfocus.org/donate-to-xarray) to support
our efforts.

## History

Xarray is an evolution of an internal tool developed at [The Climate
Corporation](http://climate.com/). It was originally written by Climate
Corp researchers Stephan Hoyer, Alex Kleeman and Eugene Brevdo and was
released as open source in May 2014. The project was renamed from
"xray" in January 2016. Xarray became a fiscally sponsored project of
[NumFOCUS](https://numfocus.org) in August 2018.

## Contributors

Thanks to our many contributors!

[![Contributors](https://contrib.rocks/image?repo=pydata/xarray)](https://github.com/pydata/xarray/graphs/contributors)

## License

Copyright 2014-2023, xarray Developers

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License. You may
obtain a copy of the License at

<https://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Xarray bundles portions of pandas, NumPy and Seaborn, all of which are
available under a "3-clause BSD" license:

- pandas: `setup.py`, `xarray/util/print_versions.py`
- NumPy: `xarray/core/npcompat.py`
- Seaborn: `_determine_cmap_params` in `xarray/core/plot/utils.py`

Xarray also bundles portions of CPython, which is available under the
"Python Software Foundation License" in `xarray/core/pycompat.py`.

Xarray uses icons from the icomoon package (free version), which is
available under the "CC BY 4.0" license.

The full text of these licenses are included in the licenses directory.
