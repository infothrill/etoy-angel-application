
import zope.interface

class AngelResource(zope.interface.Interface):
    """
    Angel-app resource interface specification.
    """
    
    def exists(self):
        """
        Checks whether this resource is accesible.
        """
    
    def isCollection():
        """
        Checks whether this resource is a collection resource.
        @return: C{True} if this resource is a collection resource, C{False}
            otherwise.
        """

    def findChildren(depth):
        """
        Returns an iterable of child resources for the given depth.
        Because resources do not know their request URIs, chidren are returned
        as tuples C{(resource, uri)}, where C{resource} is the child resource
        and C{uri} is a URL path relative to this resource.
        @param depth: the search depth (one of C{"0"}, C{"1"}, or C{"infinity"})
        @return: an iterable of tuples C{(resource, uri)}.
        """

    def hasProperty(property, request):
        """
        Checks whether the given property is defined on this resource.
        @param property: an empty L{davxml.WebDAVElement} instance or a qname
            tuple.
        @param request: the request being processed.
        @return: a deferred value of C{True} if the given property is set on
            this resource, or C{False} otherwise.
        """

    def readProperty(property, request):
        """
        Reads the given property on this resource.
        @param property: an empty L{davxml.WebDAVElement} class or instance, or
            a qname tuple.
        @param request: the request being processed.
        @return: a deferred L{davxml.WebDAVElement} instance
            containing the value of the given property.
        @raise HTTPError: (containing a response with a status code of
            L{responsecode.CONFLICT}) if C{property} is not set on this
            resource.
        """

    def writeProperty(property, request):
        """
        Writes the given property on this resource.
        @param property: a L{davxml.WebDAVElement} instance.
        @param request: the request being processed.
        @return: an empty deferred which fires when the operation is completed.
        @raise HTTPError: (containing a response with a status code of
            L{responsecode.CONFLICT}) if C{property} is a read-only property.
        """

    def removeProperty(property, request):
        """
        Removes the given property from this resource.
        @param property: a L{davxml.WebDAVElement} instance or a qname tuple.
        @param request: the request being processed.
        @return: an empty deferred which fires when the operation is completed.
        @raise HTTPError: (containing a response with a status code of
            L{responsecode.CONFLICT}) if C{property} is a read-only property or
            if the property does not exist.
        """

    def listProperties(request):
        """
        @param request: the request being processed.
        @return: a deferred iterable of qnames for all properties defined for
            this resource.
        """

