##
# Copyright (c) 2005-2006 etoy.VENTURE ASSOCIATION, Inc. All rights reserved.
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
WebDAV PUT method.
"""

__all__ = ["precondition_PUT"]

from twisted.web2.http import HTTPError

class PutMixin:
    def precondition_PUT(self, request):
        """
        A put operation from a non-authenticated source is allowed
        exactly if 
        -- the file does not exist, but is referenced in the parent resource
        -- the file is is not in a consistent state.
        See also proppatch.
        """ 
        
        if not self.exists() and not self in self.parent().metaDataChildren():
            raise HTTPError(
                    StatusResponse(
                       responsecode.FORBIDDEN, 
                       "PUT is forbidden on inexinstent unreferenced resources. Try a PROPPATCH first."
                       ))
                    
        if self.verify():
                raise HTTPError(
                    StatusResponse(
                           responsecode.FORBIDDEN, 
                           "PUT is forbidden on valid resources. Try a PROPPATCH first."
                           ))
        
        # permission granted
        return request