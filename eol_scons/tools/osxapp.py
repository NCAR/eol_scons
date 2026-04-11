# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
SCons.Tool.osxqtapp

Create an OSX application bundle from a qt executable.

See OsxQtApp() for the parameter descriptions.

Example:
  switchappname = 'RICSwitch-' + apprevision
  switchappdir = Dir(switchappname+'.app')
  switchapp = env.OsxQtApp(switchappdir,
                           '#/switch/ric_switch',
                           '#/Resources/proxy/proxyIcon.icns',
                           switchappname,
                           apprevision)

Process:
 - Remove the existing bundle, if present.
 - Populate the bundle directory tree with the executable and icon files.
 - create Info.plist and copy to Contents/
 - run macdeployqt on the bundle, which copies in needed frameworks
   and libraries.

Info.plist is an XML description of the application.

The bundle hierarchy is as follows:
apname.app/
   Contents/
      Frameworks/
         frameworks and libraries
      MacOS/
         executable
      Resources/
         icon file
      Info.plist
"""

import glob
import os
import shutil
import sys
import SCons
from SCons.Script import Execute, Dir, Delete, Copy, Mkdir
from SCons.Script import Builder

from eol_scons.appbundlechecker import AppBundleChecker

class ToolOsxQtAppWarning(SCons.Warnings.WarningOnByDefault):
    pass


class MacdeployqtNotFound(ToolOsxQtAppWarning):
    pass


class NotAnOsxSystem(ToolOsxQtAppWarning):
    pass


def _make_info_plist(bundle_name, bundle_identifier, bundle_signature,
                     bundle_version, icon_filename):
    """
    Return a customized Info.plist. This is a manifest that is found in
    Contents/ in the bundle.

    Parameters: Should be self evident
    """

    bundleName = bundle_name
    bundleDisplayName = bundle_name
    bundleIdentifier = bundle_identifier
    bundleVersion = bundle_version
    bundleSignature = bundle_signature
    bundleIconFile = icon_filename

    info = r"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
                       "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>%s</string>
    <key>CFBundleDisplayName</key>
    <string>%s</string>
    <key>CFBundleIdentifier</key>
    <string>%s</string>
    <key>CFBundleVersion</key>
    <string>%s</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>%s</string>
    <key>CFBundleExecutable</key>
    <string>%s</string>
    <key>CFBundleIconFile</key>
    <string>%s</string>
</dict>
</plist>
""" % (
        bundleName,
        bundleDisplayName,
        bundleIdentifier,
        bundleVersion,
        bundleSignature,
        bundleIdentifier,
        bundleIconFile
    )

    return info

def _find_mdqt(env):
    """
    Look for macdeployqt.

    Returns the path to the executable, if found. Otherwise
    raises an error exception.
    """
    try:
        return env['MACDEPLOYQT']
    except KeyError:
        pass

    macdeployqt = env.WhereIs('macdeployqt')
    if macdeployqt:
        return macdeployqt

    raise SCons.Errors.StopError(
        MacdeployqtNotFound,
        "Could not find macdeployqt")
    return None


#
# Builder to run macdeployqt on a bundle
#
def _macdeployqt(target, source, env):
    """
    Run macdepoyqt on the bundle.

    Parameters:
    target[0] -- bogus

    source[0] -- The bundle directory, e.g. RICProxy-6454.app.
    """
    bundle = str(source[0])
    tmpbundle = str(os.path.basename(bundle))

    # Run macdeployqt.
    # macdeployqt will give volume name of bundle, so cd to directory just
    # above.
    Execute(env.ChdirActions([env['MACDEPLOYQT'] + " " + tmpbundle], os.path.dirname(bundle)))


#
# Builder to create a bundle.
#
def _create_bundle(bundle, appname, version, exename, iconname, plist=None):
    """
    Create and populate an OSX application bundle.
    """
    bundledir = bundle.get_abspath()
    contentsdir = Dir(bundledir + '/Contents')
    macosdir = Dir(bundledir + '/Contents/MacOS')
    resourcesdir = Dir(bundledir + '/Contents/Resources')

    # Get rid of the existing bundle. Otherwise macdeployqt gets bent out of
    # shape when it finds its products already there.
    Execute(Delete(bundle))

    # Buid the basic bundle structure
    Execute(Mkdir(bundledir))
    Execute(Mkdir(contentsdir))
    Execute(Mkdir(macosdir))
    Execute(Mkdir(resourcesdir))

    # Copy the executable and icon
    Execute(Copy(macosdir, exename))
    Execute(Copy(resourcesdir, iconname))
    if plist:
        # name needs to be exactly 'Info.plist'
        Execute(Copy(os.path.join(contentsdir.path, 'Info.plist'), plist))
    else:
        info = _make_info_plist(
            bundle_name=appname,
            bundle_identifier=exename,
            bundle_signature='ncar-eol-cds-qt-app',
            bundle_version=version,
            icon_filename=iconname)
        infofilepath = contentsdir.get_abspath() + '/Info.plist'
        infoplistfile = open(infofilepath, "w")
        infoplistfile.write(info)


def _fix_app_bundle_paths(app, env):
    checker = AppBundleChecker(app, brew_prefix=env['MACOS_PREFIX'])
    checker.check()


def _createOsxQtApp(target, source, env):
    """
    Create an OSX application bundle for a Qt application.

    Parameters:
    target[0] -- The bundle directory, e.g. RICProxy-6454.app.

    source[0] -- The application executable to be bundled, e.g. ric_proxy.
    source[1] -- The application icon file, e.g. '#/Resources/proxy/proxyIcon.icns'
    source[2] -- (optional) The Info.plist file to be used in the bundle. If not provided, a default one will be created with the appropriate fields filled in.

    env['EXENAME']    -- e.g. ric_proxy
    env['VERSION']   -- e.g. 6454
    env['ICON']      -- e.g. '#/Resources/proxy/proxyIcon.icns'
    env['PLIST']     -- (optional) The path to the Info.plist file to be used in the bundle.
    """
    bundle = target[0]
    exename = source[0].path
    iconname = source[1].path
    plist = None
    if len(source) > 2:
        plist = source[2].path
    version = env['VERSION']
    appname = env['APPNAME']
    # create the bundle structure and copy in exe, icon, and plist
    _create_bundle(bundle, appname, version, exename, iconname, plist=plist)
    # run macdeployqt
    _macdeployqt(bundle, [bundle.path], env)
    # finish what macdeployqt started
    _fix_app_bundle_paths(bundle.path, env)
    # codesign if cert is present
    if os.environ.get('DEVELOPER_CERT'):
        Execute(['codesign -s "' + os.environ.get('DEVELOPER_CERT') + '" -v -f --deep ' + bundle.path])


def OsxQtApp(env, destdir, appexe, appicon, appname, appversion, plist=None, *args, **kw):
    """
    A pseudo-builder to create an OSX application bundle for a Qt application.

    An OSX application bundle hierarchy is created, and the executable and
    other artifacts are copied in. The macdeployqt application is run on
    the bundle in order to bring in supporting frameworks and libraries.

    A script (launch_app) is created which sets environment values such as
    DYLD_LIBRARY_PATH and DYLD_FRAMEWORK_PATH to the locations within
    the bundle, and then runs the application. This script is designated as
    the application executable in the Info.plist file.

    The final bundle name will be appname + '.app'.

    Parameters:
    destdir    -- Directory where bundle will be created. Must end with '.app'
    appexe     -- The path to the application executable.
    appicon    -- The path to the application icon.
    appname    -- The final name of the app, without '.app'. E.g. 'Proxy-6457'
    appversion -- The version number to be included in Info.plist
    plist     -- (optional) The path to the Info.plist file to be used in the bundle.
    """


    # Establish some useful attributes.
    bundledir = Dir(str(destdir))

    sources = [appexe, appicon]
    if plist:
        sources.append(plist)
    bundle = env.CreateOsxQtApp(bundledir, sources, VERSION=appversion, APPNAME=appname)
    env.AlwaysBuild(bundle)
    return bundle


def _createOsxCmdlineApp(target, source, env):
    """
    Parameters:

    target[0]   -- Path to the versioned destination directory.
    source[0]   -- The cmdline executable to be deployed
    """
    source_executable = str(source[0])
    dest_dir = str(target[0])
    dest_executable = os.path.join(dest_dir, os.path.basename(source_executable))
    # create destination directory and copy source executable
    if os.path.exists(dest_dir):
        print("removing existing directory: ", dest_dir)
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=False)
    print("copying: ", source_executable, " to ", dest_executable)
    shutil.copy(source_executable, dest_executable)
    # add dependencies.
    checker = AppBundleChecker(dest_executable, app_path_override=True)
    checker.check_executable(dest_executable)
    dylibs = glob.glob(os.path.join(dest_dir, "*dylib"))
    for d in dylibs:
        checker.check_executable(d)
    if os.environ.get('DEVELOPER_CERT'):
        Execute(['codesign -s "' + os.environ.get('DEVELOPER_CERT') + '" -v -f ' + dest_dir + "/*"])


def OsxCmdlineApp(env, target, source):
    createCmdline = env.CreateOsxCmdlineApp(target, source)
    env.AlwaysBuild(createCmdline)
    return createCmdline


def generate(env):
    """Add Builders and construction variables to the Environment."""

    # find macdeployqt command
    env['MACDEPLOYQT'] = _find_mdqt(env)

    # Define the entire osx app process builder.
    bldr = Builder(action=_createOsxQtApp)
    env.Append(BUILDERS={'CreateOsxQtApp': bldr})

    env.AddMethod(OsxQtApp, "OsxQtApp")

    bldr = Builder(action=_createOsxCmdlineApp)
    env.Append(BUILDERS={'CreateOsxCmdlineApp': bldr})

    env.AddMethod(OsxCmdlineApp, "OsxCmdlineApp")


def exists(env):
    if sys.platform != 'darwin':
        raise SCons.Errors.StopError(
            NotAnOsxSystem,
            "Trying to create an application bundle on a non-OSX system")
    return _find_mdqt(env)
