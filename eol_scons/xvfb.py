# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"Wrap the Xvfb process to provide a headless X server for scripts."

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
        # The Xvfb subprocess has to be able to inherit the pipe fd to write
        # the display number to it.  Python 3.4 changed to making all file
        # descriptors non-inheritable by default.
        os.set_inheritable(dpipe[1], True)
        cmd = ['Xvfb', '-displayfd', str(dpipe[1])]
        # The -displayfd option causes Xvfb to look for an available
        # display number, but it writes error messages apparently when
        # attempts to open a display fail.  It would be nice to create a
        # pipe for stderr to filter out the error messages, but that gets
        # complicated because we would need to keep reading from that pipe
        # after starting Xvfb or else risk blocking the Xvfb process.
        # Probably there would not be any output once the display number is
        # written back over the pipe, but that is not guaranteed.  It works
        # to use the shell to pipe and filter with grep, but then the
        # kill() only goes to the shell and not to the actual Xvfb process.
        # So it's back to the simplest approach and just ignoring the error
        # messages.
        print(" ".join(cmd))
        print("Looking for available displays..."
              "Ignore errors about servers already running.")
        self.proc = sp.Popen(cmd, close_fds=False, stdout=None, stderr=None,
                             shell=False)
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
                displaybuf = displaybuf + chr(os.read(dpipe[0], 1)[0])
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
