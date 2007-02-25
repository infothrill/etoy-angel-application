"""
This module  provides atomic file operation facilities
"""

legalMatters = """
 Copyright (c) 2006, etoy.VENTURE ASSOCIATION
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without modification, 
 are permitted provided that the following conditions are met:
 *  Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
 *  Redistributions in binary form must reproduce the above copyright notice, 
    this list of conditions and the following disclaimer in the documentation 
    and/or other materials provided with the distribution.
 *  Neither the name of etoy.CORPORATION nor the names of its contributors may be used to 
    endorse or promote products derived from this software without specific prior 
    written permission.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
 EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
 OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
 SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT 
 OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
"""

author = """Paul Kremer, 2007"""

DEBUG = False

import re
import shutil
import os

class SingleFileTransaction:
    """
    This class provides an interface to safely work with files.
    The idea is to use a standard python file object for doing
    regular file operations and hide away safety operations like
    creation of temporary files.
    """
    def __init__(self):
        from angel_app.log import getLogger
        self.log = getLogger("SingleFileTransaction")
        self.needcopyregex = re.compile(".*[a|\+].*")
        self.needemptyregex = re.compile(".*[w].*")
        self.safe = None
    
    def open(self, name, mode = 'r', buffering = 0):
        """
        Method to open a file. Syntax is the same than the standard
        python open(). This method takes care of "securing" the file
        first. It returns a standard python file object.
        Before calling commit() on the SingleFileTransaction object,
        the changes made to the file object returned are not committed.
        """
        self.name = name
        self.mode = mode
        self.buffering = buffering
        if not self.needcopyregex.match(self.mode) == None:
            DEBUG and self.log.debug("we are in needcopy mode for file '%s'" % self.name)
            (self.safe, self.safename) = self.__createTmpCopy()
        elif not self.needemptyregex.match(self.mode) == None:
            DEBUG and self.log.debug("we are in needempty mode for file '%s'" % self.name)
            (self.safe, self.safename) = self.__createTmpEmpty()
        else:
            DEBUG and self.log.debug("we are in readonly mode for file '%s'" % self.name)
            return open(self.name, self.mode, self.buffering)
        return self.safe

    def commit(self):
        """
        Commits the changes made to the file atomically
        """
        if not None == self.safe:
            DEBUG and self.log.debug("we have a safe, so we need to commit!")
            self.safe.close()
            return os.rename(self.safename, self.name)

    def __createTmpEmpty(self):
        (safe, safename) = self.__mkstemp()
        return (safe, safename)
        
    def __createTmpCopy(self):
        (safe, safename) = self.__mkstemp()
        try:
            originalfile = open(self.name, 'rb')
            try:
                shutil.copyfileobj(originalfile, safe)
                safe.seek(0)
            finally:
                originalfile.close()
        except IOError:
            pass
        return (safe, safename)

    def __mkstemp(self):
        """
        Function to create a named temporary file. Returns an OS-level
        handle to the file and the name, as a tuple. The file is readable
        and writable only by the creating user, and executable by no one.
        """
        from errno import EEXIST
        import tempfile

        if os.name == 'posix':
            _bin_openflags = os.O_RDWR | os.O_CREAT | os.O_EXCL
        else:
            _bin_openflags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_BINARY
            
        flags = _bin_openflags
    
        while 1:
            safename = tempfile.mktemp()
            try:
                #os.open(filename, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0600)
                fd = os.open(safename, flags, 0600)
                safe = os.fdopen(fd, self.mode)
                #return (fd, name)
                return (safe, safename)
            except OSError, e:
                if e.errno == EEXIST:
                    continue # try again
                raise

if __name__ == "__main__":
    """
    test code
    """
    DEBUG = True
    import os.path
    import angel_app.log
    angel_app.log.setup()
    angel_app.log.enableHandler('console')

    import sys
    testfname = "test.data"
    print ">starting test..."
    if os.path.exists(testfname):
        print "Please remove file %s first" % testfname
        sys.exit()

    t = SingleFileTransaction()

    print ">write test"
    safe = t.open(testfname, 'wb')
    testcontent = "Some randomly chosen text to be put into the new file\n"
    safe.write(testcontent)
    t.commit()
    
    print ">read test"
    safe = t.open(testfname, 'rb')
    content = safe.read()
    assert(content == testcontent), "ERROR: content does not match what we expected!"
        
    print ">append test"
    safe = t.open(testfname, 'ab')
    appendcontent = "appended stuff\n"
    safe.write(appendcontent)
    t.commit()

    print ">read test"
    safe = t.open(testfname, 'rb')
    content = safe.read()
    assert(content == testcontent + appendcontent), "ERROR: content does not match what we expected!"

    print ">read+write test"
    safe = t.open(testfname, 'w+b')
    content = safe.read()
    assert(content == testcontent + appendcontent), "ERROR: content does not match what we expected!"
    safe.write("x")
    safe.seek(len(content))
    assert(safe.read(1) == 'x'), "ERROR: content does not match what we expected!"
    t.commit()
    
    