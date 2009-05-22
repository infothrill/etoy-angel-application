"""
Module providing more or less low level methods for doing IO

The original intent was to be able to do rate limiting on network transfers.
"""

from __future__ import division

import time
import StringIO
from copy import deepcopy

from angel_app.log import getLogger

log = getLogger(__name__)

def bufferedReadLoop(readCall, blocksize, totalsize, callbacks):
    """
    Does a fobj.read(blocksize) loop and calls each callback provided with the
    buffer just read. Returns the number of bytes read.
    
    @param fobj: an object that supports the read(numbytes) calls
    @param blocksize: number of bytes to read per iteration
    @param totalsize: total number of bytes to read
    @param callbacks: list of callbacks to be called with the buffer read for each iteration
    @return: number of bytes read
    """
    bytesread = 0
    while bytesread < totalsize:
        buf = readCall(blocksize)
        if len(buf) == 0:
            log.warn("Unexpected EOF after %s bytes, expected total %s bytes. Remote disconnect?" % (bytesread, totalsize))
            break
        bytesread += len(buf)
        for callback in callbacks:
            callback(buf)
    return bytesread

def bufferedRead(readCall, blocksize, totalsize, callbacks):
    """
    Same as bufferedReadLoop(), except that it returns the data that was read.
    
    ATTENTION:
    It therefore might eat a substantial amount of memory and should used with care.
    """
    data = StringIO.StringIO()
    mycallbacks = deepcopy(callbacks)
    mycallbacks.append(data.write)
    bufferedReadLoop(readCall, blocksize, totalsize, mycallbacks)
    return data.getvalue()

    
class RateLimit(object):
    """Tool to limit the speed of subsequent read()/write() calls by sleeping inbetween"""

    def __init__(self, total_size, rate_limit = None):
        """rate limit in bytes / second"""
        self.rate_limit = rate_limit
        self.rate_limit_kb = rate_limit / 1024
        self.total_size = total_size
        self.total_size_kb = total_size / 1024
        self.piped_bytes = 0
        self.start = time.time()
        self._lastlog = 0

    def __call__(self, buf):
        if self.rate_limit is None or self.rate_limit <= 0: return # no limit
        self.piped_bytes += len(buf)
        elapsed_time = time.time() - self.start
        if elapsed_time != 0:
            expected_time = self.piped_bytes / self.rate_limit
            sleep_time = expected_time - elapsed_time
            if sleep_time > 0: # only sleep when it's worth it ;-)
                self._log(self.piped_bytes / elapsed_time, sleep_time)
                time.sleep(sleep_time)
                
    def _log(self, rate, sleep_time):
        "helper method to limit the rate of logging to 1 / second"
        now = time.time()
        if now - self._lastlog > 1: # log once per second max
            log.debug("Rate limiting (max %.1f kiB/s): %d kiB of %d kiB piped at %.1f kiB/s, sleeping for %.4f s" % (self.rate_limit_kb, self.piped_bytes / 1024 ,self.total_size_kb, rate / 1024, sleep_time))
            self._lastlog = now 

