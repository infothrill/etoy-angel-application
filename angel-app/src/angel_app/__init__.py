"""
admin: utilities for administration of the repository
config: configuration file management
contrib: (modified) external libraries that we ship with the angel-app
elements: XML element definitions
graph: graph traversal routines
log: loggin facilities
logserver: handle logs of multiple processes
procmanager: utilities for spawning and managing processes
resource: implementation of the various resources
version: version information
wx: GUI related
"""

all = [
       "admin", 
       "config", 
       "contrib", 
       "elements", 
       "graph", 
       "io",
       "ipv6",
       "log",  
       "logserver", 
       "proc", 
       "procmanger", 
       "resource", 
       "server", 
       "singlefiletransaction",
       "version",
       "wx"
       ]

# register xml elements with parser. see task #3500
from twisted.web2.dav.element.parser import registerElements
from angel_app import elements
registerElements(elements)