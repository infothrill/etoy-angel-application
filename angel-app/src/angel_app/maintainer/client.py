from twisted.python import log
from twisted.web2 import responsecode
from twisted.web2.dav.element.rfc2518 import PropertyFind, PropertyContainer
from twisted.python.filepath import FilePath

from config.common import rootDir
from angel_app.static import AngelFile
from angel_app import elements
from angel_app.maintainer.util import relativePath

DEBUG = True

from httplib import HTTPConnection

def testConn(host = "localhost", port = 9999):
    conn = HTTPConnection(host, port)
    conn.request("PROPFIND", "/", headers = {"Depth" : 0})
    resp = conn.getresponse()
    
    if resp.status != responsecode.MULTI_STATUS: return False
    
    body = resp.read()
    conn.close()

def validateClone(url):
    """
    @param url -- url of the clone to be validated
    
    exeptions wherever they might occur are passed on to the next level (i.e. not handled),
    signalling that this (potential) clone should be ignored from now on.
    """
    DEBUG and log.err(url)
    conn = HTTPConnection(url)

    requestBody = PropertyFind(
                               PropertyContainer(
                                                 *[
                                                   elements.Revision(),
                                                   elements.PublicKeyString()
                                                   ]
                                                 ))
    
    DEBUG and log.err(requestBody.toxml())
    
    conn.request("PROPFIND", "/", headers = {"Depth" : 0}, body = requestBody.toxml())
    resp = conn.getresponse()
    if resp.status != responsecode.MULTI_STATUS:
        raise "must receive a MULTI_STATUS response for PROPFIND, otherwise something's wrong"
    body = resp.read()
    print body
    conn.close()

def updateClones(af):
    """
    @param af -- an AngelFile
    """
    #print elements.Clones().toxml()
    
    try:
        clones = af.deadProperties().get(elements.Clones.qname())
    except:
        # we have no clones
        DEBUG and log.err("no clones")
        return
    
    for clone in clones.children:
       url = str(clone.children[0].children[0])
       validateClone(url)

def inspectResource(path = rootDir):
    #if DEBUG and relativePath(resource.path) != "": raise "debugging and stopping beyond root: " + relativePath(resource.path)
    DEBUG and log.err("inspecting resource: " + path)
    DEBUG and log.err("relative path is: " + relativePath(path))
    af = AngelFile(path)
    updateClones(af)
    DEBUG and log.err("DONE\n\n")
    