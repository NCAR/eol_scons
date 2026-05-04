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
import SCons
import SCons.Errors
import SCons.Warnings
import SCons.Node.FS
from SCons.Script import Environment, Delete, Copy, Mkdir

from eol_scons.appbundlechecker import AppBundleChecker
import eol_scons.installmode as im


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
    macdeployqt = env.WhereIs('macdeployqt')
    if macdeployqt:
        return macdeployqt

    if im.AllMode():
        return 'macdeployqt'

    raise SCons.Errors.StopError(
        MacdeployqtNotFound,
        "Could not find macdeployqt")
    return None


#
# Execute macdeployqt on a bundle
#
def _macdeployqt(bundle: SCons.Node.FS.Dir, env: Environment):
    """
    Run macdepoyqt on the bundle.

    Parameters:
    bundle -- The bundle directory, e.g. RICProxy-6454.app.
    env -- The SCons environment.
    """
    # Run macdeployqt.
    # macdeployqt will give volume name of bundle, so cd to directory just
    # above.
    cmd = im.Command(f'{env["MACDEPLOYQT"]} {bundle.name}')
    env.Execute(env.ChdirActions([cmd], bundle.get_dir()))


#
# Builder to create a bundle.
#
def _create_bundle(env, bundle, appname, version, exename, iconname,
                   plist=None):
    """
    Create and populate an OSX application bundle.
    """
    bundledir = bundle.get_abspath()
    contentsdir = env.Dir(bundledir + '/Contents')
    macosdir = env.Dir(bundledir + '/Contents/MacOS')
    resourcesdir = env.Dir(bundledir + '/Contents/Resources')

    # Get rid of the existing bundle. Otherwise macdeployqt gets bent out of
    # shape when it finds its products already there.
    env.Execute(Delete(bundle))

    # Buid the basic bundle structure
    env.Execute(Mkdir(bundledir))
    env.Execute(Mkdir(contentsdir))
    env.Execute(Mkdir(macosdir))
    env.Execute(Mkdir(resourcesdir))

    # Copy the executable and icon
    env.Execute(Copy(macosdir, exename))
    env.Execute(Copy(resourcesdir, iconname))
    if plist:
        # name needs to be exactly 'Info.plist'
        env.Execute(Copy(contentsdir.File('Info.plist'), plist))
    else:
        info = _make_info_plist(
            bundle_name=appname,
            bundle_identifier=exename,
            bundle_signature='ncar-eol-cds-qt-app',
            bundle_version=version,
            icon_filename=iconname)
        infofilepath = contentsdir.get_abspath() + '/Info.plist'
        with open(infofilepath, "w") as infoplistfile:
            infoplistfile.write(info)


def _fix_app_bundle_paths(env, app):
    brew_prefix = env['MACOS_PREFIX']
    checker = AppBundleChecker(app, brew_prefix=brew_prefix)
    if im.MockMode():
        im.MockEcho(f'AppBundleChecker({app}, brew_prefix={brew_prefix})')
        return
    checker.check()


def _createOsxQtApp(target, source, env):
    """
    Create an OSX application bundle for a Qt application.

    Parameters:
    target[0] -- The bundle directory, e.g. RICProxy-6454.app.

    source[0] -- The application executable to be bundled, e.g. ric_proxy.
    source[1] -- The application icon file, e.g.
                 '#/Resources/proxy/proxyIcon.icns'
    source[2] -- (optional) The Info.plist file to be used in the bundle.
                 If not provided, a default one will be created with
                 the appropriate fields filled in.

    env['EXENAME']    -- e.g. ric_proxy
    env['VERSION']   -- e.g. 6454
    env['ICON']      -- e.g. '#/Resources/proxy/proxyIcon.icns'
    env['PLIST']     -- (optional) The path to the Info.plist file to be
                        used in the bundle.
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
    _create_bundle(env, bundle, appname, version, exename, iconname,
                   plist=plist)
    # run macdeployqt
    _macdeployqt(bundle, env)
    # finish what macdeployqt started
    _fix_app_bundle_paths(env, bundle.path)
    # codesign if cert is present
    cert = os.environ.get('DEVELOPER_CERT')
    if cert:
        cmd = f'codesign -s "{cert}" -v -f --deep {bundle.path}'
        env.Execute(im.Command(cmd))


def OsxQtApp(env, destdir, appexe, appicon, appname, appversion, plist=None,
             *args, **kw):
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
    plist     -- (optional) Path to Info.plist file to be used in the bundle.
    """

    # Establish some useful attributes.
    bundledir = env.Dir(str(destdir))

    sources = [appexe, appicon]
    if plist:
        sources.append(plist)
    bundle = env.Command(bundledir, sources, action=_createOsxQtApp,
                         VERSION=appversion, APPNAME=appname)
    env.AlwaysBuild(bundle)
    return bundle


def _createOsxCmdlineApp(target, source, env: Environment):
    """
    Parameters:

    target[0]   -- Path to the versioned destination directory.
    source[0]   -- The cmdline executable to be deployed
    """
    env.Execute(Delete(target[0]))
    env.Execute(Mkdir(target[0]))
    env.Execute(Copy(target[0], source[0]))
    destexe = target[0].File(source[0].name)
    checker = AppBundleChecker(str(destexe), app_path_override=True)
    im.MockEcho(f'AppBundleChecker({destexe}, app_path_override=True)')
    if not im.MockMode():
        checker.check_executable(str(destexe))
    im.MockEcho(f'checker.check_executable({destexe})')
    dylib_pattern = os.path.join(str(target[0]), "*dylib")
    dylibs = glob.glob(dylib_pattern)
    if im.MockMode():
        im.MockEcho(f'checker.check_executable({dylib_pattern})')
    else:
        for d in dylibs:
            checker.check_executable(d)
    frameworks_pattern = os.path.join(str(target[0]), "*framework")
    frameworks = glob.glob(frameworks_pattern)
    for f in frameworks:
        checker.check_framework(f)
    cert = os.environ.get('DEVELOPER_CERT')
    if cert:
        cmd = f'codesign -s "{cert}" -v -f {target[0]}/*'
        env.Execute(im.Command(cmd))


def OsxCmdlineApp(env, target, source):
    createCmdline = env.Command(env.Dir(target), source,
                                action=_createOsxCmdlineApp)
    env.AlwaysBuild(createCmdline)
    return createCmdline


def generate(env):
    """Add Builders and construction variables to the Environment."""

    # find macdeployqt command
    env['MACDEPLOYQT'] = _find_mdqt(env)

    # in all mode, provide default MACOS_PREFIX to avoid missing key errors
    if im.AllMode() and 'MACOS_PREFIX' not in env:
        env['MACOS_PREFIX'] = "/opt/local"

    # Define the entire osx app process builder.
    env.AddMethod(OsxQtApp, "OsxQtApp")
    env.AddMethod(OsxCmdlineApp, "OsxCmdlineApp")


def exists(env):
    # _find_mdqt raises an error if not found
    return _find_mdqt(env)
