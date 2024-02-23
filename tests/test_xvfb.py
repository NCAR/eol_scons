# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import time
import pytest

from eol_scons.xvfb import Xvfb


def test_xvfb_stop():
    xvfb = Xvfb()
    if not xvfb.detected():
        pytest.skip("Xvfb not installed.")
    xvfb.start()
    pid = xvfb.proc.pid
    assert pid
    time.sleep(1)
    xvfb.stop()
