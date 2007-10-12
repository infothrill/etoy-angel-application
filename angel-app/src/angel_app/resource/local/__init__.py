"""
Behaviour of "local" resources. I.e. locally stored resources, that are exposed via a WebDAV interface.

The layout of these packages follows this pattern:

basic.Basic extends DAVFile with functionality needed by all angel-app WebDAV resources, such as
the self.parent() method.

internal.resource.Crypto extends basic.Basic and provides additional methods for destructive updates,
such as self._updateMedata, self.encrypt etc. . Handlers for HTTP/WebDAV methods specific to this class
are implemented as mixin-classes (one module per WebDAV method) in internal.method.

external.resource.External extends basic.Basic, providing no additional (at the moment) functionality. 
Handlers for HTTP/WebDAV methods specific to this class are implemented as mixin-classes 
(one module per WebDAV method) in external.method.
"""

all = [
       "external",
       "internal", 
       "basic",
       "dirlist",
       "propertyManager"
       "util",
       ]