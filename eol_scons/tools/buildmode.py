"""
Accept a list of known 'build modes', such as optimization and compiler
warnings, which are mapped to different compiler options on different
platforms.  The mapping happens by applying each mode as a tool, and the
tool in turn tries to apply the right method from the Environment instance.
Different platform compiler tools, such as gcc and msvc, provide the
environment methods which set the right compiler flags for the build mode.

This seems more circuitous than necessary.  Another option is for a build
mode to just be its own tool, which tests the current platform to decide
what options to apply.  However, it makes more object-oriented sense to
group the settings in the compiler tool.  The specific build mode tools
like warnings.py and optimize.py could be removed in favor of calling
directly the right method on the environment instance based on the
buildmode name.

The problem then is how to specify options and defaults to buildmode, since
it is applied when it is loaded.

"""

from SCons.Script import ListVariable

import eol_scons

def generate(env):
    env.SetDefault(BUILDMODE_DEFAULT='debug,warnings,optimize')
    options = env.GlobalVariables()
    if 'buildmode' not in options.keys():
        modes = ['debug', 'warnings', 'optimize', 'profile', 'cppcheck']
        options.AddVariables(
            ListVariable('buildmode', """\
Select basic building modes such as debugging and optimization.
By default, all three of debugging, warnings, and optimization are enabled
if the compiler supports it.  The modes can be selected and combined using
a comma-separated list.  The default for this project is '%s'.""" %
                         (env['BUILDMODE_DEFAULT']),
                         "${BUILDMODE_DEFAULT}", modes))
    options.Update(env)
    buildmodes = env.subst("${buildmode}").split(" ")
    if 'all' in buildmodes:
        buildmodes = modes
    for mode in buildmodes:
        if not mode or mode == 'none':
            continue
        try:
            if mode == 'debug':
                env.Debug()
            elif mode == 'optimize':
                env.Optimize()
            elif mode == 'warnings':
                env.Warnings()
            elif mode == 'profile':
                env.Profile()
            else:
                env.Tool(mode)
        except:
            print("No '%s' buildmode settings for this platform." % (mode))

def exists(env):
    return True
