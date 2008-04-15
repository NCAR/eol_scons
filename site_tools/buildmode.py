
from SCons.Script import ListOption

import eol_scons

_options = None

def generate(env):
    global _options
    if not _options:
        _options = env.GlobalOptions()
        defaultmodes = ['debug', 'warnings', 'optimize']
        modes = defaultmodes + ['profile']
        _options.AddOptions(
            ListOption('buildmode', """\
Select basic building modes such as debugging and optimization.
By default, all three of debugging, warnings, and optimization are enabled
if the compiler supports it.  The modes can be selected and combined using
a comma-separated list.""",
                       defaultmodes, modes))
    _options.Update(env)
    buildmodes = env.subst("${buildmode}").split(" ")
    for mode in buildmodes:
        if mode == 'all':
            env.Tool(modes)
        elif mode != '' and mode != 'none':
            env.Tool(mode)

def exists(env):
    return True
