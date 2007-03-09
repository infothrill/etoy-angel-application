"""
This module contains code for running master and wx in the same
process, using two threads.
"""

import wx
import threading
     
"""
Class for the thread running our external process in its own thread.
Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""
class MasterThread(threading.Thread):
    def __init__(self):
        super(MasterThread, self).__init__()
        self.proc = None

    def run(self):
        import sys
        import subprocess
        self.showOutput = True
        m = [sys.executable, 'master.py']
        self.proc = subprocess.Popen(m, stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT)
        while self.showOutput:
            line = self.proc.stdout.readline()
            if len(line):
                sys.stdout.write(line)

    def stop(self):
        import os
        from signal import SIGTERM
        import signal
        if not self.proc == None:
            print "================SIGNALLING SUBPROCESS %s ========================" % `self.proc.pid`
            self.showOutput = False
            os.kill(self.proc.pid, SIGTERM)


