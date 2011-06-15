
import os
import re

pylint = "${PYLINTPYTHONPATH and 'env PYTHONPATH='+PYLINTPYTHONPATH or ''} "
pylint += "${PYLINT} "
pylint += "${PYLINTRC and '--rcfile='+str(PYLINTRC) or ''} ${SOURCES} 2>&1 | "
pylint += 'egrep -v "maximum recursion depth exceeded.*ignored"'


def find_python_files(env, topdir):
    found = []
    for root, dirs, files in os.walk(str(env.Dir(topdir))):
        dirs[:] = [ d for d in dirs if d not in ['.svn', 'CVS'] ]
        found.extend([ env.File(os.path.join(root, f))
                       for f in files if re.match("[^.].*\.py$", f) ])
    return found


def PythonLint(env, name, sources):
    target = env.Command(name, sources, pylint)
    env.Alias(name, target)
    return target


def generate(env):
    env.AddMethod(find_python_files, "FindPythonFiles")
    env.AddMethod(PythonLint, "PythonLint")
    env.SetDefault(PYLINT='pylint')
    pylintrc = os.path.join(os.path.dirname(__file__), "pylintrc")
    env.SetDefault(PYLINTRC=pylintrc)
    env.SetDefault(PYLINTPYTHONPATH=env.Dir('.').path)
                   

def exists(env):
    return env.Detect('pylint')

