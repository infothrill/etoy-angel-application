all = ["crypto", "elements", "fileop", "maintainer", "method", "static"]

"""
crypto:       trivial ezPyCrypto stuff
elements:     angel-app specific WebDAV XML element definitions
fileop:       we need to override some operations from twisted.web2.dav.fileop.py
maintainer:   routines for the maintainer loop (client utils, tree steppgin etc.)
method:       hacked versions of the http_* methods (exposed as http methods, e.g. GET, PUT etc.); see also twisted.web2.dav.method
static:       the main angel-app data-structure ('AngelFile'). see also twisted.web2.dav.static.py and twisted.web.static.py
"""