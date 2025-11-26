# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
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


def generate(env):
    env.SetDefault(BUILDMODE_DEFAULT='debug,warnings,optimize')
    options = env.GlobalVariables()
    if 'buildmode' not in options.keys():
        modes = ['debug', 'warnings', 'optimize', 'profile', 'cppcheck',
                 'errors']
        options.AddVariables(
            ListVariable('buildmode', """\
Select build modes, such as to enable debug, warnings, and optimization.
The errors mode uses -Werror to fail on warnings.
Default for this project: %s.""" % (env['BUILDMODE_DEFAULT']),
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
            elif mode == 'errors':
                # someday this could be customized according to the compiler
                # in the corresponding compiler tool (eg gcc.py), but for now
                # just assume it will only be used with compilers which
                # support the gcc flag.
                env.AppendUnique(CCFLAGS=['-Werror'])
            else:
                env.Tool(mode)
        except AttributeError:
            print("No '%s' buildmode settings for this platform." % (mode))


def exists(env):
    return True
