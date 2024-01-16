# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# All the python files for the eol_scons package are actually in the eol_scons
# subdirectory.  This module sets the package __path__ to that subdirectory
# and executes the package __init__.py file, so it is loaded into this
# eol_scons package module.
#
# If eol_scons is not imported through this file, then eol_scons/__init__.py
# prints a warning.

from pathlib import Path

pkgpath = Path(__file__).parent.joinpath("eol_scons")
# print("Setting eol_scons package path: %s" % (pkgpath))
__path__ = [str(pkgpath)]

initpath = pkgpath.joinpath("__init__.py")

__eol_scons_init_exec__ = True

# The __init__.py code needs the __file__ variable to be the path to that file
# and not this one.
__file__ = str(initpath)
exec(compile(filename=initpath, source=initpath.read_text(), mode='exec'))
