"""
This module  provides atomic file operation facilities.
Basically, all we do, is rely on python's os.mkstemp()
function. This only provides wrapping for ease of use
and also ensuring we stay on the same filesystem by
restricting all operations to the angel-app homepath.

Note: logging is not allowed in this class, because
this class needs to run without facilities that might
require safe file operations!
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
import tempfile

from angel_app.config.defaults import getAngelHomePath


bootstrap = True

def setup():
    """
    setup() creates the needed internal directory structure for safe
    file  transactions (.angel_app/tmp/). It must be called once
    during bootstrap.
    """
    path = getTmpPath()
    if not os.path.exists(path):
        os.mkdir(path)
    elif not os.path.isdir(path):
        raise "Filesystem entry '%s' occupied, cannot create directory here." % path

def getTmpPath():
    """
    Returns the full path of the tmp directory to be used for safe
    file operations. This method does not ensure the path is valid!
    """
    tmpPath = os.path.join(getAngelHomePath(), "tmp")
    return tmpPath


def purgeTmpPathAndSetup():
    """
    This function will empty the tmp path. It must only be called
    during bootstrap and while no other process is using the tmp path!
    """
    shutil.rmtree(getTmpPath(), ignore_errors = True) # FIXME: do we want to catch errors here?
    setup()

class SingleFileTransaction:
    """
    This class provides an interface to safely work with files.
    The idea is to use a standard python file object for doing
    regular file operations and hide away safety operations like
    creation of temporary files.
    """

    def __init__(self):
        """
        Just set some attributes
        """
        self._needcopyregex = re.compile(".*[a|\+].*")
        self._needemptyregex = re.compile(".*[w].*")
        self._safe = None
        self._basedir = getTmpPath()
    
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
        if not self._needcopyregex.match(self.mode) == None:
            if DEBUG: print "we are in needcopy mode for file '%s'" % self.name
            (self._safe, self._safename) = self.__createTmpCopy()
        elif not self._needemptyregex.match(self.mode) == None:
            if DEBUG: print "we are in needempty mode for file '%s'" % self.name
            (self._safe, self._safename) = self.__createTmpEmpty()
        else:
            if DEBUG: print "we are in readonly mode for file '%s'" % self.name
            return open(self.name, self.mode, self.buffering)
        return self._safe

    def commit(self):
        """
        Commits the changes made to the file atomically
        """
        if not None == self._safe:
            if DEBUG: "we have a safe, so we need to commit!"
            self._safe.close()
            return os.rename(self._safename, self.name)

    def __createTmpEmpty(self):
        """
        Creates an empty temp file
        @return see __mkstemp()
        """
        (safe, safename) = self.__mkstemp()
        return (safe, safename)
        
    def __createTmpCopy(self):
        """
        Creates a temp file, originally being a copy of the file
        specified in open().
        @return see __mkstemp()
        """
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
        Function to create a named temporary file. Returns a tuple containing
        the file object and the filename.
        The file is readable and writable only by the creating user, and
        executable by no one.
        """
        import time
        fd, safename = tempfile.mkstemp(suffix='.tmp', prefix='safe', dir=self._basedir)
        safe = os.fdopen(fd, self.mode)
        return (safe, safename)


if __name__ == "__main__":
    """
    test code
    """
    DEBUG = True
    import os.path

    import sys
    testfname = "test.data"
    print ">starting test..."
    if os.path.exists(testfname):
        print "Please remove file %s first" % testfname
        sys.exit()

    setup()
    purgeTmpPathAndSetup()
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
    
    