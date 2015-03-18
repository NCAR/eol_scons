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
import re

import SCons.Script
from SCons.Script import DefaultEnvironment
from SCons.Action import Action
from SCons.Action import ListAction

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


class ImageComparisonPage(object):

    """
    Encapsulate the information and settings needed to generate a HTML page
    for comparing images, such as comparing expected plots against current
    plots.  Each image comparison is a pair of images, one 'before'
    (expected) and one 'after' (latest), each image with its own url
    relative to the page being generated, and with a title for the
    comparison.  These tuples are added to this object with the
    addComparison() method, before generating the page with generatePage().
    """

    _default_header = """<html>
<head>
<title>%(pagetitle)s</title>
<style media="screen" type="text/css">
%(css)s
</style>
</head>
<body>
<table border>
"""

    _default_css = """
table { border-width: 4 }
body { margin: 0 0 0 0 ; padding: 0 0 0 0 }
p { margin: 0 0 0 0 ; padding: 0 0 0 0 }
h1, h2, h3, h4, h5,h6 { margin: 0 0 0 0 ; padding: 0 0 0 0 ; 
			text-align: center }
ul { margin-top: 2px; margin-bottom: 2px }

.titlebox { border: thick groove blue; padding: 5px 5px 5px 5px }
"""

    _default_rowtemplate = """
<tr>
<td colspan='2'><h2>%(title)s</h2></td>
</tr>
<tr>
<td>
<h2>%(before)s</h2><br>
<a href='%(before)s'><img %(width)s %(height)s src='%(srcbefore)s'></a>
</td>
<td>
<h2>%(after)s</h2><br>
<a href='%(after)s'><img %(width)s %(height)s src='%(srcafter)s'></a>
</td>
</tr>
"""

    def __init__(self):
        self.pagetitle = None
        self.images = []
        self.header = self._default_header
        self.rowtemplate = self._default_rowtemplate
        self.css = self._default_css
        # Create the img element with these width and height attributes,
        # or omit the property if it is None.
        self.image_width = 400
        self.image_height = 300

    def setPageTitle(self, pagetitle):
        self.pagetitle = pagetitle

    def addComparison(self, before, after, title=None):
        # If title is None then a default is generated from the image names.
        image = {}
        image['before'] = before
        image['after'] = after
        image['srcbefore'] = before
        image['srcafter'] = after
        if title is None:
            title = "Comparison of %s and %s" % (before, after)
        image['title'] = title
        self.images.append(image)

    def writePage(self, page):
        if not self.pagetitle:
            self.pagetitle = page
        out = open(page, 'wb')
        out.write(self.header % self.__dict__)
        for image in self.images:
            props = {}
            props.update(image)
            if self.image_width is None:
                props['width'] = ""
            else:
                props['width'] = "width=%s" % (self.image_width)
            if self.image_height is None:
                props['height'] = ""
            else:
                props['height'] = "height=%s" % (self.image_height)
            out.write(self.rowtemplate % props)
        out.write("</table>\n")
        out.close()
        return None

    def builder(self, target, source, env):
        pagepath = target[0].get_path()
        return self.writePage(pagepath)

    def build(self, env, pagepath):
        """
        "Instantiate a builder for the given page, with the current
        images as the sources.
        """
        page = env.Command(pagepath, [env.Value(self)] +
                           [image['before'] for image in self.images] +
                           [image['after'] for image in self.images],
                           self.builder)
        return page


def _get_instance(env):
    page = env.get('IMAGE_COMPARISON_PAGE')
    if not page:
        page = ImageComparisonPage()
        env['IMAGE_COMPARISON_PAGE'] = page
    return page


def generate(env):
    env.AddMethod(_TestLog, "TestLog")
    env.AddMethod(_TestRun, "TestRun")
    env.AddMethod(_DefaultTest, "DefaultTest")
    env.AddMethod(_get_instance, "ImageComparisonPage")


def exists(env):
    return True


def gtest(env):
    env.Append(LIBS=['gtest'])

def gtest_main(env):
    env.Append(LIBS=['gtest_main'])
    env.Require('gtest')

SCons.Script.Export('gtest')
SCons.Script.Export('gtest_main')
