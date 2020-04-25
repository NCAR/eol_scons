import os
from eol_scons import parseconfig

_options = None

def getPrefix(env, apply_config = False):
    matchdir = env.FindPackagePath('COIN_DIR','$OPT_PREFIX/Coin*')
    prefixes = [ env.get('COIN_DIR'), "/usr/local", matchdir, 
                 env.get('OPT_PREFIX'), "/usr"]
    return parseconfig.ParseConfigPrefix(env, 'coin-config', prefixes,
                                         apply_config = apply_config)


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('COIN_DIR', """Set the Coin directory.
Use the first coin-config found in this list of paths:
 $COIN_DIR/bin, /usr/local/bin, $OPT_PREFIX/Coin*/bin, 
 $OPT_PREFIX/bin, and /usr/bin.
/usr/local/bin is searched early since it is the default installation 
for the Coin version on which Quarter depends.""", 
                     getPrefix(env))
        
    _options.Update(env)
    prefix = getPrefix(env, apply_config = True)
    if env['PLATFORM'] == 'darwin':
        env.Append(LIBS=["coin"])
        env.AppendUnique(FRAMEWORKS=["CoreFoundation"])

    if (env['PLATFORM'] =='posix'):
        env.Append(LIBS=["Coin", 'GLU', 'dl', 'GL','X11'])

    if env['PLATFORM'] == 'msys':
        env.AppendUnique(CPPDEFINES=["COIN_NOT_DLL"])
        env.AppendUnique(CPPPATH=["$COIN_DIR/include"])
        env.Append(LIBPATH=["$COIN_DIR/lib"])
        env.Append(LIBS=["Coin"])
        env.Append(LIBS=['opengl32'])
        env.Append(LIBS=['glu32'])
        env.Append(LIBS=['gdi32'])
        env.Append(LIBS=['openal'])
    if 'COIN_DOXDIR' not in env:
        # When installed into the system as the Coin2-devel package,
        # the doxygen html has a custom path.
        if prefix == '/usr':
            env['COIN_DOXDIR'] = '/usr/share/Coin3/Coin'
        else:
            env['COIN_DOXDIR'] = "%s/share/Coin/html" % (prefix)
    env.SetDefault(COIN_DOXREF='${COIN_DOXDIR}/coin.tag:${COIN_DOXDIR}')
    env.AppendDoxref('$COIN_DOXREF')


def exists(env):
    return True

