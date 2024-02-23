
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
