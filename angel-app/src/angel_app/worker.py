"""
This module provides methods to delegate work to be done.
This supposedly provides a layer of indirection for the actual implementation
of workers.
For now, this code can 
"""

import sys
from logging import getLogger

from angel_app.config.config import getConfig

log = getLogger(__name__)
cfg = getConfig()

class WorkerError(object):
    """Class for passing on exceptions raised in worker processes."""
    def __init__(self, type, value, traceback = []):
        self._type = type
        self._value = value
        self._traceback = traceback
    def __repr__(self):
        return "<WorkerError %s: %s>" % (self._type, self._value)
    def formatted_tb(self):
        """returns a traceback as in traceback.format_tb()"""
        return self._traceback
    def type(self):
        return self._type
    def value(self):
        return self._value


def dowork(function, items, children = 5):
    """
    High level method to delegate work to a function.
    This is essentially a hack to allow using optimized parallelization
    as well as sequential execution, based on the configuration
     
    @param function: a callable
    @param items: a list of things that should be passed individualy to function
    @param children: max children to be run in parallel at a time
    """
    if len(items) < 1:
        return {}
    elif len(items) > 1 and cfg.getboolean('common', 'workerforking'):
        return forkedwork(function, items, children)
    else: # if only 1 item, do not fork()!
        return serialwork(function, items, children)

def forkedwork(function, items, children = 5):
    "run function on each member of items in parallel using fork()"  
    log.debug("forkedwork(): parallel execution with %i tasks (max %i)", len(items), children)
    from angel_app.contrib import delegate
    resMap = delegate.parallelize(function, items, children)
    # map errors to our own wrapper (WorkerError)
    for k in resMap:
        if isinstance(resMap[k], delegate.Exception):
            resMap[k] = WorkerError(resMap[k].type, resMap[k].value, resMap[k].tbdump)
    return resMap

def serialwork(function, items, children = 5):
    "run function on each member of items in a serial fashion"
    log.debug("serialwork(): sequential execution for %i tasks", len(items))
    res = {}
    import traceback
    for item in items:
        try:
            res[item] = function(item)
        except Exception, e:
            res[item] = WorkerError(type(e), e, traceback = traceback.format_tb(sys.exc_traceback))
    return res

def main():
    """
    main method for testing only
    """
    from angel_app.log import initializeLogging
    from angel_app.log import getLogger
    initializeLogging('shell', ['console'])
    log = getLogger()
    items = [1, 2, 6]
    def testmethod(i):
        "will raise an exception if i > 5"
        if i > 5:
            raise ValueError, "Test"
        return i
    res = forkedwork(testmethod, items)
    for item in res:
        print item
        if isinstance(res[item], WorkerError):
            print "exception found" + repr(res[item])
            print res[item].type()
            print res[item].value()
            print "".join(res[item].formatted_tb())
            log.warn("foo %r\n%s", res[item], "".join(res[item].formatted_tb()))
            #raise res[item]

if __name__ == '__main__':
    sys.exit(main())