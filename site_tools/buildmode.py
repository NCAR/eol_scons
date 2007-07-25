
from SCons.Script import EnumOption

import eol_scons

options = None

def generate(env):
    global options
    if not options:
        options = env.GlobalOptions()
        options.AddOptions(
            EnumOption('buildmode',
                       'Select basic building modes, ' +
                       'such as for debugging or optimization.',
                       'debug',
                       allowed_values=('debug', 'release')))
    options.Update(env)
    if env.has_key('buildmode') and env['buildmode'] == 'release':
        env.Tool('optimize')
    else:
        env.Tool('debug')
        env.Tool('warnings')


def exists(env):
    return True
