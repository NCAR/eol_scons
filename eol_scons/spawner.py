"""
Module for SpawnerLogger class.
"""

import subprocess
import sys
import re

echo_only = False

_rxpatterns = [r'^\d+ checks\.',
               r'^\d+ failures\.',
               r'^Running \d+ test cases\.\.\.',
               r'^.+\(N\): .* passed',
               r'^.+\(N\): .* FAIL',
               r'^\*\*\* No errors detected',
               r'^Leaving test case.*',
               r'^Entering test case.*',
               r'^\*\*\* Skipping test.*'
               ]


class SpawnerLogger:
    """
    Spawn a subprocess and allow output to be logged and filtered.  A
    SpawnerLogger can be assigned to the SCons SPAWN environment variable to
    affect output from all build subprocesses, or it can be limited to
    specific actions using the LogAction class (in the _testing_ tool).

    The idea is to allow the build output to the console to be trimmed while
    preserving a full unfiltered copy of the output in a log file.  The
    original use case is for voluminous test output, where usually just the
    results of the tests are needed, but a log file can be helpful if the test
    output needs to be investigated.

    If an instance is used to override the SPAWN variable in a SCons
    environment, then the log file (when specified) is opened and closed
    implicitly whenever the instance is called to spawn a process.  If the
    same instance (with the same log file path) spawns multiple processes
    (such as when the build must run multiple commands), then each subsequent
    spawn appends to the existing log file.

    If a log file is not needed, then a SpawnerLogger can be used just to
    filter the output of any processes spawned by it, but the filtered output
    is not preserved anywhere.
    """

    def __init__(self, logpath=None, rxpatterns=None):
        """
        Create a spawner which will write all output to @p logpath and only
        write output lines to stdout which match one of @p rxpatterns.  If @p
        logpath is None, then no log file will be written.  If @p rxpatterns
        is None, then a default is used.   Pass rxpatterns=[] to suppress all
        output and rxpatterns=[r'.*'] to write all output.
        """
        self.logpath = logpath
        self.logfile = None
        # After the first process has been spawned, all subsequent spawns will
        # append to the log file.  Thus all actions handled by this spawner
        # within the same scons run will accumulate their output into the same
        # log file.
        self.appending = False
        self._rxpass = None
        self.setPassingPatterns(rxpatterns)

    def _pass_filter(self, line):
        for rx in self._rxpass:
            if rx.search(line):
                return True
        return False

    def setPassingPatterns(self, rxpatterns=None):
        """
        Set line patterns which pass through the output filter.  If rxpatterns
        is None, set a default list of patterns.
        """
        if rxpatterns is None:
            rxpatterns = _rxpatterns
        self._rxpass = [re.compile(rx) for rx in rxpatterns]

    def open(self):
        "Open the log file if not already open and log path is specified."
        if not self.logpath or self.logfile:
            return
        self.logfile = open(self.logpath, "w" if not self.appending else "a")
        if not self.appending:
            print("Logging to '%s' while filtering output." % (self.logpath))
        self.appending = True

    def close(self):
        if self.logfile:
            self.logfile.close()
            self.logfile = None

    def spawn(self, sh, escape, cmd, args, env):
        """
        Spawn the process and pipe the output.

        The output is written to the log file, if any, and any lines which
        pass the filter are written to stdout.  The log file is opened here
        and closed when the process completes.  The log file is truncated on
        the first open, then all subsequent spawns append to it.  So within
        the same SCons build step it is possible to accumulate the output of
        multiple processes (actions) in the same log file.
        """
        self.open()
        try:
            return self._spawn(sh, escape, cmd, args, env)
        finally:
            self.close()

    def _spawn(self, sh, escape, cmd, args, env):
        cmd = [sh, '-c', ' '.join(args)]
        if echo_only:
            cmd = [sh, '-c', 'echo "*** Skipping test: %s"' % (" ".join(args))]
        pipe = subprocess.Popen(cmd, env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True,
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

    def __call__(self, sh, escape, cmd, args, env):
        return self.spawn(sh, escape, cmd, args, env)
