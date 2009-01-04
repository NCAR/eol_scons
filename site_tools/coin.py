import os
from eol_scons import parseconfig

_options = None

def getPrefix(env, apply_config = False):
    matchdir = env.FindPackagePath('COIN_DIR','$OPT_PREFIX/Coin*')
    prefixes = [ env.get('COIN_DIR'), matchdir, env.get('OPT_PREFIX'), "/usr"]
    return parseconfig.ParseConfigPrefix(env, 'coin-config', prefixes,
                                         apply_config = apply_config)


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalOptions()
        _options.Add('COIN_DIR', """Set the Coin directory.
If not set, look for a directory matching Coin* under $OPT_PREFIX.
Use the first coin-config found in this list of paths:
 $COIN_DIR/bin, $OPT_PREFIX/bin, and /usr/bin.""", getPrefix(env))
        
    _options.Update(env)
    prefix = getPrefix(env, apply_config = True)
    if env['PLATFORM'] == 'win32':
        env.Append(CPPDEFINES=["COIN_DLL"])
        env.AppendUnique(CPPPATH=["$COIN_DIR/include"])
        env.Append(LIBPATH=["$COIN_DIR/lib"])
        env.Append(LIBS=["coin2d"])
    if not env.has_key('COIN_DOXDIR'):
        # When installed into the system as the Coin2-devel package,
        # the doxygen html has a custom path.
        if prefix == '/usr':
            env['COIN_DOXDIR'] = '/usr/share/Coin2/Coin'
        else:
            env['COIN_DOXDIR'] = "%s/share/Coin/html" % (prefix)
    if not env.has_key('COIN_DOXREF'):
        env['COIN_DOXREF'] = "coin:%s" % env['COIN_DOXDIR']
    env.AppendDoxref(env['COIN_DOXREF'])
    env.AppendUnique(DEPLOY_SHARED_LIBS=['Coin'])


def exists(env):
    return True

