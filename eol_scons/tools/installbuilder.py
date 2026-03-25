# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
SCons.Tool.osxqtapp

Create an InstallBuilder installer from an application and an InstallBuilder xml configuration. Currently
only runs on Windows and OSX.

See InstallBuilder() for the parameter descriptions.

Example usage (OSX):
    installerdir = Dir('RIC-' + svnrevision + '.app')
    sources = Dir('#/installers/mac/RICProxy-' + svnrevision + '.app')
    installer = env.InstallBuilder(installerdir, builderxml, [sources], svnrevision)

"""

import glob, os
import subprocess
from SCons.Script import *


xml_template = """<folder>
<description>Program Files</description>
<destination>${installdir}</destination>
<name>programfileswindowsdeps</name>
<platforms>windows-x64</platforms>
<distributionFileList>
<distributionDirectory>
    <origin>C:/msys64/ucrt64/share/qt6/plugins/platforms</origin>
</distributionDirectory>
<!-- add windows dependencies here -->
</distributionFileList>
</folder>"""


def _find_installbuilder(env):
    """ 
    Look for the InstallBuilder command line application.

    Returns the path to the executable, if found. Otherwise
    returns None.
    """
    try:
        return env['INSTALLBUILDER']
    except KeyError:
        pass

    if env['PLATFORM'] in  ['msys', 'win32', 'cygwin']:
        for path in glob.glob('/c/Tools/InstallBuilder/bin/builder-cli.exe') + \
                    glob.glob('/c/Program Files/InstallBuilder*/bin/builder-cli.exe') + \
                    glob.glob('C:/Program Files/InstallBuilder*/bin/builder-cli.exe'):
            if os.path.isfile(path):
                return path
        return None

    if env['PLATFORM'] == 'darwin':
        node = env.FindFile(
            'installbuilder.sh',
            ['/Applications/BitRock/bin/Builder.app/Contents/MacOS/'])
        return node

    return None

#
# Builder to generate windows dependencies and create an installer.
#

def _create_windows_dependencies_xml(env, sources):
    if env['PLATFORM'] == 'darwin':
        # just save the empty template as a placeholder file, since mac doesn't use dependencies here
        with open('Installers/InstallBuilder/WindowsDependencies.xml', 'w') as f:
            f.write(xml_template)
    else:
        # generate the windows dependencies xml file by running the get_windows_dependency_list script
        subprocess.check_call(['python', os.path.join(env['EOL_SCONS_SCRIPTS_DIR'], 'get_windows_dependency_list.py'),
                               '--exe1', sources[0], '--exe2', sources[2], # positions hardcoded for now, will rework
                               '--template', os.path.join(env['EOL_SCONS_SCRIPTS_DIR'], 'WindowsDependenciesTemplate.xml'),
                               '--output', 'Installers/InstallBuilder/WindowsDependencies.xml'])

def _installbuilder(target, source, env):
    """
    Parameters:

    target[0]   -- The generated installer path name. We don't use it.
    source[0]   -- The installbuilder xml definition.
    source[1:]  -- Other source dependencies.

    Environment values:
    env['SVNVERSION'] -- The version number to be passed to installbuilder.
    """

    sources = source
    if type(sources) != type(list()):
        sources = [source]

    builder = str(env['INSTALLBUILDER'])
    version = env['REPO_REVISION']
    version = version.replace(':', '-')
    osid  = env['OSID']
    xml = str(sources[0])
    
    # create windows dependencies xml file
    _create_windows_dependencies_xml(env, sources[1:])

    # Run InstallBuilder.
    subprocess.check_call([builder, 'build', xml, '--setvars', 'svnversion='+version, 'osversion='+osid,],
                          stderr=subprocess.STDOUT, bufsize=1)


def InstallBuilder(env, destfile, builderxml, source, version, osid='win',*args, **kw):
    """
    A psuedo-builder for creating InstallBuilder installers. 

    The recipe for creating the installer is provided in the InstallBuilder xml 
    specification file. In general this file is edited using the InstallBuilder GUI 
    application, although some modification is possible with a text editor. But
    if you break it, you get to keep the pieces.

    The InstallBuilder xml configuration has an explicitly named output file,
    and many source files. We will always run InstallBuilder, since it would be hard to
    account for all of these dependencies. Perhaps in the future we can
    come up with a scheme to allow this routine to specify the output 
    file path for InstallBuilder; this will involve modifying the InstallBuilder xml
    file. 

    The git version and os id values are passed to InstallBuilder as variables.

        Parameters:
        destfile   -- The target generated installer file. This should be 
                      the same as the output file specified in the xml file.
        builderxml -- The InstallBuilder xml configuration
        sources    -- Other dependencies that should trigger a rebuild.
        version    -- The version number that will be fed to InstallBuilder.
        osid       -- The operating system identifier that will be fed to InstallBuilder

    """
    sources = source
    if type(sources) != type(list()):
        sources = [source]

    # Create the installer dependencies and actions.
    installer = env.RunInstallBuilder(
        destfile,  [builderxml] + sources, SVNVERSION=version, OSID=osid)
    env.AlwaysBuild(installer)
    env.Clean(installer, installer)

    return installer


def generate(env):
    """Add Builders and construction variables to the Environment."""

    # Define the InstallBuilder builder.
    bldr = Builder(action=_installbuilder)
    env.Append(BUILDERS={'RunInstallBuilder': bldr})

    # find the InstallBuilder command
    env['INSTALLBUILDER'] = _find_installbuilder(env)

    # Define that all important method.
    env.AddMethod(InstallBuilder, "InstallBuilder")


def exists(env):
    return True
