# Run this test like so:
#
# env PYTHONPATH=/usr/lib/scons py.test -v valgrind.py

import io
import eol_scons.tools.valgrind as vg

_valgrind_example = """\
11111
22222 Random leader text here...
33333
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


def test_parsevalgrind():
    log = io.StringIO(_valgrind_example)
    results = vg._parseValgrindOutput(log)
    assert results['dlost'] == 408
    assert results['ilost'] == 3854
    assert results['plost'] == 191841
    assert results['nerrors'] == 16
    assert results['tool'] == 'Memcheck'
    log = io.StringIO(_helgrind_example)
    results = vg._parseValgrindOutput(log)
    assert results['tool'] == 'Helgrind'
    assert 'dlost' not in results
    assert results['nerrors'] == 17
