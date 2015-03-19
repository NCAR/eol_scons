"""SCons tool to run test programs and to log or filter the output.

All test pseudo-builder methods take a name for the test (the alias) and
the list of actions to execute to run that test, typically a shell command.
The default test alias is 'xtest', relative to the Environment's directory.
There is a global default test alias called 'test', and test targets can be
added to this alias with the DefaultTest() method.

The test methods try to provide two aliases: one is an unqualified name
that may be shared across the whole source tree, such as 'xtest', and one
that is qualified with the source directory, such as
'datastore/tests/xtest'.

Additionally, test output can be logged to a file, named <alias>.log in the
Environment directory, and the output which gets shown on stdout can be
filtered.  This allows the stdout output to be more concise while
preserving all the debugging output in case it is needed for closer
inspection.  The TestRun() builder runs a test without logging the output.

The eol_scons package always adds a Test() pseudo-builder by default.  That
method uses the 'xtest' and 'test' aliases by default, so it cannot be used
to create other non-default test commands used during development.  Here is
the equivalent of Test() using the methods in this tool:

  xtest = env.DefaultTest(env.TestRun('xtest', test_program_targets, actions))

If the test is only meant to run when specified explicitly, then provide a
unique alias:

  qtest = env.TestLog('qtest', test_program_targets, actions)

Finally, there is a list of regular expression patterns for lines which
should be allowed to pass to stdout from the test output.  This can be
extended as needed.  Someday it might be useful to parameterize it.  Also
it would be useful to be able to delegate the filtering.  For example, a
valgrind output parser could extract information from the output and pass
through only the errors.  Then the filters could be broken down into types
of output, such as boost tests, logx Checker tests, and valgrind checks.

All tests are cleaned by default.  In other words, when no targets are
given on the command line with the clean option, the test targets are added
to the default targets so they will be cleaned.  Run 'scons -c' to clean
the default targets along with any test programs and their output.  Running
'scons -u -c' in a subdirectory only cleans targets, whether tests or
otherwise, beneath that directory.  To clean all the targets within a whole
source tree, whether tests or not, it is necesary to specify the top
directory as the target:

 scons -c .

This module defines extra test-related "sub-tools" which seem too small to
warrant their own module.  The 'gtest' tool adds the gtest library for
building google-test programs, while the 'gtest_main' tool also links
against the 'gtest_main' library for programs which do not provide their
own main().  These tools are not defined until this tool has been loaded,
so the testing tool must always be required first:

env = Environment(tools=['default', 'testing', 'gtest'])

"""

import subprocess
import io
import sys
import os
import re
import difflib

import SCons
import SCons.Script
from SCons.Script import DefaultEnvironment
from SCons.Action import Action
from SCons.Action import ListAction
from SCons.Script import Builder

_echo_only = False

_rxpatterns = [ r'^\d+ checks\.',
                r'^\d+ failures\.',
                r'^Running \d+ test cases\.\.\.',
                r'^.+\(N\): .* passed',
                r'^.+\(N\): .* FAIL',
                r'^\*\*\* No errors detected',
                r'^Leaving test case.*',
                r'^Entering test case.*',
                r'^\*\*\* Skipping test.*'
                ]


class _SpawnerLogger:

    def __init__(self):
        self.logpath = None
        self.logfile = None
        self._rxpass = None
        self.setPassingPatterns(_rxpatterns)

    def _pass_filter(self, line):
        if self._rxpass is None:
            return True
        for rx in self._rxpass:
            if rx.search(line):
                return True
        return False

    def setPassingPatterns(self, rxpatterns):
        """
        Set line patterns which pass through the output filter.  If
        rxpatterns is None, no lines will be filtered out.
        """
        self._rxpass = None
        if rxpatterns:
            self._rxpass = [ re.compile(rx) for rx in rxpatterns ]

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
        if _echo_only:
            cmd = [sh, '-c', 'echo "*** Skipping test: %s"' % (" ".join(args))]
        pipe = subprocess.Popen(cmd, env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT,
                                bufsize=1, close_fds=True, shell=False)
        pipe.stdin.close()
        output = pipe.stdout.readline()
        flines = 0
        while output:
            if self.logfile:
                self.logfile.write(output)
            if self._pass_filter(output):
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
        if flines >= 50:
            sys.stdout.write("\n")
        return pipe.returncode


class LogAction(ListAction):

    def __init__(self, actionlist, logpath=None, patterns=_rxpatterns):
        ListAction.__init__(self, actionlist)
        self.logpath = logpath
        self.patterns = patterns
        # Disable filtering when log file is disabled.
        if not logpath:
            self.patterns = None

    def __call__(self, target, source, env, **kw):
        # Replace the SPAWN variable with our own instance of _SpawnerLogger.
        spawner = _SpawnerLogger()
        if self.logpath:
            spawner.open(self.logpath)
        spawner.setPassingPatterns(self.patterns)
        spawnsave = env['SPAWN']
        env['SPAWN'] = spawner.spawn
        try:
            status = ListAction.__call__(self, target, source, env, **kw)
        finally:
            spawner.close()
            env['SPAWN'] = spawnsave
        return status


def _test_builder(env, alias, sources, actions, logfile=None):
    if not alias:
        alias = 'xtest'
    targets = [ env.File(alias) ]

    # Use the Action() factory to create the action instance, which may
    # itself be a ListAction, then wrap the action/s in a LogAction
    # instance.  If the logfile is disabled, then there are no filter
    # patterns either.
    if logfile:
        targets.append(logfile)
    logaction = LogAction([Action(actions)], logfile)

    xtest = env.Command(targets, sources, logaction)

    # The test should always run when given as a target, even if the log
    # file already exists.  This may also be required for the virtual file
    # target, since it is required when using an Alias() builder.
    env.AlwaysBuild(xtest)

    # The alias target is a file in the virtual filesystem, but it will
    # never exist and does not need to be cleaned.  Using an actual Alias()
    # builder instead of Command() does not work, because there is no way
    # to setup the alias target to be cleaned by default.  Adding an alias
    # target to Default() does not cause that target's dependencies to be
    # cleaned as it does for an actual File node.  However, setting NoClean
    # for the virtual file also prevents the log file from being cleaned,
    # so we'll just have to live with scons' attempts to remove the virtual
    # target.
    #
    # env.NoClean(xtest[0])

    # This sets up an alias as a single word name, rather than the name
    # above which is qualified by the source directory.
    env.Alias(alias, xtest)

    # As I read the code in SCons.Script.Main.CleanTask, the extra
    # CleanTargets are supposed to be files to be explicitly removed,
    # rather than target nodes which should be recursively cleaned.  So
    # this doesn't do what I think I wanted it to do, so leave it out.
    #
    # env.Clean(clean_targets, xtest)

    # If cleaning, then we want test targets to be cleaned by default.  For
    # some unknown reason, setting only the log file target or the alias
    # target (ie, xtest) as the default does not clean the test targets,
    # but it does work to add all the aliases as default targets.
    if env.GetOption('clean'):
        env.Default(xtest)

    return xtest


def _TestLog(env, alias, sources, actions):
    "Wrap a pseudo-builder test with an output filter."
    if not alias:
        alias = 'xtest'
    logfile = env.File(alias + '.log').get_abspath()
    return _test_builder(env, alias, sources, actions, logfile)


def _TestRun(env, alias, sources, actions):
    "Run a test without piping the output into a log file."
    return _test_builder(env, alias, sources, actions)


def _DefaultTest(env, xtest):
    "Add target to the default test alias 'test'."
    alias = env.Alias('test', xtest)
    return xtest


def _get_page_instance(env):
    from imagecomparisonpage import ImageComparisonPage
    page = env.get('IMAGE_COMPARISON_PAGE')
    if not page:
        page = ImageComparisonPage()
        env['IMAGE_COMPARISON_PAGE'] = page
    return page

def _sync_cache(target, source, env):
    dfcache = env.DataFileCache()
    if dfcache.sync():
        return None
    raise SCons.Errors.StopError("datasync failed.")

def _get_cache_instance(env):
    import datafilecache
    import os
    dfcache = env.get('DATA_FILE_CACHE')
    if not dfcache:
        path = str(env.Dir('#/DataCache'))
        if not os.path.isdir(path):
            os.makedirs(path)
        dfcache = datafilecache.DataFileCache(path)
        env['DATA_FILE_CACHE'] = dfcache
        env.Command('datasync', None, _sync_cache)
        # No point downloading anything for clean and help options.
        if env.GetOption('clean') or env.GetOption('help'):
            dfcache.enableDownload(False)
    return dfcache

def diff_files(target, source, env):
    diffs = None
    p1 = source[0].get_abspath()
    p2 = source[1].get_abspath()
    f1 = open(p1, "rb")
    f2 = open(p2, "rb")
    diff = difflib.unified_diff(f1.readlines(), f2.readlines())
    f1.close()
    f2.close()
    diffs = [line for line in diff]
    if diffs:
        print("".join(diffs))
        return str("Differences found between " + 
                   str(source[0]) + " and " + str(source[1]))
    return None

def diff_emitter(target, source, env):
    "Generate a target if not given."
    #print("target:%s, source:%s" % (",".join([str(n) for n in target]),
    # ",".join([str(n) for n in source])))
    # SCons creates a default target when only sources are passed to the
    # Builder.  I think the algorithm truncates any suffix from the first
    # source file and appends the builder suffix, which in this case is
    # None.  So to determine if the target is a default which should be
    # replaced, look for that in the target.
    (base, ext) = os.path.splitext(str(source[0]))
    if str(target[0]) == base:
        diff = "diff-" + str(source[0]) + "-" + str(source[1])
        diff = diff.replace('/', '-')
        print("Creating default diff target: %s" % (diff))
        target = [diff]
    return target, source

diff_builder = Builder(action=[diff_files], emitter=diff_emitter)


def generate(env):
    env.Append(BUILDERS = {'Diff':diff_builder})
    env.AddMethod(_TestLog, "TestLog")
    env.AddMethod(_TestRun, "TestRun")
    env.AddMethod(_DefaultTest, "DefaultTest")
    env.AddMethod(_get_page_instance, "ImageComparisonPage")
    env.AddMethod(_get_cache_instance, "DataFileCache")

def exists(env):
    return True


def gtest(env):
    env.Append(LIBS=['gtest'])

def gtest_main(env):
    env.Append(LIBS=['gtest_main'])
    env.Require('gtest')

SCons.Script.Export('gtest')
SCons.Script.Export('gtest_main')
