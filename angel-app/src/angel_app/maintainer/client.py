from twisted.python import log
from twisted.web2 import responsecode
from twisted.web2.dav.element.rfc2518 import PropertyFind, PropertyContainer
from twisted.web2.dav.element import base
from twisted.web2.dav import davxml

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

def validationKeys():
    return elements.signedKeys + [elements.MetaDataSignature]

def validationRequestXML():
    """
    the (xml) body of the validation request.
    """
    return PropertyFind(
                        PropertyContainer(
                                          *[key() for key in validationKeys()]
                                          )).toxml()

def validateClone(url, af):
    """
    @param url -- url of the clone to be validated
    @param af -- angel file to be validated against
    
    exeptions wherever they might occur are passed on to the next level (i.e. not handled),
    signalling that this (potential) clone should be ignored from now on.
    """
    DEBUG and log.err(url)
    conn = HTTPConnection(url)
    
    conn.request(
                 "PROPFIND", 
                 "/", 
                 headers = {"Depth" : 0}, 
                 body = validationRequestXML()
                 )
    
    resp = conn.getresponse()
    if resp.status != responsecode.MULTI_STATUS:
        raise "must receive a MULTI_STATUS response for PROPFIND, otherwise something's wrong"
    
    responseBody = resp.read()
    #print responseBody
    
    
    msr = davxml.WebDAVDocument.fromString(responseBody)
    
    # points to the dav "prop"-element
    properties = msr.root_element.children[0].children[1].children[0]
    
    #print `properties.children`
    
    # parse the revision number
    #if not isinstance(properties.children[0], elements.Revision):# or \
#    not isinstance(properties.children[0].children[0], base.PCDATAElement):
    #    raise "illegal element for revision: " + `properties.children[0]` + `properties.children[0].__class__`
    revision = str(properties.children[0].children[0])
    #print `revision`

    contentSignatureElements = properties.children[1]
    #print publicKeyElements
    #if not isinstance(properties.children[1], elements.ContentSignature) or \
    #not [ee for ee in properties.children[1].children if isinstance(ee, base.PCDATAElement)]: 
    #    raise "illegal element(s) for meta data signature"
    contentSignature = "".join([str(ee) for ee in contentSignatureElements.children])
    #print contentSignature
  
    publicKeyElements = properties.children[2]
    #print publicKeyElements
    #if not isinstance(properties.children[1], elements.ContentSignature) or \
    #not [ee for ee in properties.children[1].children if isinstance(ee, base.PCDATAElement)]: 
    #    raise "illegal element(s) for meta data signature"
    publicKeyString = "".join([str(ee) for ee in publicKeyElements.children])
    #print publicKeyString
    
    isDeleted = str(properties.children[3].children[0])
    #print `isDeleted`
    
    metaDataSignatureElements = properties.children[4]
    #print metaDataSignatureElements
    #if not isinstance(properties.children[1], elements.ContentSignature) or \
    #not [ee for ee in properties.children[1].children if isinstance(ee, base.PCDATAElement)]: 
    #    raise "illegal element(s) for meta data signature"
    metaDataSignature = "".join([str(ee) for ee in metaDataSignatureElements.children])
    #print metaDataSignature 
    
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
       validateClone(url, af)

def inspectResource(path = rootDir):
    #if DEBUG and relativePath(resource.path) != "": raise "debugging and stopping beyond root: " + relativePath(resource.path)
    DEBUG and log.err("inspecting resource: " + path)
    DEBUG and log.err("relative path is: " + relativePath(path))
    af = AngelFile(path)
    updateClones(af)
    DEBUG and log.err("DONE\n\n")
    