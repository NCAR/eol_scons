# -*- python -*-
from __future__ import print_function
import os
import string
from eol_scons import parseconfig

_options = None

_removed_already_warned = False

def getPrefix(env, apply_config = False):
    matchdir = env.FindPackagePath('SOQT_DIR','$OPT_PREFIX/SoQt*')
    prefixes = [ env.get('SOQT_DIR'), matchdir, env.get('COIN_DIR'),
                 env.get('OPT_PREFIX'), "/usr" ]
    return parseconfig.ParseConfigPrefix(env, 'soqt-config', prefixes,
                                         apply_config = apply_config)


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables() 
        _options.Add('SOQT_DIR', """Set the SoQt directory.
If not set, look for a directory matching SoQt* under $OPT_PREFIX.
Use the first soqt-config found in this list of paths:
 $SOQT_DIR/bin, $COIN_DIR/bin, $OPT_PREFIX/bin, and finally /usr/bin.""",
                    getPrefix(env))
    _options.Update(env)
    prefix = getPrefix(env, apply_config = True)

    # As a special case, if QT4DIR is not /usr/lib64/qt4 or /usr/lib/qt4,
    # then remove all elements from CPPPATH and LIBPATH with those paths.
    # SoQt may have been built against a different Qt4, such as the one
    # installed in the system, but this tool needs to force the Qt4
    # configuration chosen here.

    def find_path(paths, p):
        for i, path in enumerate(paths):
            if p in str(path):
                return i
        return -1

    def remove_path(paths, p):
        if not paths:
            return 0
        n = 0
        i = find_path(paths, p)
        while i >= 0:
            del paths[i]
            n += 1
            i = find_path(paths, p)
        return n

    removed = 0
    if env.get('QT4DIR') != "/usr/lib64/qt4":
        removed += remove_path(env.get('CPPPATH'), "/usr/lib64/qt4")
        removed += remove_path(env.get('LIBPATH'), "/usr/lib64/qt4")
    if env.get('QT4DIR') != "/usr/lib/qt4":
        removed += remove_path(env.get('CPPPATH'), "/usr/lib/qt4")
        removed += remove_path(env.get('LIBPATH'), "/usr/lib/qt4")
    global _removed_already_warned
    if removed > 0 and not _removed_already_warned:
        print("soqt: removed %d extraneous qt4 paths from soqt-config." % removed)
        _removed_already_warned = True

    if 'SOQT_DOXDIR' not in env:
        # When installed into the system as the SoQt-devel package,
        # the doxygen html has a custom path.
        if prefix == '/usr':
            env['SOQT_DOXDIR'] = '/usr/share/Coin2/SoQt'
        else:
            env['SOQT_DOXDIR'] = '%s/share/SoQt/html' % (prefix)
    env.SetDefault(SOQT_DOXREF='soqt:$SOQT_DOXDIR')
    env.AppendDoxref('$SOQT_DOXREF')
#    env.Append(DEPLOY_SHARED_LIBS=['SoQt'])
    if (env['PLATFORM'] != 'win32') and (env['PLATFORM'] != 'darwin'):
        env.Append(LIBS=['Xi'])
    # This is needed especially to get the doxygen reference.
    env.Require(['coin'])
    if env['PLATFORM'] == 'win32':
        env.Append(CPPDEFINES=["SOQT_NOT_DLL"])
        env.Append(LIBS=['SoQt'])
        env.Append(LIBS=['opengl32'])
        env.Append(LIBS=['glu32'])
        

    

def exists(env):
    return True

