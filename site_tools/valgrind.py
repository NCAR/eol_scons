"""\
Simple scons tool to find a valgrind executable and set the VALGRIND_PATH
construction variable accordingly.  The value will also be available in
the runtime environment, such as for test scripts executed by scons.

Also set VALGRIND_COMMAND according to these options provided to the
scons environment.  If valgrind is 'off', then VALGRIND_COMMAND will be
empty.  Set VALGRIND_VERSION to the valgrind version string
using 'valgrind --version'.

 valgrind={valgrind|callgrind|off}    
    Whether to run valgrind or callgrind or neither.
 
The valgrind Action runs another Action using valgrind

These are the expected uses of this tool:

 * Run a test script which runs a test program using VALGRIND_COMMAND:
     $VALGRIND_COMMAND ./test_program <program_options>   > test.log
   The script can add a suppressions file if it likes:
     if [ -n "$VALGRIND_COMMAND" ]; then
        vgopts="--suppressions=vg.suppresions"
     fi
 * Build a summary report of a valgrind log file which results in a failure
   when certain errors are detected.
     env.ValgrindLog("test.log", VALGRIND_LEAK_THRESHOLD=0, 
                                 VALGRIND_ERROR_THRESHOLD=0)

So everything can be combined with this:

   env.Valgrind("test_command ...options...", VALGRIND_ settings...)

or

   env.ValgrindLog(env.Test(...), VALGRIND_ settings...)

The Valgrind() builder first wraps the command in a Test() builder,
then parses the output.

If valgrind is not enabled, then ValgrindLog() and Valgrind() do not do
anything except run the test program.

Add a TEST_LOGFILE construction variable for Test() pseudo-builder, so the
logfile will be the target of the Test().  Can xtest still be an alias to
run the test in that case?

Valgrind builders should be added to the test alias too?  Or perhaps I have
this backwards: the Test() pseudo-builders should add the valgrind actions
instead of the other way around, eg, env.Test("command") will call the
valgrind builder automatically if enabled.  The test should run and have
the 'test' and 'xtest' aliases whether valgrind is run as part of it or
not.


"""

import os
import re
import SCons
from SCons.Builder import Builder
from SCons.Action import Action


class ValgrindWarning(SCons.Warnings.Warning):
    pass

_options = None

def findValgrind(env):
    global _options
    if not _options:
        _options = env.GlobalVariables()
        _options.Add('VALGRIND_PATH',
                     'Path to valgrind, or else "valgrind" if unset.')

    _options.Update(env)

    # Short circuit the test if VALGRIND_PATH is already set in the
    # run environment.
    if env.get('VALGRIND_PATH'):
        return env['VALGRIND_PATH']
    extra_paths = [ '/usr/bin' ]
    if env.has_key('OPT_PREFIX'):
        extra_paths.append("%s/bin" % env['OPT_PREFIX'])
    opts = ['el4','el3','ws3','fc4','fc3','fc2']
    extra_paths.extend([ "/net/opt_lnx/local_%s/bin" % o for o in opts])
    return env.WhereIs('valgrind', extra_paths)

def getValgrindPath(env):
    valgrind = findValgrind(env)
    if not valgrind:
        valgrind = "valgrind"
    return valgrind


def generate(env):
    valgrind = getValgrindPath(env)
    env['ENV']['VALGRIND_PATH'] = valgrind
    env['VALGRIND_PATH'] = valgrind


def exists(env):
    if not findValgrind(env):
        SCons.Warnings.warn(ValgrindWarning,
                            "Could not find valgrind program.")
        return False
    return True
