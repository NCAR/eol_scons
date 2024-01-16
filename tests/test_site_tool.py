# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import sys
import conftest


if not conftest.called_from_test:

    from SCons.Script import Environment

    # If using the eol_scons.py tool module installed into a site_tools
    # directory, then no import is needed to apply eol_scons just like a tool.

    env = Environment(tools=['default', 'eol_scons_tool', 'prefixoptions',
                             'netcdf'])
    variables = env.GlobalVariables()

    # And not applying the eol_scons tool means no eol_scons extensions.
    try:
        env = Environment(tools=['default', 'prefixoptions', 'netcdf'])
        variables = env.GlobalVariables()
    except AttributeError:
        print("Exception raised as expected.")
        sys.exit(0)

    raise Exception("Expected error since eol_scons_tool not loaded.")


def test_eol_scons_tool():
    conftest.run_scons(__file__)
