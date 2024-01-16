# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Add this tool to the project GLOBAL_TOOLS to run scons builds under the
Clang Static Analyzer.  If this tool detects that scan-build is running
scons, it passes the appropriate compiler settings and environment
variables into the SCons construction and process environments.

In the SConstruct file, create an Environment like this:

    env = Environment(tools=['default', 'gitinfo'], GLOBAL_TOOLS=['scanbuild'])

Then run the build like below to generate the analysis report:

    scan-build -v -o csa-reports -analyze-headers --status-bugs scons

For a really deep dive, you can enable lots of optional checkers:

    scan-build -v -o csa-reports -analyze-headers --status-bugs \
      -enable-checker alpha.clone.CloneChecker \
      -enable-checker alpha.unix.PthreadLock \
      -enable-checker alpha.unix.Stream 
      -enable-checker optin.cplusplus.VirtualCall scons

To make sure scons tries to build everything, and therefore runs the
checkers on everything, first clean everything beneath the top directory:

    scons -c .
"""


import os

def generate(env):
    # Propagate CXX and CC from the process environment, in case running
    # under scan-build.  The set of environment variables which scan-build
    # needs passed down was found by running 'scan-build env'.  If this
    # only passed the overridden CXX and CC, then the clang analyzer
    # programs create lots of separate reports instead of one report.
    if os.environ.get('CLANG'):
        env.PassEnv(r'CLANG.*')
        env.PassEnv(r'CCC_.*')
        env.PassEnv(r'CC')
        env.PassEnv(r'CXX')
        # CC and CXX also have to be set explicitly in the SCons
        # Environment so SCons will run the right compile command.
        if os.environ.get('CXX'):
            env['CXX'] = os.environ.get('CXX')
        if os.environ.get('CC'):
            env['CC'] = os.environ.get('CC')

def exists(env):
    return True


