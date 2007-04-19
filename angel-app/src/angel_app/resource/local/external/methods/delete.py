##
# Copyright (c) 2005-2006 etoy.CORPORATION, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Vincent Kraeutler, vincent@etoy.com
##

"""
WebDAV DELETE method.
"""

__all__ = ["preconditions_DELETE"]

from twisted.web2.http import HTTPError
from twisted.web2.http import StatusResponse
from twisted.web2 import responsecode

from angel_app.log import getLogger
log = getLogger(__name__)

class DeleteMixin:
    
    def preconditions_DELETE(self, request):
        """
        A DELETE operation from a non-authenticated source is allowed
        exactly if the file is not referenced in the parent resource,
        See also proppatch.
        """ 
        
        log.debug("foo")
        
        if self in self.parent().metaDataChildren():
            raise HTTPError(
                    StatusResponse(
                       responsecode.FORBIDDEN, 
                       "DELETE is forbidden on referenced resources. Try a PROPPATCH on the parent first."
                       ))