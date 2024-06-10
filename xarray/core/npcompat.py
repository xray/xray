# Copyright (c) 2005-2011, NumPy Developers.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

#     * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.

#     * Neither the name of the NumPy Developers nor the names of any
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import numpy as np

try:
    # requires numpy>=2.0
    from numpy import isdtype  # type: ignore[attr-defined,unused-ignore]
except ImportError:

    dtype_kinds = {
        "bool": np.bool_,
        "signed integer": np.signedinteger,
        "unsigned integer": np.unsignedinteger,
        "integral": np.integer,
        "real floating": np.floating,
        "complex floating": np.complexfloating,
        "numeric": np.number,
    }

    def isdtype(dtype, kind):
        kinds = kind if isinstance(kind, tuple) else (kind,)

        unknown_dtypes = [kind for kind in kinds if kind not in dtype_kinds]
        if unknown_dtypes:
            raise ValueError(f"unknown dtype kinds: {unknown_dtypes}")

        # verified the dtypes already, no need to check again
        translated_kinds = [dtype_kinds[kind] for kind in kinds]
        if isinstance(dtype, np.generic):
            return any(isinstance(dtype, kind) for kind in translated_kinds)
        else:
            return any(np.issubdtype(dtype, kind) for kind in translated_kinds)


def is_weak_scalar_type(t):
    return isinstance(t, (bool, int, float, complex, str, bytes))


def _future_array_api_result_type(*arrays_and_dtypes, xp):
    strongly_dtyped = [t for t in arrays_and_dtypes if not is_weak_scalar_type(t)]
    weakly_dtyped = [t for t in arrays_and_dtypes if is_weak_scalar_type(t)]

    dtype = xp.result_type(*strongly_dtyped)
    if not weakly_dtyped:
        return dtype

    possible_dtypes = {
        complex: "complex64",
        float: "float32",
        int: "int8",
        bool: "bool",
        str: "str",
        bytes: "bytes",
    }
    dtypes = [possible_dtypes.get(type(x), "object") for x in weakly_dtyped]

    return xp.result_type(dtype, *dtypes)


def result_type(*arrays_and_dtypes, xp) -> np.dtype:
    if xp is np or any(
        isinstance(getattr(t, "dtype", t), np.dtype) for t in arrays_and_dtypes
    ):
        return xp.result_type(*arrays_and_dtypes)
    else:
        return _future_array_api_result_type(*arrays_and_dtypes, xp=xp)
