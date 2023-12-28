
import sys
from pathlib import Path

sys.path.append(Path('.').absolute().joinpath('eol_scons'))

import eol_scons

eol_scons.RunScripts()

from SCons.Script import PathVariable, Environment, Delete

env = Environment(tools=['default'])

variables = eol_scons.GlobalVariables()
variables.AddVariables(PathVariable('PREFIX', 'installation path',
                                    '/usr/share/scons/site_scons',
                                    PathVariable.PathAccept))
variables.Update(env)

# Someday this would be a good place to set the PROJECT_NUMBER in the Doxyfile
# to the current version...
docsources = ['doxy/Doxyfile', 'doxy/mainpage.dox', 'eol_scons/README']
docs = env.Command(env.Dir('doxy/html'), docsources, 'cd doxy && doxygen')
env.AlwaysBuild(docs)
env.Alias('docs', docs)

# For now, install the package in the same layout as in the repository, so the
# top-level __init__.py can keep the main package eol_scons/__init__.py from
# thinking it is being imported in the deprecated layout, that is, as
# site_scons/eol_scons/__init__.py.
install = env.Install("$PREFIX/eol_scons", ["__init__.py", "eol_scons",
                                            "site_tools"])
install += env.Install("$PREFIX/eol_scons/scripts", ["scripts/build_rpm.sh"])
env.Alias('install', install)

if env.GetOption('clean'):
    env.Execute(Delete(["build", "rpms.txt", "tests/.sconf_temp",
                        "tests/config.log", "tests/.sconsign.dblite",
                        "tests/test_site_scons", "doxy/html"]))

env.Test('tests/runtests', 'cd tests && ./runtests')

env.SetHelp()
