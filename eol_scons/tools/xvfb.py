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

import SCons
import os
import subprocess as sp
import select


class Xvfb(object):

    """
    Wrap a Xvfb subprocess and provide methods to start and stop it.
    """

    def __init__(self):
        self.saved_display = None
        self.display = None
        self.proc = None
        self.dpipe = None
        self.displayfd = None

    def start(self):
        dpipe = os.pipe()
        cmd = ['Xvfb', '-displayfd', str(dpipe[1])]
        # The -displayfd option causes Xvfb to look for an available
        # display number, but it writes error messages for each failed
        # attempt to open a display.  It would be nice to create a pipe for
        # stderr to filter out the error messages, but that gets
        # complicated because we would need to keep reading from that pipe
        # after starting Xvfb or else risk blocking the Xvfb process.
        # Likely there would not be any output once the display number is
        # written back over the pipe, but that is not guaranteed.  Instead
        # it works to use the shell to pipe and filter with grep.
        cmd = "Xvfb -displayfd %d |& grep -v 'SocketCreateListener() failed' "
        cmd += " | grep -v 'server already running'"
        cmd = cmd % (dpipe[1])
        print(cmd)
        self.proc = sp.Popen(cmd, close_fds=False, stdout=None, stderr=None,
                             shell=True)
        rfds = [dpipe[0]]
        displaybuf = ""
        # Since I cannot figure out how to open the pipe fds nonblocking,
        # resort to using select and reading one character at a time.  This
        # code must handle two cases: the display fd has been written
        # successfully to the pipe, or else the Xvfb process has exited and
        # will never write to the pipe.
        while '\n' not in displaybuf:
            (readable, writable, xable) = select.select(rfds, [], [], 1)
            if dpipe[0] in rfds:
                displaybuf = displaybuf + os.read(dpipe[0], 1)
            xcode = self.proc.poll()
            if xcode is not None:
                print("*** Xvfb exited with return code %d ***" % (xcode))
                return None

        self.display = ':'+str(int(displaybuf))
        os.close(dpipe[1])
        os.close(dpipe[0])
        self.saved_display = os.environ.get('DISPLAY')
        os.environ['DISPLAY'] = self.display
        return self

    def stop(self):
        if self.proc is None:
            return
        self.proc.kill()
        self.proc.wait()
        self.proc = None
        self.display = None
        if self.saved_display is not None:
            os.environ['DISPLAY'] = self.saved_display
        else:
            del os.environ['DISPLAY']

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



