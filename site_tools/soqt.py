import os
import string
from eol_scons import parseconfig

options = None

def getPrefix(env):
    matchdir = env.FindPackagePath('SOQT_DIR','$OPT_PREFIX/SoQt*')
    prefixes = [ env.get('SOQT_DIR'), matchdir, env.get('COIN_DIR'),
                 env.get('OPT_PREFIX'), "/usr" ]
    return parseconfig.ParseConfigPrefix(env, 'soqt-config', prefixes)


def generate(env):
    global options
    if not options:
        options = env.GlobalOptions() 
        options.Add('SOQT_DIR', """Set the SoQt directory.
If not set, look for a directory matching SoQt* under $OPT_PREFIX.
Use the first soqt-config found in this list of paths:
 $SOQT_DIR/bin, $COIN_DIR/bin, $OPT_PREFIX/bin, and finally /usr/bin.""",
                    getPrefix(env))
    options.Update(env)
    prefix = getPrefix(env)

    if not env.has_key('SOQT_DOXDIR'):
        # When installed into the system as the SoQt-devel package,
        # the doxygen html has a custom path.
        if prefix == '/usr':
            env['SOQT_DOXDIR'] = '/usr/share/Coin2/SoQt'
        else:
            env['SOQT_DOXDIR'] = '%s/share/SoQt/html' % (prefix)
    if not env.has_key('SOQT_DOXREF'):
        env['SOQT_DOXREF'] = 'soqt:%s' % env['SOQT_DOXDIR']
    env.AppendDoxref(env['SOQT_DOXREF'])
    env.Append(DEPLOY_SHARED_LIBS='SoQt')
    if env['PLATFORM'] != 'win32':
        env.Append(LIBS='Xi')
    # This is needed especially to get the doxygen reference.
    env.Require(['PKG_COIN'])

def exists(env):
    return True

