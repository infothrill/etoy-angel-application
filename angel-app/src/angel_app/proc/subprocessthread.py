"""
This module contains code for running the subprocesses in a separate thread.
In our case mainly useful in combination with the GUI, which has to control the master process,
but needs to stay responsive.
"""

import os
import sys
import signal
import time
import threading
import subprocess

from angel_app.log import getLogger

log = getLogger(__name__)

"""
Class for running an external process in its own thread.
"""
class SubprocessThread(threading.Thread):
    def __init__(self, args = None):
        """
        Instantiate the subprocess thread and define the external command.
        
        @param args: list of strings passed to subprocess.Popen()
        """
        super(SubprocessThread, self).__init__()
        self.proc = None
        self.args = args

    def run(self):
        """
        Start the subprocess defined in the constructor
        """
        self.proc = subprocess.Popen(self.args)
        #self.proc = subprocess.Popen(self.args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    def isAlive(self):
        """
        Returns True if the subprocess has not exited yet and false otherwise
        """
        if self.proc == None:
            return False
        result = self.proc.poll()
        if result == None:
            return True
        else:
            return False

    def stop(self):
        """
        This method will stop the subprocess started with run()
        """
        maxWait = 2 # number of seconds the subprocess is allowed to take when shutting down
        if self.isAlive():
            pid = self.proc.pid
            log.info("================SIGNALLING SUBPROCESS %s ========================" % `pid`)
            os.kill(pid, signal.SIGTERM) # FIXME: not cross-platform
            # give it a moment to digest the signal:
            tStart = time.time()
            tElapsed = time.time() - tStart
            while tElapsed < maxWait and self.isAlive():
                time.sleep(0.0001)
                #print "WAITING"
                tElapsed = time.time() - tStart
            # check if it's really gone:
            if self.isAlive():
                log.warn("================SIGNALLING SUBPROCESS HARD %s ========================" % `pid`)
                os.kill(pid, signal.SIGKILL) # FIXME: not cross-platform
        else:
            log.info("=========== not alive, not signalling ===============")

    def conditionalRestart(self):
        """
        Re-execute the subprocess, but only if it is currently running.
        """
        if self.isAlive():
            self.stop()
            self.run()

"""
Class to run the "master"-process from the GUI.
Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""
class MasterThread(SubprocessThread):
    def __init__(self, args = None):
        super(MasterThread, self).__init__(args = [sys.executable, "master.py"])
