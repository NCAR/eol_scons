# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from SCons.Environment import Environment

import eol_scons.tools.qt5 as qt5


def test_replace_drive():
    env = Environment(tools=['default'])
    b = env.File("C:/b")
    c = env.File("/c/etc")
    u = env.Dir("/tmp")
    l1 = ["C:/a", b, c, u, "C:"]
    l2 = l1
    qt5.replace_drive_specs(l1)
    assert l1 == ["/c/a", "/c/b", c, u, "/c"]
    assert l2 == l1
