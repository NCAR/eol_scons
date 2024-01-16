# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
Use GetBuildFailures() in recent SCons versions to cache the commands which
cause a build to fail.  Then rerun just those commands in subsequent SCons
runs and avoid the delays from reading all the SConscript files.

After loading the 'rerun' tool in the top-level SConstruct environment,
short-circuit the rest of the SConscript files using code like this:

@code

env = Environment(tools = ['default', 'rerun'])

if env.Rerun():
    Return()

@endcode

All the SConscript() calls would follow.

Once the rerun commands succeed, then a full scons build is repeated to
make sure all the dependencies are updated and the build continues past the
failed commands.

The intention is that it will be faster to iterate through compiles when
fixing a source file.  Until the file compiles successfully, scons will
keep running the exact same compile command on each iteration.

Pass rerun=1 to enable command reruns.  If it causes problems, pass rerun=0
to disable reruns and to remove any existing rerun command cache.
"""

import os
import sys
import atexit
import pickle

from SCons.Variables import BoolVariable
from SCons.Script import SetOption
from SCons.Script import GetBuildFailures

# Cache the scons command with all its arguments
_scons_command = sys.argv[:]

_last_command_path = None

_options = None

def bf_to_str(bf):
    """Convert an element of GetBuildFailures() to a string
    in a useful way."""
    import SCons.Errors
    if bf is None: # unknown targets product None in list
        return '(unknown tgt)'
    elif isinstance(bf, SCons.Errors.StopError):
        return str(bf)
    elif bf.node:
        return str(bf.node) + ': ' + bf.errstr
    elif bf.filename:
        return bf.filename + ': ' + bf.errstr
    return 'unknown failure: ' + bf.errstr


def build_status():
    """Convert the build status to a 2-tuple, (status, msg)."""
    bf = GetBuildFailures()
    failures_message = ''
    if bf:
        # Cache the command for the first failed target.
        nodes = []
        for x in bf:
            if x is None:
                continue
            sources = [ str(s) for s in x.node.sources ]
            nodes.append((str(x.node), sources, x.command))
            failures_message += "Failed building %s\n" % bf_to_str(x)
        # If the command cache already exists, then these build failures
        # are from running those commands, so don't rewrite the cache file.
        if not os.path.exists(_last_command_path):
            lc = open(_last_command_path, "w")
            pickle.dump(nodes, lc)
            lc.close()
            print("Failed commands cached: %s" % _last_command_path)
	# bf is normally a list of build failures; if an element is None,
	# it's because of a target that scons doesn't know anything about.
        status = 'failed'
    else:
        # if bf is None, the build completed successfully.
        status = 'ok'
    return (status, failures_message)


def display_build_status():
    """Display the build status.  Called by atexit.
    Here you could do all kinds of complicated things."""
    status, failures_message = build_status()
    if status == 'failed':
        print(failures_message)
    elif status == 'ok':
        # If we succeeded, and there was a last command file, then we
        # need to re-run the command without the last command file.
        if os.path.exists(_last_command_path):
            # lin = open(_last_command_path, "r")
            # nodes = pickle.load(lin)
            # lin.close()
            # for n in nodes:
            #     target = n[0] + ".rerun"
            #     print("Renaming: %s -> %s" % (target, n[0]))
            #     os.rename(target, n[0])
            os.unlink(_last_command_path)
            print("Last failed commands succeeded.\n" +
                  "Re-running scons to complete the build...")
            os.execv(_scons_command[0], _scons_command)
        print("Build succeeded.  No commands to rerun.")


def Rerun(env):
    global _last_command_path
    _last_command_path = env.File("#/scons_rerun_commands.txt").get_abspath()
    enabled = env.get('rerun')
    exists = os.path.exists(_last_command_path)

    # Check for last failed commands, and if found, just run those commands
    # before trying anything else.
    if exists and not enabled:
        # Disabled, so delete the cache.
        os.unlink(_last_command_path)
        print("Removed rerun command cache.")
    elif exists:
        print("Creating builder to rerun failed commands...")
        # Ask SCons not to change or scan dependencies.
        SetOption("implicit_cache", 1)
        lin = open(_last_command_path, "r")
        nodes = pickle.load(lin)
        lin.close()
        for n in nodes:
            # Use a different name for the rerun target, so it doesn't
            # interfere with the cached dependencies for the original
            # target.
            target = n[0] + ".rerun"
            env.Command(target, None, " ".join(n[2]))

    if enabled:
        atexit.register(display_build_status)
    return enabled and exists


def generate(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.AddVariables(BoolVariable(
                'rerun',
                'Enable immediate rerun of failed commands.',
                None))
    _options.Update(env)
    env.AddMethod(Rerun)


def exists(env):
    return True


