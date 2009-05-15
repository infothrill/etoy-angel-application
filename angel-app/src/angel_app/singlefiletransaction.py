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

from angel_app.config.config import getConfig
angelConfig = getConfig()

bootstrap = True

def setup():
    """
    setup() creates the needed internal directory structure for safe
    file  transactions (.angel_app/tmp/). It must be called once
    during bootstrap.
    Executing is not strictly necessary when using the SingleFileTransaction
    class directly (it can have a temp dir as parameter in the constructor)
    """
    path = getTmpPath()
    if not os.path.exists(path):
        os.mkdir(path)
    elif not os.path.isdir(path):
        raise Exception, "Filesystem entry '%s' occupied, cannot create directory here." % path

def getTmpPath():
    """
    Returns the full path of the tmp directory to be used for safe
    file operations (from the angelConfig).
    This method does not ensure the path is valid!
    """
    tmpPath = os.path.join(angelConfig.get("common","angelhome"), "tmp")
    return tmpPath


def purgeTmpPathAndSetup():
    """
    This function will empty the configured tmp path. It must only be called
    during bootstrap and while no other process is using the tmp path!
    """
    shutil.rmtree(getTmpPath(), ignore_errors = False) # FIXME: catch errors
    setup()

class SingleFileTransaction(object):
    """
    This class provides an interface to safely work with files.
    The idea is to use a standard python file object for doing
    regular file operations and hide away safety operations like
    creation of temporary files.
    Parameters:
    tmpPath - full pathname to the temp directory to operate in (optional)
    """

    def __init__(self, tmpPath = None):
        """
        The constructor
        
        @param tmpPath: string path to temporary directory (optional)
        """
        self._needcopyregex = re.compile(".*[a|\+].*")
        self._needemptyregex = re.compile(".*[w].*")
        self.safe = None # placeholder for the python file object that points to the temp file
        if tmpPath == None:
            self._basedir = getTmpPath()
        else:
            self._basedir = tmpPath
        assert os.path.isdir(self._basedir), "temp path '%s' does not exist" % self._basedir
    
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
            (self.safe, self.safename) = self.__createTmpCopy()
        elif not self._needemptyregex.match(self.mode) == None:
            if DEBUG: print "we are in needempty mode for file '%s'" % self.name
            (self.safe, self.safename) = self.__createTmpEmpty()
        else:
            if DEBUG: print "we are in readonly mode for file '%s'" % self.name
            return open(self.name, self.mode, self.buffering)
        return self.safe

    def commit(self):
        """
        Commits the changes made to the file atomically and return
        the filename of the commit
        """
        if not None is self.safe:
            if DEBUG: print "we have a safe, so we need to commit!"
            if not self.safe.closed:
                self.safe.flush()
                os.fsync(self.safe.fileno())
                self.safe.close()
            os.rename(self.safename, self.name)
            return self.name

    def cleanup(self):
        """
        Cleanup left overs that have not been comitted.
        Usually, you want to call this method if something failed during writing
        to the safe file and you haven't comitted yet, in order to discard
        the temporary data.
        """
        if not self.safe is None:
            try:
                if not self.safe.closed:
                    self.safe.close()
                os.unlink(self.safename)
            except: # don't fail / worst case is spurious leftovers
                pass
            self.safe = None

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
        fd, safename = tempfile.mkstemp(suffix='.tmp', prefix='safe', dir=self._basedir)
        safe = os.fdopen(fd, self.mode)
        return (safe, safename)

    def __del__(self):
        self.cleanup()

import unittest

class SingleFileTransactionTest(unittest.TestCase):

    def setUp(self):
        self.testdir = tempfile.mkdtemp('tmp', 'unittest', os.getcwd())
        self.teststring = "Lorem Ipsum is simply dummy text of the printing and typesetting industry.\n"
        self.teststring2 = "This is on a new line.\n"
        self.testfilename = os.path.join(self.testdir, 'test.dat')
        self.t = SingleFileTransaction(self.testdir)

    def testWriteNewFile(self):
        #t = SingleFileTransaction(self.testdir)
        safe = self.t.open(self.testfilename, 'wb')
        safe.write(self.teststring)
        fname = self.t.commit()
        # now, self.testfilename should exist:
        self.assertEqual(self.testfilename, fname)
        self.assertEqual(True, os.path.exists(self.testfilename))
        # also, it should have the content:
        self.assertEqual(self.teststring, open(self.testfilename).read())
        
    def testAppendToFile(self):
        # first, create a new file with content:
        safe = self.t.open(self.testfilename, 'wb')
        safe.write(self.teststring)
        self.t.commit()
        # now open ind append mode and append:
        safe = self.t.open(self.testfilename, 'ab')
        safe.write(self.teststring2)
        self.t.commit()
        content = open(self.testfilename).read()
        self.assertEqual(self.teststring + self.teststring2, content)

    def testOverwriteFile(self):
        # first create, an initial file to be overwritten:
        safe = self.t.open(self.testfilename, 'wb')
        safe.write(self.teststring)
        self.t.commit()
        # now, overwrite it, with new content:
        safe = self.t.open(self.testfilename, 'wb')
        safe.write(self.teststring2)
        self.t.commit()
        self.assertEqual(self.teststring2, open(self.testfilename).read())

    def testReadWriteFile(self):
        # first create, an initial file to work on:
        safe = self.t.open(self.testfilename, 'wb')
        safe.write(self.teststring)
        self.t.commit()
        # open it in read+write mode:
        safe = self.t.open(self.testfilename, 'w+b')
        self.assertEqual(self.teststring, safe.read())
        # append, file pointer is now at end of file:
        safe.write(self.teststring2)
        safe.seek(len(self.teststring))
        self.assertEqual(safe.read(len(self.teststring2)), self.teststring2)
#        self.assertEqual(self.teststring + self.teststring2, open(self.testfilename).read())
        # rewind file pointer and overwrite beginning of file:
        safe.seek(0)
        safe.write(self.teststring2)
        safe.seek(0)
        self.assertEqual(safe.read(len(self.teststring2)), self.teststring2)
        self.t.commit()
        # result must now match 
        expectedcontent = self.teststring2 + self.teststring[len(self.teststring2):] + self.teststring2
        self.assertEqual(expectedcontent, open(self.testfilename).read())
    
    def testCleanup(self):
        #t = SingleFileTransaction(self.testdir)
        safe = self.t.open(self.testfilename, 'wb')
        safe.write(self.teststring)
        self.t.cleanup()
        fname = self.t.commit()
        # now, nothing should exist, because we ran cleanup():
        self.assertEqual(fname, None)
        self.assertEqual(False, os.path.exists(self.testfilename))
        del self.t # make sure the destructor does not fail by calling it explicitly

    def tearDown(self):
        shutil.rmtree(self.testdir)

if __name__ == "__main__":
    """
    test code
    """
    unittest.main()