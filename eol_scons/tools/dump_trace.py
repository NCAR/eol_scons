"""
The scons2ninja script (https://github.com/remko/scons2ninja) by Remko
Tronc,on depends upon a 'dump_trace' boolean command-line option, which
activates some nifty setup code to dump a trace of all the commands to
build the command-line targets.  Since that seems generally useful, it is
incorporated as a standard eol_scons tool.

Just require the 'dump_trace' tool, then pass dump_trace=1 on the command
line to print all the commands that would be run to build all the targets,
whether updated or not, without actually running any commands.
"""

import SCons
from SCons.Variables import BoolVariable

variables = None

def generate(env):
    global variables
    if variables is None:
        variables = env.GlobalVariables()
        variables.AddVariables(BoolVariable(
            'dump_trace', 'Dump trace of commands in dryrun mode.', False))
    variables.Update(env)
    if env['dump_trace']:
        env.SetOption('no_exec', True)
        env.Decider(lambda x, y, z: True)
        SCons.Node.Python.Value.changed_since_last_build = (lambda x, y, z: True)

def exists(env):
    return True

