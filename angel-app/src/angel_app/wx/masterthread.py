"""
This module contains code for running master and wx in the same
process, using two threads.
"""

import threading
import os
import sys
import signal
import time
import angel_app.log
import subprocess
     
"""
Class for the thread running our external process in its own thread.
Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""

EXTERNAL_SCRIPT_NAME = "master.py" # name of the script to be executed

class MasterThread(threading.Thread):
    def __init__(self):
        super(MasterThread, self).__init__()
        self.proc = None

    def run(self):
        """
        Start the subprocess
        """
        self.showOutput = True
        # TODO: is PYTHONPATH ok here?
        m = [sys.executable, EXTERNAL_SCRIPT_NAME]
        #self.proc = subprocess.Popen(m, stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)
        self.proc = subprocess.Popen(m)
        #self.taillog()
        
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
            print "================SIGNALLING SUBPROCESS %s ========================" % `pid`
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
                print "================SIGNALLING SUBPROCESS HARD %s ========================" % `pid`
                os.kill(pid, signal.SIGKILL) # FIXME: not cross-platform
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
                
    def win32kill(self, pid): # TODO: use this! (also in daemonizer.py), currently unused
        """
        kill function for Win32
        """
        import win32api
        handle = win32api.OpenProcess(1, 0, pid)
        return (0 != win32api.TerminateProcess(handle, 0))