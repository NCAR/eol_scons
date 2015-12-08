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


def _parseValgrindOutput(log):
    # Parse valgrind error summary lines

    rxmap = { 'nerrors' : re.compile(r"ERROR SUMMARY: *([\d,]+) *"),
              'dlost' : re.compile(r"definitely lost: *([\d,]+) bytes"),
              'plost' : re.compile(r"possibly lost: *([\d,]+) bytes"),
              'ilost' : re.compile(r"indirectly lost: *([\d,]+) bytes") }
    results = {}
    l = log.readline()
    # The first line gives the tool
    match = re.search(r"==\d+== (Memcheck|Helgrind), "
                      r"a (memory|thread) error detector", l)
    if not match:
        msg = "not a valgrind log file from memcheck or helgrind tool"
        raise SCons.Errors.StopError, msg
    results['tool'] = match.group(1)
    while l:
        l = l.strip()
        for vname, rx in rxmap.items():
            match = rx.search(l)
            if match:
                print("found %s in %s" % (vname, l))
                results[vname] = int(match.group(1).replace(',',''))
        l = log.readline()

    return results
        

_valgrind_example = """\
==9158== Memcheck, a memory error detector
==9158== Copyright (C) 2002-2013, and GNU GPL'd, by Julian Seward et al.
==9158== Using Valgrind-3.9.0 and LibVEX; rerun with -h for copyright info
==9158== Command: tcore
==9158== 
...
==9158== 
==9158== HEAP SUMMARY:
==9158==     in use at exit: 72 bytes in 4 blocks
==9158==   total heap usage: 1,598 allocs, 1,594 frees, 123,497 bytes allocated
==9158== 
==19284== LEAK SUMMARY:
==19284==    definitely lost: 408 bytes in 1 blocks
==19284==    indirectly lost: 3,854 bytes in 36 blocks
==19284==      possibly lost: 191,841 bytes in 2,586 blocks
==19284==    still reachable: 74,503,382 bytes in 9,568 blocks
==19284==         suppressed: 102,158 bytes in 1,871 blocks
==19284== Reachable blocks (those to which a pointer was found) are not shown.
==19284== To see them, rerun with: --leak-check=full --show-reachable=yes
==19284== 
==19284== For counts of detected and suppressed errors, rerun with: -v
==19284== ERROR SUMMARY: 16 errors from 5 contexts (suppressed: 4 from 4)
"""

_helgrind_example = """\
==9080== Helgrind, a thread error detector
==9080== Copyright (C) 2007-2013, and GNU GPL'd, by OpenWorks LLP et al.
==9080== Using Valgrind-3.9.0 and LibVEX; rerun with -h for copyright info
==9080== Command: tcore
==9080== 
Running 19 test cases...
received signal Interrupt(2), si_signo=2, si_errno=0, si_code=0

*** No errors detected
==9080== 
==9080== For counts of detected and suppressed errors, rerun with: -v
==9080== Use --history-level=approx or =none to gain increased speed, at
==9080== the cost of reduced accuracy of conflicting-access information
==20791== ERROR SUMMARY: 17 errors from 17 contexts (suppressed: 143 from 117)
"""

# Run this test like so:
#
# env PYTHONPATH=/usr/lib/scons py.test -v valgrind.py

def test_parsevalgrind():
    import io
    log = io.StringIO(_valgrind_example.decode('ascii'))
    results = _parseValgrindOutput(log)
    assert results['dlost'] == 408
    assert results['ilost'] == 3854
    assert results['plost'] == 191841
    assert results['nerrors'] == 16
    assert results['tool'] == 'Memcheck'
    log = io.StringIO(_helgrind_example.decode('ascii'))
    results = _parseValgrindOutput(log)
    assert results['tool'] == 'Helgrind'
    assert results.has_key('dlost') == False
    assert results['nerrors'] == 17


def ValgrindLog_emit(source, target, env):
    # If the target is a default, generate a target from the source.
    if target and str(target[0]) == str(source[0]):
        target = [str(source[0]) + '-vglog']
    return target, source


def ValgrindLog(target, source, env):
    # Perhaps Node.get_contents() could be used here, but valgrind logs
    # can be very very large, so stick with the file stream.
    log = open(str(source[0]), "r")
    results = _parseValgrindOutput(log)
    log.close()
    maxleaked = env.get('VALGRIND_LEAK_THRESHOLD', 0)
    maxerrors = env.get('VALGRIND_ERROR_THRESHOLD', 0)
    if results['nerrors'] > maxerrors:
        return "ValgrindLog: Too many errors (%d)" % (results['nerrors'])
    if results['tool'] == 'Memcheck' and results['dlost'] > maxleaked:
        return "ValgrindLog: Too many bytes leaked: %d" % (results['dlost'])
    return None


def generate(env):
    valgrind = getValgrindPath(env)
    env['ENV']['VALGRIND_PATH'] = valgrind
    env['VALGRIND_PATH'] = valgrind
    env.Append(BUILDERS = {'ValgrindLog' : Builder(action = ValgrindLog,
                                                   emitter = ValgrindLog_emit) })


def exists(env):
    if not findValgrind(env):
        SCons.Warnings.warn(ValgrindWarning,
                            "Could not find valgrind program.")
        return False
    return True
