import os

options = None

def generate(env):
    global options
    if not options:
        options = env.GlobalOptions()
        options.Add('COIN_DIR', 'Set the Coin directory.', 
                    env.FindPackagePath('COIN_DIR','$OPT_PREFIX/Coin*','/usr'))

    options.Update(env)
    coin_dir = env['COIN_DIR']
    if env['PLATFORM'] != 'win32':
        coin_config = os.path.join(coin_dir, 'bin', 'coin-config')
        env.ParseConfig(coin_config + ' --cppflags --ldflags --libs')
        prefix=os.popen(coin_config + ' --prefix').read().strip()
    else:
        prefix="$OPT_PREFIX"
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

