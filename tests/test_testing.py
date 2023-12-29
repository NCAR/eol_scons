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
    log_action = env.LogAction([f"@echo {_all_lines}"], 'junk.log', [r'.*'])
    target = env.Command('junk.out', [], log_action)

    # make sure output can be filtered without a log file.
    nolog = env.LogAction(["@echo This line good.",
                           "@echo This line bad."],
                          None, [r'.*good.*'])
    target = env.Command('junk2.out', [], nolog)

    # and that multiple actions can log to the same file, and empty pattern
    # lists suppress all lines.
    logx = env.LogAction(["@echo logx line 1.",
                          "@echo logx line 2."],
                         "logx.log", [])
    target = env.Command('logx.out', [], logx)


@pytest.fixture(scope="module")
def sconscript_task():
    Path('junk.log').unlink(True)
    Path('junk2.log').unlink(True)
    Path('xtest.log').unlink(True)
    return conftest.run_scons(_this_file)


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


def test_no_log(sconscript_task):
    task = sconscript_task
    assert 'This line good.' in task.stdout
    assert 'This line bad.' not in task.stdout


def test_multi_log(sconscript_task):
    task = sconscript_task
    log = Path('logx.log')
    assert log.exists
    assert 'logx line 1' not in task.stdout
    assert 'logx line 2' not in task.stdout
    text = log.read_text()
    assert 'logx line 1' in text
    assert 'logx line 2' in text
