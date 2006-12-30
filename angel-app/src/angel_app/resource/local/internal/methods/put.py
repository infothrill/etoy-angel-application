from twisted.python import log
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError
from angel_app import elements


from twisted.python.failure import Failure
from twisted.internet.defer import deferredGenerator, waitForDeferred
from twisted.web2.stream import readIntoFile
from twisted.web2.dav.http import statusForFailure

from twisted.web2.dav.fileop import checkResponse

DEBUG = True

class Putable(object):
    """
    A mixin class (for AngelFile) that implements put operations.
    """
    def _put(self, stream): 
       
        not self.fp.exists() and DEBUG and log.err("adding new file at: " + self.fp.path)

        if not self.isWritableFile():
            log.err("http_PUT: not authorized to put file: " + self.fp.path)
            raise HTTPError(responsecode.UNAUTHORIZED)
        
        DEBUG and log.err("_put: deleting file at: " + self.fp.path)
        
        response = waitForDeferred(deferredGenerator(self.__putDelete)())
        yield response
        response = response.getResult()
        DEBUG and log.err("_put: return code for deleting file: " + `response`)
        
        xx  = waitForDeferred(deferredGenerator(self.__putFile)(stream))
        yield xx
        xx = xx.getResult()
        
        
        xx = waitForDeferred(deferredGenerator(self._updateMetadata)())
        yield xx
        
        DEBUG and log.err("return code for updating meta data: " + `response`)
        
        yield response
        
        
    def __putDelete(self):
        """
        Original comment from Wilfredo:
        
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
        DEBUG and log.msg("Writing to file %s" % (self.fp.path,))
        
        # TODO: actually do the above
        
        if self.fp.exists():
            response = self.delete()
            DEBUG and log.err("__putDelete: " + `response`)
            checkResponse(response, "delete", responsecode.NO_CONTENT)
            success_code = responsecode.NO_CONTENT
        else:
            success_code = responsecode.CREATED
        yield success_code
    
    
    def __putFile(self, stream):
        """
         Write the contents of the request stream to resource's file
        """

        try:
            resource_file = self.fp.open("w")
        except:
            DEBUG and log.err("failed to open file: " + self.fp.path)
            raise HTTPError(statusForFailure(
                                             Failure(),
                "opening file for writing: %s" % (self.fp.path,)
                ))

        try:
            x = waitForDeferred(readIntoFile(stream, resource_file))
            yield x
            x.getResult()
            DEBUG and log.err("__putFile: read stream into file into: " + self.fp.path)
        except:
            DEBUG and log.err("failed to write to file: " + self.fp.path)
            raise HTTPError(statusForFailure(
                                             Failure(),
                "writing to file: %s" % (self.fp.path,)
                ))
        
        DEBUG and log.err("__putFile: done putting file stream: " + self.fp.path)
        DEBUG and log.err("__putFile: file contents: " + open(self.fp.path).read())
        yield None
            
            
    def http_PUT(self, request):
        """
        Respond to a PUT request. (RFC 2518, section 8.7)
        """
    
        #return self.put(request.stream)
        return deferredGenerator(self._put)(request.stream)
        #return self.put(request.stream)
        #put = deferredGenerator(self.put)
        #return put(request.stream)
        