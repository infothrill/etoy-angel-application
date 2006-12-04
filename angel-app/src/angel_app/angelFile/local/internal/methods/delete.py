import os, urllib
from urlparse import urlsplit
from twisted.python import log
from twisted.python.failure import Failure
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.http import ResponseQueue, statusForFailure
from angel_app import elements

DEBUG = False

class Deletable(object):
    """
    A mixin class (for AngelFile) that implements deletion operations.
    """
    def delete(self, uri = "", depth = "infinity"): 
    
        if not self.fp.exists():
            DEBUG and log.err("File not found: %s" % (self.fp.path,))
            raise HTTPError(responsecode.NOT_FOUND)

        if not self.isWritableFile():
            DEBUG and log.err("Not authorized to delete file: %s" % (self.fp.path,))
            raise HTTPError(responsecode.UNAUTHORIZED)

        succeededFileOperation =  self.__delete(uri, depth)
        
        self.deadProperties().set(
                                  elements.Deleted().fromString("1"))
        
        self.update()
        
        
        log.err("done deleting file, with return code: " + `succeededFileOperation`)
        return succeededFileOperation
        
    def __deleteFile(self):
        """
        Delete a file; much simpler, eh?
        """
        DEBUG and log.err("Deleting file %s" % (self.fp.path,))
        try:
            if self.fp.exists():
              open(self.fp.path, "w").close()
        except:
            ff = Failure()
            log.err(ff)
            raise HTTPError(statusForFailure(
                ff, #Failure(),
                "deleting file: %s" % (self.fp.path,)
            ))

        return responsecode.NO_CONTENT
    
    def __recursiveDelete(self, uri):
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

        # TODO: this function sucks, review and fix it
        
        uri_path = urllib.unquote(urlsplit(uri)[2])
        if uri_path[-1] == "/":
            uri_path = uri_path[:-1]

        DEBUG and log.msg("Deleting directory %s" % (self.fp.path,))

        # NOTE: len(uri_path) is wrong if os.sep is not one byte long... meh.
        request_basename = self.fp.path[:-len(uri_path)]

        errors = ResponseQueue(request_basename, "DELETE", responsecode.NO_CONTENT)

        # FIXME: defer this
        for dir, subdirs, files in os.walk(self.fp.path, topdown=False):
            for filename in files:
                path = os.path.join(dir, filename)
                try:
                    os.remove(path)
                except:
                    errors.add(path, Failure())

            for subdir in subdirs:
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

        #try:
        #    os.rmdir(self.fp.path)
        #except:
        #    raise HTTPError(statusForFailure(
        #        Failure(),
        #        "deleting directory: %s" % (self.fp.path,)
        #    ))

        return errors.response()
    
    def __deleteDirectory(self, uri, depth):
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
        if depth != "infinity":
            msg = ("Client sent illegal depth header value for DELETE: %s" % (depth,))
            DEBUG and log.err(msg)
            raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, msg))
        
        self.__recursiveDelete(uri)
        
        return responsecode.NO_CONTENT


 
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
        
        return response
    
    
    def http_DELETE(self, request):
        """
        Respond to a DELETE request. (RFC 2518, section 8.6)
        """

        return self.delete(
                       request.uri, 
                       request.headers.getHeader("depth", "infinity")
                       )
        #return delete(request.uri, self.fp, depth)

