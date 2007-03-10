"""
This module contains code for running master and wx in the same
process, using two threads.
"""

import wx
import threading
import os
import sys
from signal import SIGTERM, SIGKILL
import signal
import time
     
"""
Class for the thread running our external process in its own thread.
Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""
class MasterThread(threading.Thread):
    def __init__(self):
        super(MasterThread, self).__init__()
        self.pid = None

    def run(self):
        import sys
        import subprocess
        self.showOutput = True
        # TODO: is PYTHONPATH ok here?
        m = [sys.executable, 'master.py']
        self.pid = subprocess.Popen(m).pid
        self.taillog()
        
    def isAlive(self):
        if self.pid == None:
            return False
        pid = self.pid
        try:
            os.kill(pid, 0)
        except OSError, err:
            return False
        return True

    def stop(self):
        # FIXME: for some reason, it seems impossible to make the subprocess go away,
        # it hangs around in zombie state until the GUI quits as well !??!?
        if self.isAlive():
            pid = self.pid
            print "================SIGNALLING SUBPROCESS %s ========================" % `pid`
            os.kill(pid, SIGTERM)
            time.sleep(1.5)
            if self.isAlive():
                print "================SIGNALLING SUBPROCESS HARD %s ========================" % `pid`
                time.sleep(2.5)
                os.kill(pid, SIGKILL)
        else:
            print "=========== not alive, not signalling ==============="

    def taillog(self):
        """
        Does `tail -f` on the master.log logfile, so we don't need to read
        from the subprocess's STDOUT
        """
        #Set the filename and open the file
        filename = angel_app.log.getAngelLogFilenameForApp('master')
        file = open(filename,'r')
        
        #Find the size of the file and move to the end
        st_results = os.stat(filename)
        st_size = st_results[6]
        file.seek(st_size)
        
        while True:
            where = file.tell()
            line = file.readline()
            if not line:
                #time.sleep(1)
                file.seek(where)
            else:
                print line, # already has newline
                
    def win32kill(pid): # TODO: use this! (also in daemonizer.py)
        """kill function for Win32"""
        import win32api
        handle = win32api.OpenProcess(1, 0, pid)
        return (0 != win32api.TerminateProcess(handle, 0))