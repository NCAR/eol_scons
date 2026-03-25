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
            [os.path.expanduser('~/Applications/InstallBuilder/bin/Builder.app/Contents/MacOS/'),
                '/Applications/BitRock/bin/Builder.app/Contents/MacOS/'])
        return node

    return None

#
# Builder to generate windows dependencies and create an installer.
#

def _get_dependencies(exe_path):
    """ Return list of dependencies for executable """
    result = subprocess.run(['ldd', exe_path], capture_output=True, text=True)
    return result.stdout.splitlines()

def _parse_dependency_location(line):
    """ Return path to dependency file from line in ldd output """
    # format: libunistring-5.dll => /ucrt64/bin/libunistring-5.dll (0x7ffd71ba0000)
    fields = line.split(" ")
    return fields[2] if len(fields) >= 3 else None

def _create_xml_entry(line):
    depfile = _parse_dependency_location(line)
    if not depfile or depfile.startswith("/c/Windows"):
        # assume dependencies in here are normal windows OS files
        return ""
    # msys paths start at /ucrt64 but windows paths (that installbuilder uses) are really c:/msys64/ucrt64
    return f"""<distributionFile>
    <origin>/msys64{depfile}</origin>
</distributionFile>
"""

def _add_openssl_deps(openssldir):
    openssl_dlls = []
    openssl_distribution_files = ""
    for pattern in ['libssl-*.dll', 'libcrypto-*.dll']:
        openssl_dlls += glob.glob(os.path.join(openssldir, pattern))
    for dll in openssl_dlls:
        openssl_dir_xml = openssldir.rstrip('/')
        # Strip windows drive letter if present (C:/msys64/ucrt64/bin -> /msys64/ucrt64/bin)
        if len(openssl_dir_xml) > 1 and openssl_dir_xml[1] == ':':
            openssl_dir_xml = openssl_dir_xml[2:]
        depfile = openssl_dir_xml + '/' + os.path.basename(dll)
        # Prepend /msys64 if path is a MSYS2 ucrt64-relative path (eg /ucrt64/...)
        if not depfile.startswith('/msys64'):
            depfile = '/msys64' + depfile
        if not depfile in openssl_distribution_files:
            openssl_distribution_files += f"""<distributionFile>
    <origin>{depfile}</origin>
</distributionFile>"""
    return openssl_distribution_files

def _create_xml(distribution_files, output_path):
    comment = "<!-- add windows dependencies here -->"
    if comment in xml_template:
        contents = xml_template.replace(comment, distribution_files)
        with open(output_path, "w") as f:
            f.write(contents)
    else:
        print("No comment placeholder in template to insert dependencies in.")


def _create_windows_dependencies_xml(env, sources, dest, openssldir):
    if env['PLATFORM'] == 'darwin':
        # just save the empty template as a placeholder file, since mac doesn't use dependencies here
        with open(dest, 'w') as f:
            f.write(xml_template)
    else:
        deps = []
        for s in sources:
            deps += _get_dependencies(s)
        deps = list(set(deps)) #remove duplicates
        distribution_files = ""
        for d in deps:
            distribution_files += _create_xml_entry(d)
        if openssldir:
            distribution_files += _add_openssl_deps(openssldir)
        _create_xml(distribution_files, dest)

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
    openssldir = env['OPENSSLDIR']
    xml = str(sources[0])
    windeps = os.path.join(os.path.dirname(xml), "WindowsDependencies.xml")
    
    # create windows dependencies xml file
    _create_windows_dependencies_xml(env, sources[1:], windeps, openssldir)

    # Run InstallBuilder.
    subprocess.check_call([builder, 'build', xml, '--setvars', 'svnversion='+version, 'osversion='+osid,],
                          stderr=subprocess.STDOUT, bufsize=1)


def InstallBuilder(env, destfile, builderxml, source, version, osid='win', openssldir=None, *args, **kw):
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

    The git version and os id values are passed to InstallBuilder as variables. The openssldir value is used in creating the dependencies file.

        Parameters:
        destfile   -- The target generated installer file. This should be 
                      the same as the output file specified in the xml file.
        builderxml -- The InstallBuilder xml configuration
        sources    -- Other dependencies that should trigger a rebuild.
        version    -- The version number that will be fed to InstallBuilder.
        osid       -- The operating system identifier that will be fed to InstallBuilder
        openssldir -- The directory to find openssl dependencies in

    """
    sources = source
    if type(sources) != type(list()):
        sources = [source]

    # Create the installer dependencies and actions.
    installer = env.RunInstallBuilder(
        destfile, [builderxml] + sources, SVNVERSION=version, OSID=osid, OPENSSLDIR=openssldir)
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
