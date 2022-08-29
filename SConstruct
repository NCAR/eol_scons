
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

# For now, install the package in the same layout as in the repository, so the
# top-level __init__.py can keep the main package eol_scons/__init__.py from
# thinking it is being imported in the deprecated layout, that is, as
# site_scons/eol_scons/__init__.py.
install = env.Install("$PREFIX/eol_scons", ["__init__.py", "eol_scons"])
install += env.Install("$PREFIX/eol_scons/scripts", ["scripts/build_rpm.sh"])
env.Alias('install', install)

if env.GetOption('clean'):
    env.Execute(Delete(["build", "rpms.txt"]))

env.Test('tests/runtests', 'cd tests && ./runtests')

env.SetHelp()
