# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os
import re

_options = None

pylint = "${PYLINTPYTHONPATH and 'env PYTHONPATH='+PYLINTPYTHONPATH or ''} "
pylint += "${PYLINT} ${PYLINTARGS} "
pylint += "${PYLINTRC and '--rcfile='+str(PYLINTRC) or ''} ${SOURCES} 2>&1"
# pylint += '| egrep -v "maximum recursion depth exceeded.*ignored" | '
# pylint += 'egrep -v "Instance of \'Popen\' has no \'.*\' member"'


def find_python_files(env, topdir, excludes=None):
    found = []
    if not excludes:
        excludes = []
    excludes = [env.File(xf).get_abspath() for xf in excludes]
    for root, dirs, files in os.walk(str(env.Dir(topdir))):
        dirs[:] = [d for d in dirs if d not in ['.svn', 'CVS']]
        for f in files:
            if not re.match("[^.].*\.py$", f):
                continue
            fnode = env.File(os.path.join(root, f))
            if fnode.get_abspath() not in excludes:
                found.append(fnode)
    return found


def PythonLint(env, name, sources, **kw):
    target = env.Command(name, sources, pylint, **kw)
    env.Alias(name, target)
    return target


pylintrc = os.path.join(os.path.dirname(__file__), "pylintrc")


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('PYLINT', "Path to pylint program.", "pylint")
    _options.Update(env)
    env.AddMethod(find_python_files, "FindPythonFiles")
    env.AddMethod(PythonLint, "PythonLint")
    env.SetDefault(PYLINT='pylint')
    env.SetDefault(PYLINTRC=pylintrc)
    env.SetDefault(PYLINTARGS='')
    env.SetDefault(PYLINTPYTHONPATH=env.Dir('.').path)


def exists(env):
    return env.Detect('pylint')


if __name__ == "__main__":
    # Given python files on the command line, run the same pylint command
    # on them with the same options as would be used as part of a SCons
    # build.
    import sys
    import os
    pylint = os.environ.get('PYLINT', 'pylint')
    pylint = [pylint, "--rcfile="+pylintrc]
    print(" ".join(pylint))
    os.execvp(pylint[0], pylint+sys.argv[1:])
