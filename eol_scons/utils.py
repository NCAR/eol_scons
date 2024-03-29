# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
import re
import subprocess


def get_cxxversion(env):
    try:
        # do g++ --version, grab 3rd field for CXXVERSION
        revline = subprocess.Popen([env['CXX'], '--version'],
                                   env={'PATH': env['ENV']['PATH']},
                                   universal_newlines=True,
                                   stdout=subprocess.PIPE).stdout.readline()
        rev = re.split(r'\s+', revline)[2]
        return rev
    except OSError as xxx_todo_changeme:
        (errno, strerror) = xxx_todo_changeme.args
        print("Error: %s: %s" % (env['CXX'], strerror))
        return None


if __name__ == "__main__":
    import eol_scons
    from SCons.Script import Environment
    env = Environment(tools=['default'])
    print("CXX version: %s" % (get_cxxversion(env)))
