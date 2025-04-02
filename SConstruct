
import sys
from pathlib import Path

sys.path.append(str(Path('.').absolute().joinpath('eol_scons')))

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
docsources = ['doxy/Doxyfile', 'doxy/mainpage.dox', 'eol_scons/README',
              'doxy/eol_scons']
docs = env.Command(env.Dir('doxy/html'), docsources, 'cd doxy && doxygen')
env.AlwaysBuild(docs)
env.Alias('docs', docs)

# to get the right package paths in doxygen and subvert the top-level
# __init__.py (ie eol_scons.gitinfo and not eol_scons.eol_scons.gitinfo),
# install a copy of the eol_scons package under the doxy directory for doxygen
# to scan.  This must be always built when needed for the doxygen target,
# since scons does not compare all the individual files in the install.
env.AlwaysBuild(env.Install("#/doxy", ["eol_scons"]))

# For now, install the package in the same layout as in the repository, so the
# top-level __init__.py can keep the main package eol_scons/__init__.py from
# thinking it is being imported in the deprecated layout, that is, as
# site_scons/eol_scons/__init__.py.
install = env.Install("$PREFIX/eol_scons", ["__init__.py"])
for subdir in ['site_tools', 'eol_scons', 'eol_scons/tools',
               'eol_scons/hooks', 'eol_scons/postgres']:
    files = env.Glob(f"{subdir}/*.py")
    files += env.Glob(f"{subdir}/pylintrc")
    install += env.Install(f"$PREFIX/eol_scons/{subdir}", files)
install += env.Install("$PREFIX/eol_scons/scripts", ["scripts/build_rpm.sh"])
env.Alias('install', install)

if env.GetOption('clean'):
    env.Execute(Delete(["build", "rpms.txt", "tests/.sconf_temp",
                        "tests/config.log", "tests/.sconsign.dblite",
                        "tests/test_site_scons", "doxy/html"]))

# for the test script, look for scons and pytest executables in the same place
# as the python executable running this SConstruct.
testenv = env.Clone()
testenv.PrependENVPath('PATH', str(Path(sys.executable).parent.resolve()))
testenv.Test('tests/runtests', 'cd tests && ./runtests')

env.SetHelp()
