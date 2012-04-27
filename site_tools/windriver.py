# Tool for the Jungo WinDriver generic driver library and headers
#
# If construction variable WINDRIVER_DIR is set, it is taken as the top 
# directory of the WinDriver distribution being used. Otherwise, we look
# for a directory matching "WinDriver*" under OPT_PREFIX.
#
# This tool adds header paths for the WinDriver API and adds the necessary
# API library.
import os
import re
from eol_scons import parseconfig
import SCons

_options = None

# Get the base directory for WinDriver, trying the value of WINDRIVER_DIR
# (if any) first, then for the last directory which matches the glob 
# '$OPT_PREFIX/WinDriver*'. None is returned if no directory is found.
def getBasedir(env):
    matchdir = env.get('WINDRIVER_DIR')
    if (matchdir):
        if (not os.path.exists(matchdir)):
            print '\nERROR: No directory exists matching WINDRIVER_DIR (%s)' % matchdir
            return None
    else:
        matchdir = env.FindPackagePath(None, '$OPT_PREFIX/WinDriver*')

    return matchdir


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('WINDRIVER_DIR', 
                     'The WinDriver top directory. If this is not set, SCons will look\n' + 
                     'for WinDriver under OPT_PREFIX ($OPT_PREFIX)', 
                     None)
        
    _options.Update(env)
    basedir = getBasedir(env)
    if (not basedir):
        # Print an error message and force printing of the help message
        # (and exit before actually building)
        print ''
        print 'ERROR: No WinDriver base directory found. Use --help and see OPT_PREFIX and WINDRIVER_DIR.'
        print ''
        # If the user specified -h, return and let them see the help message 
        # they asked for. Otherwise exit with an error now.
        if (SCons.Script.GetOption('help')):
            return
        else:
            raise SCons.Errors.StopError
        
        return

    # We need to get the WinDriver version number from the base directory string.
    # By default, WinDriver installation is under a directory named 
    # WinDriver<version>, e.g., WinDriver1031. We need the numeric portion,
    # or '1031' in this example. We test both the given pathname and its canonical 
    # version, in case someone is using a symbolic link like /opt/WinDriver ->
    # /opt/WinDriver1031.
    versionString = None
    testpaths = [basedir, os.path.realpath(basedir)]
    for path in testpaths:
        try:
            # Look for the string 'WinDriver' immediately followed by digits
            # in the pathname. Set versionString to the series of digits if
            # we found them 
            versionString = re.search('.*WinDriver(?P<version>\d+)', path).groupdict()['version']
            break
        except:
            continue
        
    if (not versionString):
        errmsg = 'No WinDriver version number found in tested path names:', testpaths
        # If the user specified -h, return and let them see the help message 
        # they asked for. Otherwise exit with an error now.
        if (SCons.Script.GetOption('help')):
            return
        else:
            raise SCons.Errors.StopError


    # Headers are sometimes requested relative to <basedir>/include and sometimes 
    # relative to <basedir>
    env.AppendUnique(CPPPATH=[os.path.join(basedir, 'include'), basedir])
    
    # The WinDriver library includes the version number in the name, e.g., 
    # libwdapi1031.so. It is installed into a system default location, so
    # we don't need to worry about adding a -L search path.
    libname = 'wdapi' + versionString
    env.AppendLibrary(libname)

def exists(env):
    return True

