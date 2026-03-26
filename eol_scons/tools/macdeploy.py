# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Tool for creating deployable application bundles on macOS, whether a .app for
GUI programs or just a folder with the executable and dependencies for command
line programs.

"""

import os
import glob
import shutil
from SCons.Script import *

from eol_scons.appbundlechecker import AppBundleChecker


def _deployCmdline(target, source, env):
    """
    Parameters:

    target[0]   -- Path to the directory containing the executable and its dependencies.
    source[0]   -- The cmdline executable to be deployed
    """
    source_executable = str(source[0])
    dest_dir = str(target[0])
    dest_executable = os.path.join(dest_dir, os.path.basename(source_executable))

    # create destination directory and copy source executable
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(source_executable, dest_executable)

    # add dependencies.
    checker = AppBundleChecker(dest_executable, app_path_override=True)
    checker.check_executable(dest_executable)
    dylibs = glob.glob(os.path.join(dest_dir, "*dylib"))
    for d in dylibs:
        checker.check_executable(d)


def DeployCmdline(env, target, source):
    deployCmdline = env.RunDeployCmdline(target, source)
    env.AlwaysBuild(deployCmdline)
    env.Clean(deployCmdline, deployCmdline)
    return deployCmdline


def generate(env):
    """Add Builders and construction variables to the Environment."""

    bldr = Builder(action=_deployCmdline)
    env.Append(BUILDERS={'RunDeployCmdline': bldr})

    env.AddMethod(DeployCmdline, "DeployCmdline")


def exists(env):
    return True
