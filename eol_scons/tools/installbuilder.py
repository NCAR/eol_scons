# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
SCons.Tool.osxqtapp

Create an InstallBuilder installer from an application and an InstallBuilder
xml configuration. Currently only runs on Windows and OSX.

See InstallBuilder() for the parameter descriptions.

Example usage (OSX):
    installerdir = Dir('RIC-' + svnrevision + '.app')
    sources = Dir('#/installers/mac/RICProxy-' + svnrevision + '.app')
    installer = env.InstallBuilder(installerdir, builderxml, [sources],
                                   svnrevision)

"""

import os
import glob
import subprocess as sp

from SCons.Script import Touch, Mkdir

import eol_scons.installmode as im


xml_template = """<folder>
<description>Program Files</description>
<destination>${{installdir}}</destination>
<name>programfileswindowsdeps</name>
<platforms>windows-x64</platforms>
<distributionFileList>
{dependencies}
</distributionFileList>
</folder>"""

_distfile_format = """<distributionFile>
    <origin>{distfile}</origin>
</distributionFile>
"""

_distdir_format = """<distributionDirectory>
    <origin>{distdir}</origin>
</distributionDirectory>
"""


def _windows_path(path):
    if im.MockMode():
        return f"_windows_path({path})"
    return sp.check_output(['cygpath', '-w', '-a', path], text=True).strip()


def _find_installbuilder(env):
    """
    Look for the InstallBuilder command line application.

    Returns the path to the executable, if found. Otherwise
    returns None.
    """
    # There is no harm in checking for Windows-specific commands on all
    # platforms.  Either they are found or not.
    paths = glob.glob('/c/Tools/InstallBuilder/bin/builder-cli.exe')
    paths += glob.glob('/c/Program Files/InstallBuilder*/bin/builder-cli.exe')
    paths += glob.glob('C:/Program Files/InstallBuilder*/bin/builder-cli.exe')

    for path in paths:
        if os.path.isfile(path):
            return path

    # Likewise for MacOS-specific commands.
    node = env.FindFile(
        'installbuilder.sh',
        [os.path.expanduser(
            '~/Applications/InstallBuilder/bin/Builder.app/Contents/MacOS/'),
         '/Applications/BitRock/bin/Builder.app/Contents/MacOS/'])

    return node


def _parse_dependency_location(line):
    """ Return path to dependency file from line in ldd output """
    # format: libunistring-5.dll => /ucrt64/bin/libunistring-5.dll (0x7ffd71ba0000)
    fields = line.split(" ")
    return fields[2] if len(fields) >= 3 else None


def _get_dependencies(exe_path: str) -> list[str]:
    """ Return list of dependencies for executable """
    result = sp.run(['ldd', exe_path], capture_output=True, text=True)
    deps = []
    for line in result.stdout.splitlines():
        dep = _parse_dependency_location(line)
        if dep:
            deps.append(dep)
    return deps


def _add_openssl_deps(openssldir) -> list[str]:
    openssl_dlls = []
    for pattern in ['libssl-*.dll', 'libcrypto-*.dll']:
        openssl_dlls += glob.glob(os.path.join(openssldir, pattern))
    deps = []
    for dll in openssl_dlls:
        depfile = os.path.join(openssldir, os.path.basename(dll))
        deps.append(depfile)
    return deps


def _create_xml(deps: list[str], output_path):
    im.MockEcho(f"_create_xml('...', {output_path})")
    deps = list(set(deps))  # remove duplicates
    dependencies = ""
    # the Qt6 platforms directory needs to be included as a distribution
    # directory, so convert msys-relative fixed path to Windows absolute path
    distdir = _windows_path("/ucrt64/share/qt6/plugins/platforms")
    dependencies += _distdir_format.format(distdir=distdir)
    # convert all dependency files to canonical Windows-style absolute paths
    deps = [_windows_path(dep) for dep in deps]
    # ignore dependencies that look like normal Windows OS files
    deps = [dep for dep in deps if not dep.startswith(r"C:\Windows")]
    for dep in deps:
        dependencies += _distfile_format.format(distfile=dep)

    # finally, render the template XML with the dependencies
    xml = xml_template.format(dependencies=dependencies)
    with open(output_path, "w") as f:
        f.write(xml)


def _create_windows_dependencies_xml(env, sources, dest, openssldir):
    "Collect Windows DLL dependencies and write them to XML."
    dest = str(dest)
    im.MockEcho("_create_windows_dependencies_xml("
                f"{[str(s) for s in sources]}, {dest}, {openssldir})")
    if env['PLATFORM'] == 'darwin':
        # just save the empty template as a placeholder file, since mac
        # doesn't use dependencies here
        with open(dest, 'w') as f:
            f.write(xml_template)
        return
    deps = []
    for s in sources:
        deps += _get_dependencies(str(s))
    if openssldir:
        deps += _add_openssl_deps(openssldir)
    _create_xml(deps, dest)


def _installbuilder(target, source, env):
    """
    Parameters:

    target[0]   -- The generated installer path name. We don't use it.
    source[0]   -- The installbuilder xml definition.
    source[1:]  -- Other source dependencies.

    Environment values:
    env['SVNVERSION'] -- The version number to be passed to installbuilder.
    """
    builder = str(env['INSTALLBUILDER'])
    version = env['REPO_REVISION']
    version = version.replace(':', '-')
    osid = env['OSID']
    openssldir = env['OPENSSLDIR']
    xml = str(source[0])
    windeps = env.get('WINDOWS_DEPENDENCIES_XML')

    # create windows dependencies xml file
    _create_windows_dependencies_xml(env, source[1:], windeps, openssldir)

    # Run InstallBuilder.
    cmd = [builder, 'build', xml, '--setvars', f'svnversion={version}',
           f'osversion={osid}']
    env.PrintProgress(" ".join(cmd))
    sp.check_call(im.Command(cmd), stderr=sp.STDOUT, bufsize=1)
    if im.MockMode():
        # On MacOS, installbuilder creates a .app bundle directory for the
        # installer, while on Windows it creates a .exe file.
        if str(target[0]).endswith('.app'):
            env.Execute(Mkdir(target[0]))
        else:
            env.Execute(Touch(target[0]))


def InstallBuilder(env, destfile, builderxml, sources, version, osid='win',
                   openssldir=None, *args, **kw):
    """
    A psuedo-builder for creating InstallBuilder installers.

    The recipe for creating the installer is provided in the InstallBuilder
    xml specification file. In general this file is edited using the
    InstallBuilder GUI application, although some modification is possible
    with a text editor. But if you break it, you get to keep the pieces.

    The InstallBuilder xml configuration has an explicitly named output file,
    and many source files. We will always run InstallBuilder, since it would
    be hard to account for all of these dependencies. Perhaps in the future we
    can come up with a scheme to allow this routine to specify the output file
    path for InstallBuilder; this will involve modifying the InstallBuilder
    xml file.

    The git version and os id values are passed to InstallBuilder as
    variables. The openssldir value is used in creating the dependencies file.

        Parameters:
        destfile   -- The target generated installer file. This should be
                      the same as the output file specified in the xml file.
        builderxml -- The InstallBuilder xml configuration
        sources    -- Other dependencies that should trigger a rebuild.
        version    -- The version number that will be fed to InstallBuilder.
        osid       -- The OS identifier that will be fed to InstallBuilder
        openssldir -- The directory to find openssl dependencies in

    """
    if not isinstance(sources, list):
        sources = [sources]

    # create the path here and pass it to the installbuilder in the env, so it
    # can be added as a clean target.  the alternative is to add it as a
    # target of the builder, but there may be places which expect the only
    # target returned by this pseudo-builder to be the installer file.
    builderxml = env.File(builderxml)
    windeps = builderxml.File("WindowsDependencies.xml")

    # Create the installer builder.
    installer = env.Command(destfile, [builderxml] + sources,
                            action=_installbuilder,
                            REPO_REVISION=version, OSID=osid,
                            OPENSSLDIR=openssldir,
                            WINDOWS_DEPENDENCIES_XML=windeps)
    env.AlwaysBuild(installer)
    env.Clean(installer, windeps)
    return installer


def generate(env):
    """Add Builders and construction variables to the Environment."""

    # find the InstallBuilder command
    builder = _find_installbuilder(env)
    if builder is None and im.AllMode():
        builder = 'builder-cli.exe'

    # This will be None if the installbuilder command is not available.
    # Callers can use this to create alternative installer builders.
    env['INSTALLBUILDER'] = builder

    # Define that all important method.
    env.AddMethod(InstallBuilder, "InstallBuilder")


def exists(env):
    return True
