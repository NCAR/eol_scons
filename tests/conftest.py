# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import sys
from pathlib import Path
import subprocess as sp


thisdir = Path(__file__).parent
sitepath = thisdir.joinpath('test_site_scons').resolve()
toolpath = sitepath.joinpath('eol_scons/eol_scons/tools').resolve()
# test modules which do not call scons still need to be able to find the
# eol_scons package and the tools, so add them to the path here.  hopefully
# this does not mask any problems in the python path when running scons.
sys.path.append(str(sitepath))
sys.path.append(str(toolpath))


called_from_test = False


def pytest_configure(config):
    global called_from_test
    called_from_test = True


def run_scons(sconsfile):
    cmd = ['scons', f'--site-dir={sitepath}', '-f', sconsfile, '.']
    print("%s", " ".join(cmd))
    # whatever test runs this will fail with an exception if the sconscript
    # fails
    task = sp.run(cmd, capture_output=True, universal_newlines=True)
    print(task.stdout)
    task.check_returncode()
    return task
