import sys
from pathlib import Path
import subprocess as sp


thisdir = Path(__file__).parent
sitepath = thisdir.joinpath('..').resolve()
toolpath = sitepath.joinpath('eol_scons/tools').resolve()
sys.path.append(str(toolpath))


called_from_test = False


def pytest_configure(config):
    global called_from_test
    called_from_test = True


def run_scons(sconsfile, sitedir=None):
    if sitedir is None:
        sitedir = sitepath
    sitedir = "test_site_scons"
    cmd = ['scons', f'--site-dir={sitedir}', '-f', sconsfile, '.']
    print("%s", " ".join(cmd))
    # whatever test runs this will fail with an exception if the sconscript
    # fails
    task = sp.run(cmd, capture_output=True, universal_newlines=True)
    print(task.stdout)
    task.check_returncode()
    return task
