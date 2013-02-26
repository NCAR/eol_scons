"""SCons tool to add methods useful for running and parsing test programs."""

# All test pseudo-builder methods take a name for the test (the alias) and
# the list of actions to execute to run that test, typically a shell
# command.  The default test alias is 'xtest', and this relative to the
# Environment's directory.  There is a global default test alias called
# 'test', and test targets can be added to this alias with the
# DefaultTest() method.
#
# Additionally, test output can be logged to a file, named <alias>.log in
# the Environment directory, and the output which gets shown on stdout can
# be filtered.  This allows the stdout output to be more concise while
# preserving all the debugging output in case it is needed for closer
# inspection.
#
# The eol_scons package always adds a Test() pseudo-builder by default.
# That method uses the 'xtest' and 'test' aliases by default, so it cannot
# be used to create other non-default test commands used during
# development.  Here is the equivalent of Test() using the methods in this tool:
#
#   xtest = env.DefaultTest(env.TestLog(None, test_program_targets, actions))
#
# If the test is only meant to run when specified explicitly, then provide
# a unique alias:
#
#   qtest = env.TestLog('qtest', test_program_targets, actions)
#
# Finally, there is a list of regular expression patterns for lines which
# should be allowed to pass to stdout from the test output.  This can be
# extended as needed.  Someday it might be useful to parameterize it.  Also it
# would be useful to be able to delegate the filtering.  For example, a valgrind
# output parser could extract information from the output and pass through only 
# the errors.  Then the filters could be broken down into types of output, such
# as boost tests, logx Checker tests, and valgrind checks.
#

import subprocess
import io
import sys
import re

from SCons.Script import DefaultEnvironment
from SCons.Action import Action
from SCons.Action import ListAction


_rxpatterns = [ r'^\d+ checks\.',
                r'^\d+ failures\.',
                r'^Running \d+ test cases\.\.\.',
                r'^.+\(N\): .* passed',
                r'^.+\(N\): .* FAIL',
                r'^\*\*\* No errors detected',
                r'^Leaving test case.*',
                r'^Entering test case.*',
                ]

_rxpass = [ re.compile(rx) for rx in _rxpatterns ]


def _pass_filter(line):
    for rx in _rxpass:
        if rx.search(line):
            return True
    return False


class _SpawnerLogger:

    def __init__(self):
        self.logpath = None
        self.logfile = None

    def open(self, logpath):
        self.logpath = logpath
        self.logfile = open(self.logpath, "w")
        print("Writing test log '%s', filtering stdout and stderr." % 
              (self.logpath))

    def close(self):
        if self.logfile:
            print("Closing test log '%s'." % (self.logpath))
            self.logfile.close()
            self.logfile = None
            self.logpath = None

    def spawn(self, sh, escape, cmd, args, env):
        cmd = [sh, '-c', ' '.join(args)]
        # print("Running SpawnerLogger.spawn(%s)" % (cmd))
        pipe = subprocess.Popen(cmd, env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT,
                                bufsize=1, close_fds=True, shell=False)
        pipe.stdin.close()
        output = pipe.stdout.readline()
        flines = 0
        while output:
            self.logfile.write(output)
            if _pass_filter(output):
                if flines >= 50:
                    sys.stdout.write("\n")
                sys.stdout.write(output)
                flines = 0
            else:
                flines = flines + 1
                if flines % 50 == 0:
                    sys.stdout.write('.')
            output = pipe.stdout.readline()
        pipe.wait()
        return pipe.returncode



class LogAction(ListAction):

    def __init__(self, actionlist):
        ListAction.__init__(self, actionlist)

    def __call__(self, target, source, env, **kw):
        # Replace the SPAWN variable with our own instance of _SpawnerLogger.
        spawner = _SpawnerLogger()
        spawner.open(str(env['TESTING_LOGFILE']))
        spawnsave = env['SPAWN']
        env['SPAWN'] = spawner.spawn
        try:
            status = ListAction.__call__(self, target, source, env, **kw)
        finally:
            spawner.close()
            env['SPAWN'] = spawnsave
        return status


def _TestLog(env, alias, sources, actions):
    "Wrap a pseudo-builder test with an output filter."
    if not alias:
        alias = 'xtest'
    # Set the logfile in a cloned environment, so this pseudo-builder does
    # not interfere with the log settings for another TestLog
    # pseudo-builder.
    logfile = env.File(alias + '.log')
    env = env.Clone(TESTING_LOGFILE=logfile)
    # Use the Action() factory to create the action instance, which may
    # itself be a ListAction, then wrap the action/s in a LogAction
    # instance.
    xtest = env.Command([alias, logfile], sources, LogAction([Action(actions)]))
    env.AlwaysBuild(xtest)
    defenv = DefaultEnvironment()
    defenv.Clean([xtest], xtest)
    # If cleaning, then we want test targets to be cleaned by default.
    if env.GetOption('clean'):
        env.Default(xtest)
    return xtest


def _DefaultTest(env, xtest):
    "Like Default(), except target is added to the default test alias 'test'."
    defenv = DefaultEnvironment()
    defenv.Alias('test', xtest)
    defenv.Clean(['test'], xtest)
    # If cleaning, then we want test targets to be cleaned by default.
    if env.GetOption('clean'):
        env.Default(xtest)
    return xtest


def generate(env):
    env.AddMethod(_TestLog, "TestLog")
    env.AddMethod(_DefaultTest, "DefaultTest")


def exists(env):
    return True
