##
# Copyright (c) 2005 Apple Computer, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# DRI: Wilfredo Sanchez, wsanchez@apple.com
##

"""
WebDAV file operations

This API is considered private to static.py and is therefore subject to
change.
"""

__all__ = [
   "delete",
    "put"
]

import os
import urllib
from urlparse import urlsplit

from twisted.python import log
from twisted.python.failure import Failure
from twisted.internet.defer import succeed, deferredGenerator, waitForDeferred
from twisted.web2 import responsecode
from twisted.web2.http import StatusResponse, HTTPError
from twisted.web2.stream import readIntoFile
from twisted.web2.dav.http import ResponseQueue, statusForFailure

#from angel_app.static import AngelFile
#from angel_app.elements import Deleted

DEBUG = True

def put(stream, filepath, uri=None):
    """
    Perform a PUT of the given data stream into the given filepath.
    @param stream: the stream to write to the destination.
    @param filepath: the L{FilePath} of the destination file.
    @param uri: the URI of the destination resource.
        If the destination exists, if C{uri} is not C{None}, perform a
        X{DELETE} operation on the destination, but if C{uri} is C{None},
        delete the destination directly.
        Note that whether a L{put} deletes the destination directly vs.
        performing a X{DELETE} on the destination affects the response returned
        in the event of an error during deletion.  Specifically, X{DELETE}
        on collections must return a L{MultiStatusResponse} under certain
        circumstances, whereas X{PUT} isn't required to do so.  Therefore,
        if the caller expects X{DELETE} semantics, it must provide a valid
        C{uri}.
    @raise HTTPError: (containing an appropriate response) if the operation
        fails.
    @return: a deferred response with a status code of L{responsecode.CREATED}
        if the destination already exists, or L{responsecode.NO_CONTENT} if the
        destination was created by the X{PUT} operation.
    """
    log.msg("Writing to file %s" % (filepath.path,))

    if filepath.exists():
        if uri is None:
            try:
                if filepath.isdir():
                    rmdir(filepath.path)
                else:
                    # vincent: we want to overwrite the file, not remove it and
                    # then create it again (which kills the xattr metadata)
                    open(filepath.path, "w").close()
                    #os.remove(filepath.path)
            except:
                raise HTTPError(statusForFailure(
                    Failure(),
                    "writing to file: %s" % (filepath.path,)
                ))
        else:
            response = waitForDeferred(delete(uri, filepath))
            yield response
            response = response.getResult()
            checkResponse(response, "delete", responsecode.NO_CONTENT)

        success_code = responsecode.NO_CONTENT
    else:
        success_code = responsecode.CREATED
        
    #
    # Write the contents of the request stream to resource's file
    #

    try:
        resource_file = filepath.open("w")
    except:
        raise HTTPError(statusForFailure(
            Failure(),
            "opening file for writing: %s" % (filepath.path,)
        ))

    try:
        x = waitForDeferred(readIntoFile(stream, resource_file))
        yield x
        x.getResult()
    except:
        raise HTTPError(statusForFailure(
            Failure(),
            "writing to file: %s" % (filepath.path,)
        ))

    # Restat filepath since we modified the backing file
    filepath.restat(False)
    yield success_code

put = deferredGenerator(put)


def checkResponse(response, method, *codes):
    assert (
        response in codes,
        "%s() should have raised, but returned one of %r instead" % (method, codes)
    )