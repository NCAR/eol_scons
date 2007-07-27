import os
import string

options = None

def generate(env):
    global options
    if not options:
        options = env.GlobalOptions() 
        options.Add('SOQT_DIR', 'Set the SoQt directory.', 
                    env.FindPackagePath('SOQT_DIR','$OPT_PREFIX/SoQt*','/usr'))
    options.Update(env)
    soqt_dir = env['SOQT_DIR']
    soqt_config = os.path.join(soqt_dir, 'bin', 'soqt-config')
    env.ParseConfig(soqt_config + ' --cppflags --ldflags --libs')
    prefix = os.popen(soqt_config + ' --prefix').read().strip()
    ldflags = os.popen(soqt_config + ' --ldflags').read().split()
    libdirs = []
    for flag in ldflags:
        if (flag.strip().index('-L') == 0):
            # remove the -L to get the directory, and make the resulting 
            # path absolute
            dir = os.path.abspath(flag.replace('-L', ''))
            env.Append(RPATH=dir)

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
    env.Append(LIBS='Xi')
    # This is needed especially to get the doxygen reference.
    env.Require(['PKG_COIN'])

def exists(env):
    return True

