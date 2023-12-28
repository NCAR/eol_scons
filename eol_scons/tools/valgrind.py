"""
Simple scons tool to test programs with valgrind tools.

This tool finds a valgrind executable and sets the VALGRIND_PATH
construction variable accordingly.  The value will also be available in the
runtime environment, such as for test scripts executed by scons.

By default VALGRIND_COMMAND is the concatenation of VALGRIND_PATH and
VALGRIND_OPTIONS, but it can be overridden in the usual way with keyword
arguments to scons calls.

The Valgrind() pseudo-builder works like a Command() builder.  The first
argument is the targets, then sources, then actions.  The pseudo-builder
can create one of two builders.  One builder is created with Command(),
except $VALGRIND_COMMAND is replaced with an empty string.  The other
builder runs the same actions, without replacing VALGRIND_COMMAND, but it
filters the output to a log file and adds a ValgrindLog() builder to that.
The default builder is selected by setting the VALGRIND_DEFAULT keyword to
'on' or 'off', but it is off by default.  Then the valgrind command can be
enabled or disabled for a particular scons run by setting the 'valgrind'
option to 'on' or 'off'.

If a suppressions file is detected as one of the source files, then that
file is added automatically as an argument to the valgrind command, and it
is removed from the sources for the plain Command() builder.

The VALGRIND_COMMAND variable must appear somewhere in the actions to run
valgrind, for example:

    sfile = env.File("vg.suppressions.txt")
    memcheck = env.Valgrind('memcheck', [test_program, sfile],
                            "cd ${SOURCE.dir} && "
                            "${VALGRIND_COMMAND} ./${SOURCE.file} ${GTESTS}")

The above target can be triggered by calling `scons memcheck`.  It will run
the test program directly and not under valgrind, since VALGRIND_DEFAULT
was not specified.  The same builder can be created with the code below,
but valgrind will run by default:

    sfile = env.File("vg.suppressions.txt")
    memcheck = env.Valgrind('memcheck', [test_program, sfile],
                            "cd ${SOURCE.dir} && "
                            "${VALGRIND_COMMAND} ./${SOURCE.file} ${GTESTS}",
                            VALGRIND_DEFAULT='on')

Either of the above two targets can be run with valgrind by explicitly
forcing it with a command-line setting:

    scons -u memcheck valgrind=on

The ValgrindLog() builder parses the output from valgrind and fails the
build if there are excessive errors.  It can be used separately to test a
valgrind log file rather than through the Valgrind() method.
"""

import os
import re
import SCons
from SCons.Builder import Builder
from SCons.Action import Action
from SCons.Variables import EnumVariable


class ValgrindWarning(SCons.Warnings.WarningOnByDefault):
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
    extra_paths = ['/usr/bin']
    if 'OPT_PREFIX' in env:
        extra_paths.append("%s/bin" % env['OPT_PREFIX'])
    opts = ['el4', 'el3', 'ws3', 'fc4', 'fc3', 'fc2']
    extra_paths.extend(["/net/opt_lnx/local_%s/bin" % o for o in opts])
    return env.WhereIs('valgrind', extra_paths)


def getValgrindPath(env):
    valgrind = findValgrind(env)
    if not valgrind:
        valgrind = "valgrind"
    return valgrind


def _parseValgrindOutput(log):
    # Parse valgrind error summary lines
    rxmap = {'nerrors': re.compile(r"ERROR SUMMARY: *([\d,]+) *"),
             'dlost': re.compile(r"definitely lost: *([\d,]+) bytes"),
             'plost': re.compile(r"possibly lost: *([\d,]+) bytes"),
             'ilost': re.compile(r"indirectly lost: *([\d,]+) bytes")}
    rxnoleaks = re.compile(r"no leaks are possible")
    results = {}
    # Look for the tool in the first 10 lines of the file.  Limit the line
    # lengths in case this is a binary file with no newlines.  If the
    # valgrind tool line is not found in the first 10 lines or 2560 bytes,
    # then it must not be a valgrind log file.
    rxtool = re.compile(r"==\d+== (Memcheck|Helgrind), "
                        r"a (memory|thread) error detector")
    match = None
    line = log.readline(256)
    lineno = 0
    while line and not match and lineno < 10:
        lineno += 1
        match = rxtool.search(line)
        line = log.readline(256)

    if not match:
        return None
    results['tool'] = match.group(1)
    while line:
        if rxnoleaks.search(line):
            results['dlost'] = 0
            results['plost'] = 0
            results['ilost'] = 0
            print("valgrind: %s" % line)
        for vname, rx in rxmap.items():
            match = rx.search(line)
            if match:
                print("valgrind: %s in %s" % (vname, line))
                results[vname] = int(match.group(1).replace(',', ''))
        line = log.readline()

    return results


def ValgrindLog_emit(target, source, env):
    # If the target is a default, generate a target from the source.
    if target and str(target[0]) == str(source[0]):
        target = [str(source[0]) + '-vglog']
    # env.AlwaysBuild(source)
    return target, source


def ValgrindLog(target, source, env):
    # Perhaps Node.get_text_contents() could be used here, but valgrind logs
    # can be very very large, so stick with the file stream.
    results = None
    for s in source:
        log = open(str(s), "r")
        results = _parseValgrindOutput(log)
        log.close()
        if results:
            break
    if not results:
        msg = "No valgrind log file found from memcheck or helgrind tool."
        raise SCons.Errors.StopError(msg)

    maxleaked = env.get('VALGRIND_LEAK_THRESHOLD', 0)
    maxerrors = env.get('VALGRIND_ERROR_THRESHOLD', 0)
    if results['nerrors'] > maxerrors:
        return "ValgrindLog: Too many errors (%d)" % (results['nerrors'])
    if results['tool'] == 'Memcheck' and results['dlost'] > maxleaked:
        return "ValgrindLog: Too many bytes leaked: %d" % (results['dlost'])
    return None


def Valgrind(env, targets, sources, actions, **kw):
    """
    Use a Command builder to create the targets, but also add a valgrind
    log file and parse it.  If valgrind is explicitly off, then just return
    a Command builder with the VALGRIND_COMMAND replaced with an empty
    string.  Pass VALGRIND_DEFAULT keyword as False to disable valgrind by
    default, meaning valgrind will only run for these targets when the
    'valgrind' option is explicitly set to 'on'.
    """
    _variables.Update(env)
    valgrind = env.get('valgrind', 'default')
    env.LogDebug("valgrind=%s" % (valgrind))
    vgcmd = kw.get('VALGRIND_COMMAND')
    sources = env.Flatten(sources)
    targets = env.Flatten([targets])
    suppfile = [src for src in sources
                if str(src).endswith("vg.suppressions.txt")]
    suppressions = ""
    if suppfile:
        suppfile = env.File(suppfile[0])
        suppressions = " --suppressions=%s" % (suppfile.get_abspath())

    # The only way to trigger the valgrind build is if valgrind is on
    # or default and the builder's default is on.
    if bool(valgrind == 'off' or
            kw.get('VALGRIND_DEFAULT') == 'off' and valgrind == 'default'):
        env.LogDebug("Creating builder for %s, "
                     "valgrind=off" % (str(targets[0])))
        kw['VALGRIND_COMMAND'] = ''
        output = env.Command(targets, sources, actions, **kw)
    else:
        env.LogDebug("Creating builder for %s, "
                     "valgrind=on" % (str(targets[0])))
        # Save off the valgrind output into a log file, without filtering
        # anything, then parse the valgrind output.
        logfile = str(targets[0])+'.vg.log'
        logfile = kw.get('VALGRIND_LOG', logfile)
        logfile = env.File(logfile)
        logaction = env.LogAction([Action(actions)], logfile.get_abspath())
        if not vgcmd:
            vgcmd = env.get('VALGRIND_COMMAND')
        kw['VALGRIND_COMMAND'] = vgcmd + suppressions
        targets.append(logfile)
        # First run the command under valgrind, then analyze the log file,
        # and the targets of both builders are returned as the output
        # nodes for this pseudo-builder.
        output = env.Command(targets, sources, logaction, **kw)
        output.extend(env.ValgrindLog(str(logfile)+"-analyze", logfile))

    return output


_variables = None


def _setup_variables(env):
    global _variables
    if not _variables:
        _variables = env.GlobalVariables()
        _variables.Add(EnumVariable('valgrind',
                                    "Force valgrind analysis on or off.",
                                    'default',
                                    allowed_values=('default', 'on', 'off'),
                                    ignorecase=2))
    _variables.Update(env)


def generate(env):
    # Need LogAction
    _setup_variables(env)
    env.Require('testing')
    valgrind = getValgrindPath(env)
    env['ENV']['VALGRIND_PATH'] = valgrind
    env['VALGRIND_PATH'] = valgrind
    if 'VALGRIND_COMMAND' not in env:
        env['VALGRIND_COMMAND'] = "${VALGRIND_PATH} ${VALGRIND_OPTIONS}"
    # These need to propagate for valgrind, because it uses them to generate
    # the pipe filenames for the embedded gdb server, and they must match the
    # filenames that the remote gdb client will generate with the 'target
    # remote' command.
    env['ENV']['HOSTNAME'] = os.getenv('HOSTNAME')
    env['ENV']['USER'] = os.getenv('USER')
    env.Append(BUILDERS={'ValgrindLog': Builder(action=ValgrindLog,
                                                emitter=ValgrindLog_emit)})
    env.AddMethod(Valgrind)


def exists(env):
    if not findValgrind(env):
        SCons.Warnings.warn(ValgrindWarning,
                            "Could not find valgrind program.")
        return False
    return True
