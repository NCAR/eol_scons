# -*- python -*-

import sys
import conftest


if not conftest.called_from_test:

    import eol_scons
    eol_scons.RemoveDefaultHook()

    from SCons.Script import Environment

    try:
        env = Environment(tools=['default', 'prefixoptions', 'netcdf'])
        variables = env.GlobalVariables()
    except AttributeError:
        print("Exception raised as expected.")
        sys.exit(0)

    raise Exception("eol_scons default hook should not have worked")


def test_eol_scons_tool():
    conftest.run_scons(__file__)
