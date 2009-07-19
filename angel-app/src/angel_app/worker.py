
from angel_app.config.config import getConfig
from angel_app.log import getLogger

log = getLogger(__name__)
cfg = getConfig()

def dowork(function, items, children = 5):
    """
    High level method to delegate work to a function.
    This is essentially a hack to allow using optimized parallelization
    as well as sequential execution, based on the configuration
     
    @param function:
    @param items:
    @param children:
    """
    if cfg.getboolean('common', 'workerforking'):
        log.debug("dowork(): PARALLEL execution with %i children", children)
        from angel_app.contrib import delegate
        return delegate.parallelize(function, items, children)
    else:
        log.debug("dowork(): SEQUENTIAL execution")
        res = {}
        for item in items:
            try:
                res[item] = function(item)
            except Exception, e:
                res[item] = e
        return res
