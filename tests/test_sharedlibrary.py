# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import eol_scons.tools.sharedlibrary as shl


def test_versions():
    rev = shl._extract_shlibversions_from_tag("V3.2")
    assert rev == (3, 2)
    rev = shl._extract_shlibversions_from_tag("v1.99-alpha")
    assert rev == (1, 99)
    rev = shl._extract_shlibversions_from_tag("v1.alpha")
    assert rev is None
    rev = shl._extract_shlibversions_from_tag("v10.12.02")
    assert rev == (10, 12)
    rev = shl._extract_shlibversions_from_tag("v10.02")
    assert rev == (10, 2)
    rev = shl._extract_shlibversions_from_tag("xv10.02")
    assert rev is None
