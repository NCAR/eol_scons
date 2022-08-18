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



def test_xvfb_stop():
    import time
    xvfb = Xvfb()
    xvfb.start()
    pid = xvfb.proc.pid
    time.sleep(2)
    xvfb.stop()
    
