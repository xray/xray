"""Fetch from conda database all available versions of the xarray dependencies and their
publication date. Compare it against requirements/py36-min-all-deps.yml to verify the
policy on obsolete dependencies is being followed. Print a pretty report :)
"""
import itertools
import sys
from datetime import datetime, timedelta
from typing import Dict, Iterator, Optional, Tuple

import conda.api
import yaml

CHANNELS = ["conda-forge", "defaults"]
IGNORE_DEPS = {
    "black",
    "coveralls",
    "flake8",
    "hypothesis",
    "isort",
    "mypy",
    "pip",
    "pytest",
    "pytest-cov",
    "pytest-env",
    "pytest-xdist",
}

POLICY_MONTHS = {"python": 42, "numpy": 24, "setuptools": 42}
POLICY_MONTHS_DEFAULT = 12
POLICY_OVERRIDE = {
    # dask < 2.9 has trouble with nan-reductions
    # TODO remove this special case and the matching note in installing.rst
    #      after January 2021.
    "dask": (2, 9),
    "distributed": (2, 9),
    # setuptools-scm doesn't work with setuptools < 36.7 (Nov 2017).
    # The conda metadata is malformed for setuptools < 38.4 (Jan 2018)
    # (it's missing a timestamp which prevents this tool from working).
    # setuptools < 40.4 (Sep 2018) from conda-forge cannot be installed into a py37
    # environment
    # TODO remove this special case and the matching note in installing.rst
    #      after March 2022.
    "setuptools": (40, 4),
}
has_errors = False


def error(msg: str) -> None:
    global has_errors
    has_errors = True
    print("ERROR:", msg)


def warning(msg: str) -> None:
    print("WARNING:", msg)


def parse_requirements(fname) -> Iterator[Tuple[str, int, int, Optional[int]]]:
    """Load requirements/py36-min-all-deps.yml

    Yield (package name, major version, minor version, [patch version])
    """
    global has_errors

    with open(fname) as fh:
        contents = yaml.safe_load(fh)
    for row in contents["dependencies"]:
        if isinstance(row, dict) and list(row) == ["pip"]:
            continue
        pkg, eq, version = row.partition("=")
        if pkg.rstrip("<>") in IGNORE_DEPS:
            continue
        if pkg.endswith("<") or pkg.endswith(">") or eq != "=":
            error("package should be pinned with exact version: " + row)
            continue

        try:
            version_tup = tuple(int(x) for x in version.split("."))
        except ValueError:
            raise ValueError("non-numerical version: " + row)

        if len(version_tup) == 2:
            yield (pkg, *version_tup, None)  # type: ignore
        elif len(version_tup) == 3:
            yield (pkg, *version_tup)  # type: ignore
        else:
            raise ValueError("expected major.minor or major.minor.patch: " + row)


def query_conda(pkg: str) -> Dict[Tuple[int, int], datetime]:
    """Query the conda repository for a specific package

    Return map of {(major version, minor version): publication date}
    """

    def metadata(entry):
        name = entry.name
        filename = entry.fn
        version = entry.version
        filename_version = filename[len(name) :].split("-")[1]

        if version != filename_version:
            raise RuntimeError(
                f"{entry.name}: version != filename version: {version} vs {filename_version}"
            )

        time = datetime.fromtimestamp(entry.timestamp) if entry.timestamp != 0 else None
        major, minor = map(int, version.split(".")[:2])

        return (major, minor), time

    raw_data = conda.api.SubdirData.query_all(pkg, channels=CHANNELS)
    records = sorted([metadata(entry) for entry in raw_data], key=lambda x: x[0])

    release_dates = {
        version: [time for _, time in group if time is not None]
        for version, group in itertools.groupby(records, key=lambda x: x[0])
    }
    out = {version: min(dates) for version, dates in release_dates.items() if dates}

    # Hardcoded fix to work around incorrect dates in conda
    if pkg == "python":
        out.update(
            {
                (2, 7): datetime(2010, 6, 3),
                (3, 5): datetime(2015, 9, 13),
                (3, 6): datetime(2016, 12, 23),
                (3, 7): datetime(2018, 6, 27),
                (3, 8): datetime(2019, 10, 14),
            }
        )

    return out


def process_pkg(
    pkg: str, req_major: int, req_minor: int, req_patch: Optional[int]
) -> Tuple[str, str, str, str, str, str]:
    """Compare package version from requirements file to available versions in conda.
    Return row to build pandas dataframe:

    - package name
    - major.minor.[patch] version in requirements file
    - publication date of version in requirements file (YYYY-MM-DD)
    - major.minor version suggested by policy
    - publication date of version suggested by policy (YYYY-MM-DD)
    - status ("<", "=", "> (!)")
    """
    print("Analyzing %s..." % pkg)
    versions = query_conda(pkg)

    try:
        req_published = versions[req_major, req_minor]
    except KeyError:
        error("not found in conda: " + pkg)
        return pkg, fmt_version(req_major, req_minor, req_patch), "-", "-", "-", "(!)"

    policy_months = POLICY_MONTHS.get(pkg, POLICY_MONTHS_DEFAULT)
    policy_published = datetime.now() - timedelta(days=policy_months * 30)

    policy_major = req_major
    policy_minor = req_minor
    policy_published_actual = req_published
    for (major, minor), published in reversed(sorted(versions.items())):
        if published < policy_published:
            break
        policy_major = major
        policy_minor = minor
        policy_published_actual = published

    try:
        policy_major, policy_minor = POLICY_OVERRIDE[pkg]
    except KeyError:
        pass

    if (req_major, req_minor) < (policy_major, policy_minor):
        status = "<"
    elif (req_major, req_minor) > (policy_major, policy_minor):
        status = "> (!)"
        error("Package is too new: " + pkg)
    else:
        status = "="

    if req_patch is not None:
        warning("patch version should not appear in requirements file: " + pkg)
        status += " (w)"

    return (
        pkg,
        fmt_version(req_major, req_minor, req_patch),
        req_published.strftime("%Y-%m-%d"),
        fmt_version(policy_major, policy_minor),
        policy_published_actual.strftime("%Y-%m-%d"),
        status,
    )


def fmt_version(major: int, minor: int, patch: int = None) -> str:
    if patch is None:
        return f"{major}.{minor}"
    else:
        return f"{major}.{minor}.{patch}"


def main() -> None:
    fname = sys.argv[1]
    rows = [
        process_pkg(pkg, major, minor, patch)
        for pkg, major, minor, patch in parse_requirements(fname)
    ]

    print("Package       Required             Policy               Status")
    print("------------- -------------------- -------------------- ------")
    fmt = "{:13} {:7} ({:10}) {:7} ({:10}) {}"
    for row in rows:
        print(fmt.format(*row))

    assert not has_errors


if __name__ == "__main__":
    main()
