# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
This SCons tool took some inspiration from the xvfbwrapper package
(https://pypi.python.org/pypi/xvfbwrapper/) to manage and share a
background Xvfb instance for running programs (like tests especially) which
require an X server.  Unlike xvfbwrapper, this Xvfb class uses the -displayfd
option to read the display number back from the Xvfb process.

The tool adds two python actions to the environment:

xvfb_start

  Creates an Xvfb instance, starts it, and propagates the DISPLAY
  environment setting.

xvfb_stop

  Kills any existing Xvfb instance.

The Xvfb instance for an Environment can be retrieved with the Xvfb()
method.

The usual usage is to insert the start and stop actions in the action list
for a builder around any process which must connect to an X server.  The
technique is similar that used for the postgres_testdb tool.
"""

import os
import SCons
from eol_scons.xvfb import Xvfb

def _get_instance(env):
    xvfb = env.get('XVFB_INSTANCE')
    if not xvfb:
        xvfb = Xvfb()
        env['XVFB_INSTANCE'] = xvfb
    return xvfb


def _xvfb_stop(target, source, env):
    xvfb = env.Xvfb()
    xvfb.stop()
    env['DISPLAY'] = os.environ.get('DISPLAY')
    print("Xvfb stopped.")


def _xvfb_start(target, source, env):
    xvfb = env.Xvfb()
    if xvfb.start() is None:
        raise SCons.Errors.StopError("Error starting Xvfb.")
    print("Xvfb started on display %s" % (os.environ['DISPLAY']))
    env['ENV']['DISPLAY'] = os.environ['DISPLAY']
    env['DISPLAY'] = os.environ['DISPLAY']

def generate(env):
    env.AddMethod(_get_instance, "Xvfb")
    env.xvfb_start = _xvfb_start
    env.xvfb_stop = _xvfb_stop


def exists(env):
    return True



