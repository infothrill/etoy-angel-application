import os, urllib

from twisted.python.failure import Failure
from twisted.web2 import responsecode
from twisted.web2.dav.http import ResponseQueue
from twisted.web2.http import HTTPError, StatusResponse
from urlparse import urlsplit

from angel_app.log import getLogger
log = getLogger(__name__)

class Deletable(object):
    """
    A mixin class (for AngelFile) that implements deletion operations.
    """
    
    def http_DELETE(self, request):
        """
        Respond to a DELETE request. (RFC 2518, section 8.6)
        """
        log.debug("http_DELETE starting ")

        foo = self.delete(
                       request.uri, 
                       request.headers.getHeader("depth", "infinity")
                       )
        
        log.debug("http_DELETE: " + `type(foo)`)
        return foo

    def delete(self, uri = "", depth = "infinity"): 

        succeededFileOperation =  self.__delete(uri, depth)
        
        log.debug("delete on " + self.fp.path + ": done, with return code: " + `succeededFileOperation`)
        return succeededFileOperation
        
    def __deleteFile(self):
        """
        Delete a file; much simpler, eh?
        """
        os.remove(self.fp.path)
        return StatusResponse(responsecode.NO_CONTENT, "DELETED.")
    
    def _recursiveDelete(self, uri):
        """
        Recursive delete
        
        RFC 2518, section 8.6 says that if we get an error deleting a resource
        other than the collection in the request-URI, that we must respond
        with a multi-status response containing error statuses for each
        resource that we fail to delete.  It also says we should not return
        no-content (success) status, which means that we should continue after
        errors, rather than aborting right away.  This is interesting in that
        it's different from how most operating system tools act (eg. rm) when
        recursive filesystem deletes fail.
        """

        log.debug("_recursiveDelete: entering")

        # TODO: this function sucks, review and fix it
        
        uri_path = urllib.unquote(urlsplit(uri)[2])
        if uri_path[-1] == "/":
            uri_path = uri_path[:-1]

        log.debug("Deleting directory %s" % (self.fp.path,))

        # NOTE: len(uri_path) is wrong if os.sep is not one byte long... meh.
        request_basename = self.fp.path[:-len(uri_path)]

        errors = ResponseQueue(request_basename, "DELETE", responsecode.NO_CONTENT)

        # FIXME: defer this
        for dir, subdirs, files in os.walk(self.fp.path, topdown=False):
            
            log.debug("_recursiveDelete: walking " + dir)
            
            for filename in files:
                log.debug("_recursiveDelete: deleting: " + filename)
                path = os.path.join(dir, filename)
                try:
                    os.remove(path)
                except:
                    errors.add(path, Failure())

            for subdir in subdirs:
                log.debug("_recursiveDelete: deleting: " + subdir)
                path = os.path.join(dir, subdir)
                if os.path.islink(path):
                    try:
                        os.remove(path)
                    except:
                        errors.add(path, Failure())
                else:
                    try:
                        os.rmdir(path)
                    except:
                        errors.add(path, Failure())

        path = self.fp.path
        if os.path.islink(path):
            try:
                os.remove(path)
            except:
                errors.add(path, Failure())
        elif os.path.isdir(path):
            try:
                os.rmdir(path)
            except:
                errors.add(path, Failure())
        else:
            try:
                os.remove(path)
            except:
                errors.add(path, Failure())

        log.debug("_recursiveDelete: done")
        return errors.response()
    
    def __deleteDirectory(self, uri, depth):
        
        self._recursiveDelete(uri)
        
        return StatusResponse(responsecode.NO_CONTENT, 
                       "DELETED."
                       )


 
    def __delete(self, uri, depth = "infinity"):
        """
        Based on twisted.web2.dav.fileop.delete
        
        Perform a X{DELETE} operation on the given URI, which is backed by the given
        filepath.
        @param filepath: the L{FilePath} to delete.
        @param depth: the recursion X{Depth} for the X{DELETE} operation, which must
            be "infinity".
        @raise HTTPError: (containing a response with a status code of
            L{responsecode.BAD_REQUEST}) if C{depth} is not "infinity".
        @raise HTTPError: (containing an appropriate response) if the
            delete operation fails.  If C{filepath} is a directory, the response
            will be a L{MultiStatusResponse}.
        @return: a deferred response with a status code of L{responsecode.NO_CONTENT}
            if the X{DELETE} operation succeeds.
        """
    
        if self.fp.isdir(): response = self.__deleteDirectory(uri, depth)   
        else: response = self.__deleteFile()
        
        self._deRegisterWithParent()
        
        
        log.debug("__delete: done")
        return response


    def preconditions_DELETE(self, request):

        checkDepthHeader(request)
    
        if not self.exists():
            log.debug("File not found: %s" % (self.fp.path,))
            raise HTTPError(responsecode.NOT_FOUND)
        
        if not self.isWritableFile():
            log.debug("Not authorized to delete file: %s" % (self.fp.path,))
            raise HTTPError(responsecode.UNAUTHORIZED)



def checkDepthHeader(request):
        """
        RFC 2518, section 8.6 says that we must act as if the Depth header is
        set to infinity, and that the client must omit the Depth header or set
        it to infinity, meaning that for collections, we will delete all
        members.
        
        This seems somewhat at odds with the notion that a bad request should
        be rejected outright; if the client sends a bad depth header, the
        client is broken, and RFC 2518, section 8 suggests that a bad request
        should be rejected...
        
        Let's play it safe for now and ignore broken clients.
        """
        depth = request.headers.getHeader("depth", "infinity")
        if depth != "infinity":
            msg = ("Client sent illegal depth header value for DELETE: %s" % (depth,))
            log.debug(msg)
            raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, msg))
