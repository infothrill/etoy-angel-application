"""
@copyright: 2007, etoy.VENTURE association
@author: Vincent Kraeutler
See LICENSE for licensing information.
"""

from angel_app.log import getLogger
log = getLogger(__name__)

from twisted.web2 import responsecode

def httpError(code, message):
    raise HTTPError(StatusResponse(code, message))

def mustExist(resource):
    if not resource.exists():
        httpError(responsecode.NOT_FOUND, 
                  "The resource " + resource.relativePath() + " was not found.")
        
def mustBeReferenced(resource):
    if not resource.referenced():
        httpError(responsecode.FAILED_DEPENDENCY,
            "The resource " + resource.relativePath() + " is not referenced by its parent")