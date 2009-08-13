"""
This module provides methods to delegate work to be done.
This supposedly provides a layer of indirection for the actual implementation
of workers.
For now, this code can 
"""

import sys

from angel_app.config.config import getConfig
from angel_app.log import getLogger

log = getLogger(__name__)
cfg = getConfig()

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
    return delegate.parallelize(function, items, children)

def serialwork(function, items, children = 5):
    "run function on each member of items in a serial fashion"
    log.debug("serialwork(): sequential execution for %i tasks", len(items))
    res = {}
    for item in items:
        try:
            res[item] = function(item)
        except Exception, e:
            res[item] = e
    return res

def main():
    """
    main method for testing only
    """
    from angel_app.log import initializeLogging
    initializeLogging('shell', ['console'])
    items = [1, 6]
    def testmethod(i):
        "will raise an exception if i > 5"
        if i > 5:
            raise Exception, "Test"
        return i
    res = dowork(testmethod, items)
    for item in res:
        if type(res[item]) != type(1):
            print type(res[item])
            print "class:" + res[item].__class__.__name__
            print res[item]
            #log.debug("test", exc_info = res[item])
        #if isinstance(res[item], object):
        #    print "isinstance"
        if isinstance(res[item], Exception):
            log.debug("exception found")
            raise res[item]
        print item

if __name__ == '__main__':
    sys.exit(main())