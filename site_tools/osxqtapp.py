"""
SCons.Tool.osxqtapp

Create an OSX application bundle from a qt executable

sources: the qt executable and the application icon.
targets: the directory that the bundle will be created in.

process:
 - Remove the existing bundle, if present.
 - Populate the bundle directory tree with the executable and icon files.
 - create Info.plist and copy to Contents/
 - run macdeployqt on the bundle, which copies in needed frameworks and libraries.
 
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

import os
from SCons.Script import *

class ToolOsxQtAppWarning(SCons.Warnings.Warning):
    pass

class MacdeployqtNotFound(ToolOsxQtAppWarning):
    pass

class NotAnOsxSystem(ToolOsxQtAppWarning):
    pass

SCons.Warnings.enableWarningClass(ToolOsxQtAppWarning)


def _make_info_plist(bundle_name, appexe_filename, icon_filename):
    """
    Return a customized Info.plist.
    
    Parameters:
       bundle_name -- The bundle name.
       appexe_filename -- The name that the executable will have in the MacOS directory.
       icon_filename -- The name that the icon will have in the Resources directory.
       
    """
    
    
    bundleName        = str(bundle_name)
    bundleDisplayName = str(bundle_name)
    bundleIdentifier  = "ncar.eol.cds." + str(appexe_filename)
    bundleVersion     = "0.9"
    bundleSignature   = "ncar_eol_cds_qt_app"
    bundleExecutable  = str(appexe_filename)
    bundleIconFile    = str(icon_filename)
    
    info = r"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
    """ %(
        bundleName, 
        bundleDisplayName,
        bundleIdentifier, 
        bundleVersion, 
        bundleSignature, 
        bundleExecutable, 
        bundleIconFile
    )
    
    return info
    
def _detect(env):
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
# Builder
#
def _create_bundle(target, source, env):
    """
    Create and populate an OSX application bundle.
    
    Parameters:
    target[0] -- The destination in the bundle for the executable file.
    target[1] -- The destination in the bundle for the icon file.
    target[2] -- The bundle directory path.
    source[0] -- The source of the executable file.
    source[1] -- The source of the icon file.
    """
    
    # Copy the executable and icon
    for t, s in zip(target[0:2], source):
        # Create the directory.
        dir = os.path.dirname(str(t))
        try:
           os.makedirs(dir)
        except:
            if not os.access(dir, os.W_OK): throw
        # Copy the file
        Execute(Copy(t, s))
        
    # Create Info.plist
    exename = os.path.basename(str(source[0]))
    iconname = os.path.basename(str(source[1]))
    # @todo Need to find a way to pass the bundle name to the builder.
    info = _make_info_plist('Proxy', exename, iconname)
    infoplistfile = file(str(target[2]),"w")
    infoplistfile.write(info)
	
def OsxQtApp(env, destdir, appexe, appicon, *args, **kw):
    """
    A pseudo-builder to create an OSX application bundle for a Qt application.
    
    An OSX application bundle hierarchy is created, and the executable and 
    other artifacts are copied in. The macdeployqt application is run on
    the bundle in order to bring in supporting frameworks and libraries.
    
    The bundle name will be the application executable name + '.app'. Thus
    if the executable is #/code/proxy, and the destination directory is '.',
    the bundle will be built in './proxy.app'. 
    
    This restriction on naming is due to the macdeployqt requirement that the 
    bundle name prefix (proxy of proxy.app) and the executable file within 
    must be exactly the same. There may be some artful way to work around this,
    left for later development.
    
    NOTE: The bundle must not be created in the same directory as where the 
    the executable is located. For some reason, in this situation SCons
    will erase the executable. 
    @todo Detect this situation and raise an error.
    
    Parameters:
    destdir -- The directory where the bundle will be created.
    appexe  -- The path to the application executable.
    appicon -- The path to the application icon.
    
    """
            
    # Establish some useful attributes.
    appname = str(os.path.basename(appexe))
    appdir = Dir(str(destdir) + '/' + appname + '.app')
    exe  = File(str(appdir) + '/Contents/MacOS/' + appname)
    icon = File(str(appdir) + '/Contents/Resources/' + str(os.path.basename(appicon)))
    info = File(str(appdir) + '/Contents/Info.plist')
    
    # Delete existing app.
    Execute(Delete(appdir))
    
    # Define the bundle builder.
    bldr = Builder(action = _create_bundle);
    env.Append(BUILDERS = {'MakeBundle' : bldr})
    
    # Define the macqtdeploy builder.
    mdqt = Builder(action = env['MACDEPLOYQT'] + ' $SOURCE')
    env.Append(BUILDERS = {'MacDeployQt' : mdqt})
    
    # Create the bundle.
    target = [exe, icon, info, appdir]
    source = [appexe, appicon]
    bundleit = env.MakeBundle(target, source)

    # Run macdeployqt on the bundle.
    bogustarget = 'osx_qt_app_'+appname
    macit = env.MacDeployQt(bogustarget, bundleit[3])
    
    return macit
    
def generate(env):
    """Add Builders and construction variables to the Environment."""

    # find macdeployqt command
    env['MACDEPLOYQT'] = _detect(env)

    env.AddMethod(OsxQtApp, "OsxQtApp")

def exists(env):
    if (sys.platform != 'darwin'):
        raise SCons.Errors.StopError(
            NotAnOsxSystem,
            "Trying to create an application bundle on a non-OSX system")
        return None

    return _detect(env) 
    
