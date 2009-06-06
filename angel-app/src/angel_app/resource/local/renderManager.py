from angel_app.log import getLogger
from angel_app.resource.local.dirlist import DirectoryLister
from twisted.web2 import http
from twisted.web2 import responsecode
from twisted.web2 import stream

log = getLogger(__name__)


class RenderManager(object):
    """
    Renders the angel resource when an HTTP GET request is encountered.
    """
    
    def __init__(self, resource):
        self.resource = resource

    def render(self, req):
        """You know what you doing. override render method (for GET) in twisted.web2.static.py"""
        if not self.resource.exists():
            return responsecode.NOT_FOUND

        if self.resource.isCollection():
            return self.renderDirectory(req)
        else:
            return self.__renderFile(req)

    def renderDirectory(self, req):
        if req.method == 'HEAD':
            return http.Response(200, {}, "")
        if req.uri[-1] != "/":
            # Redirect to include trailing '/' in URI
            log.debug("redirecting")
            return http.RedirectResponse(req.unparseURL(path=req.path+'/'))
        
        # is there an index file?
        ifp = self.resource.fp.childSearchPreauth(*self.resource.indexNames)
        if ifp:
            # render from the index file
            return self.resource.createSimilarFile(ifp.path).render(req)
        
        # no index file, list the directory
        return DirectoryLister(
                    self.resource.fp.path,
                    self.resource.listChildren(),
                    self.resource.contentTypes,
                    self.resource.contentEncodings,
                    self.resource.defaultType
                ).render(req)

    def __getResponse(self):
        """
        Set up a response to a GET request.
        """
        response = http.Response()         
        
        for (header, value) in (
            ("content-type", self.resource.contentType()),
            ("content-encoding", self.resource.contentEncoding()),
        ):
            if value is not None:
                response.headers.setHeader(header, value)
                
        return response

    def __renderFile(self, request):
        """
        The Basic AngelFile just returns the cyphertext of the file.
        """
        log.debug("running __renderFile")
        response = self.__getResponse()
        response.stream = stream.FileStream(self.resource.open(), 0, self.resource.fp.getsize())

        log.debug("done running __renderFile")
        return response
