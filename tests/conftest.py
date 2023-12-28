import sys
from pathlib import Path

toolpath = Path(__file__).parent.joinpath('../eol_scons/tools').resolve()
sys.path.append(str(toolpath))


called_from_test = False


def pytest_configure(config):
    global called_from_test
    called_from_test = True
