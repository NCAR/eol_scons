# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
@file examples/logx/tool_logx_example.py

This is an example of a SConscript file embedded in a source tree.  It
contains the SCons Environment calls which assemble the builders and
dependencies, but it also contains the logx() tool function for adding
the logx library and dependencies to other Environment instances.
"""

tools = ['doxygen', 'log4cpp']
env = Environment(tools=['default'] + tools)

logxDir = Dir('.').abspath

def logx_example(env):
    env.Append(LIBS=[env.GetGlobalTarget('liblogx'),])
    env.AppendUnique(CPPPATH = logxDir)
    env.AppendDoxref(doxref[0])
    env.Require(tools)

Export('logx_example')

sources = Split("""
 Logging.cc
 LogLayout.cc
 LogAppender.cc
 RecentHistoryAppender.cc
 system_error.cc
""")
headers = Split("""
 CaptureStream.h
 EventSource.h
 Logging.h
 Checks.h
 RecentHistoryAppender.h
 system_error.h
""")

objects = env.SharedObject(sources)
lib = env.Library('logx', objects)
Default(lib)

env.InstallLibrary(lib)
env.InstallHeaders('logx', headers)

env['DOXYFILE_DICT'].update({ "PROJECT_NAME" : "logx library" })
doxref = env.Apidocs(sources + headers + ["private/LogLayout.h"])

