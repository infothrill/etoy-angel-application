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
        f = self.resource.open()
        filesize = self.resource.fp.getsize()
        response = self.__getResponse()
        rangeheader = request.headers.getHeader('range')
        if rangeheader is not None:
            log.debug("http byte range header is: %s" % repr(rangeheader))
            assert rangeheader[0] == 'bytes', "Syntactically unknown http range header %s" % repr(rangeheader) 
            bytesrangetuple = rangeheader[1][0]
            rangestart, rangeend = bytesrangetuple[0], bytesrangetuple[1]
            rangelength = rangeend - rangestart
            if rangestart < 0 or rangeend <=0 or rangelength <= 0 or (rangestart + rangelength) > filesize:
                # TODO: we SHOULD probably satisfy RFC 2616: 10.4.17. 416 Requested Range Not Satisfiable
                response.code = responsecode.REQUESTED_RANGE_NOT_SATISFIABLE
                f.close()
                return response
            else: 
                response.code = responsecode.PARTIAL_CONTENT
                response.headers.setHeader('content-range', "bytes %s-%s/%s " % ( str(rangestart), str(rangeend), str(rangelength)))
        else:
            rangestart = 0
            rangelength = filesize

        response.stream = stream.FileStream(f, rangestart, rangelength)

        log.debug("done running __renderFile")
        return response
