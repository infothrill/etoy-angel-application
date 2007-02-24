legalMatters = """
 Copyright (c) 2006, etoy.VENTURE ASSOCIATION
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without modification, 
 are permitted provided that the following conditions are met:
 *  Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
 *  Redistributions in binary form must reproduce the above copyright notice, 
    this list of conditions and the following disclaimer in the documentation 
    and/or other materials provided with the distribution.
 *  Neither the name of etoy.CORPORATION nor the names of its contributors may be used to 
    endorse or promote products derived from this software without specific prior 
    written permission.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
 EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
 OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
 SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT 
 OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
"""

author = """Vincent Kraeutler, 2006"""

from angel_app.log import getLogger
from angel_app.resource.remote.client import inspectResource
import time

log = getLogger()

def makeResourceID(relativePath = ""):
    return relativePath + `time.gmtime()`

    
def inspectWithResponse(resource):
    """
    When we have processed a modifying WebDAV request (such as PUT, MKCOL, DELETE) successfully,
    rather than returning immediately we may in many cases want to propagate the changes through the
    network first. This is conveniently done by a call to inspectResource, after which we can safely
    return the response.
    """

    log.error("foo")
    # higher-order foo-nctions
    def foo(response):
        log.info("inspecting: " + resource.fp.path)
        try:
            # if we're not the root resource, inspect the parent
            if None != resource.parent():
                inspectResource(resource.parent().fp.path)
            inspectResource(resource.fp.path)
        except:
            log.warn("failed to update clones after processing request for " + resource.fp.path)
                
        return response
    
    return foo
