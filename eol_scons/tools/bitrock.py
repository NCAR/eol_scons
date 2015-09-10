"""
SCons.Tool.osxqtapp

Create a BitRock installer from an application and a BitRock configuration. Currently
only runs on Windows and OSX.

See BitRock() for the parameter descriptions.

Example usage (OSX):
    installerdir = Dir('RIC-' + svnrevision + '.app')
    sources = Dir('#/installers/mac/RICProxy-' + svnrevision + '.app')
    installer = env.BitRock(installerdir, bitrockxml, [sources], svnrevision)

"""

import os
import sys
import subprocess
from SCons.Script import *

def _find_bitrock(env):
    """ 
    Look for the BitRock command line application.
    
    Returns the path to the executable, if found. Otherwise
    returns None.
    """
    try: 
        return env['BITROCK']
    except KeyError: 
        pass

    if sys.platform == 'win32':
        node = env.FindFile('builder-cli.exe', ['C:/Tools/BitRock/bin/'])
        return node
    
    if sys.platform == 'darwin':
    	node = env.FindFile(
    	    'installbuilder.sh',
    	    ['/Applications/BitRock/bin/Builder.app/Contents/MacOS/'])
    	return node
    	
    return None

#
# Builder to run bitrock and create an installer.
#
def _bitrock(target, source, env):
    """
    Parameters:
    
    target[0]   -- The generated installer path name. We don't use it.
    source[0]   -- The bitrock xml definition.
    source[1:]  -- Other source dependencies.
    
    Environment values:
    env['SVNVERSION'] -- The version number to be passed to bitrock.
    """
    
    sources = source
    if type(sources) != type(list()):
        sources = [source]

    bitrock = str(env['BITROCK'])
    svnversion = env['SVNVERSION']
    xml = str(sources[0])
    
    # Run bitrock.
    subprocess.check_call([bitrock, 'build', xml, '--setvars', 'svnversion='+svnversion,], 
        stderr=subprocess.STDOUT, bufsize=1)

def BitRock(env, destfile, bitrockxml, source, svnversion, *args, **kw):
    """
    A psuedo-builder for creating BitRock installers. 
    
    The recipe for creating the installer is provided in BitRock xml 
    specification file. In general this file is edited using the BitRock GUI 
    application, although some modification is possible with a text editor. But
    if you break it, you get to keep the pieces.
    
    The bitrock xml configuration has an explicitly named output file,
    and many source files. We will always run bitrock, since it would be hard to
    account for all of these dependencies. Perhaps in the future we can
    come up with a scheme to allow this routine to specify the output 
    file path for bitrock; this will involve modifying the bitrock xml
    file. 
    
    The svnversion value is passed to bitrock as the svnversion variable.

 	Parameters:
 	destfile   -- The target generated installer file. This should be 
 	              the same as the output file specified in the xml file.
 	bitrockxml -- The bitrock configuration
 	sources    -- Other dependencies that should trigger a rebuild.
 	svnversion -- The version number that will be fed to bitrock.
 	 
    """
    
    sources = source
    if type(sources) != type(list()):
        sources = [source]

    # Create the installer dependencies and actions.
    installer = env.RunBitRock(destfile,  [bitrockxml] + sources, SVNVERSION=svnversion)
    env.AlwaysBuild(installer)
    env.Clean(installer, installer)

    return installer
    
def generate(env):
    """Add Builders and construction variables to the Environment."""

    # Define the BitRock builder.
    bldr = Builder(action = _bitrock);
    env.Append(BUILDERS = {'RunBitRock' : bldr})
    
    # find the BitRock command
    env['BITROCK'] = _find_bitrock(env)

    # Define that all important method.
    env.AddMethod(BitRock, "BitRock")

def exists(env):
    return true
