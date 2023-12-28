
import subprocess as sp
from pathlib import Path
import logging

import eol_scons
from SCons.Script import Environment

import pytest
import conftest


# manufacturer our own __file__since that is not available when read as a
# SConstruct file
_this_file = "test_testing.py"


logger = logging.getLogger(_this_file)


_log_line = 'This line only in log file.'
_all_lines = 'Lots of output.'


# SConstruct file begins here
if not conftest.called_from_test:
    print("Executing SConstruct %s" % (_this_file))
    env = Environment(tools=['default', 'testing'])
    # should be able to create a test target which logs the output
    xtest = env.TestLog('xtest', [], f"@echo {_log_line}")

    # if we override the patterns, then all lines appear.
    log_action = env.LogAction([f"@echo {_all_lines}"], 'junk.log', [])
    target = env.Command('junk.out', [], log_action)


@pytest.fixture(scope="module")
def sconscript_task():
    Path('junk.log').unlink(True)
    Path('xtest.log').unlink(True)
    cmd = ['scons', '--site-dir=test_site_scons', '-f', _this_file, '.']
    logger.info("%s", " ".join(cmd))
    task = sp.run(cmd, capture_output=True, universal_newlines=True)
    print(task.stdout)
    return task


def test_filter(sconscript_task):
    task = sconscript_task
    assert _log_line not in task.stdout
    log = Path('xtest.log')
    assert log.exists()
    assert _log_line in log.read_text()


def test_empty_patterns(sconscript_task):
    task = sconscript_task
    log = Path('junk.log')
    assert log.exists
    assert _all_lines in log.read_text()
    assert _all_lines in task.stdout
