from twisted.python.filepath import FilePath
from twisted.web2.dav import davxml
from os import sep
from angel_app import elements
from angel_app.log import getLogger

log = getLogger("util")
DEBUG = True
DEBUG and log.debug("util module loaded")

def validateMulistatusResponseBody(rawData = ""):
    """
    Assert that every response code in the MULTISTATUS response is 200 OK.
    """
    rr = davxml.WebDAVDocument.fromString(rawData).root_element
    for child in rr.children:
        ps = child.childOfType(davxml.PropertyStatus)
        ss = ps.childOfType(davxml.Status)
        assert str(ss) == "HTTP/1.1 200 OK", "MULTISTATUS response is not 200 OK: " + rawData 
    
    
def syncClones(angelFile, clonesB):
    """
    Insert all as yet unknown clones from clonesB into the angelFile.
    """
    dp = angelFile.deadProperties()
    try:
        clones = dp.get(elements.Clones.qname())
    except:
        log.error("root directory has no clones -- initializing.")
        clones = elements.Clones()

    cc = [child for child in clones.children]
    for peer in clonesB.children:
        if peer not in cc:
            cc.append(peer)
    log.info("util: " + `elements.Clones(*cc)`)
    dp.set(elements.Clones(*cc))
