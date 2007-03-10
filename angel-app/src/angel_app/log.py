"""
Logger for angel-app
"""

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

author = """Paul Kremer, 2007"""

"""
This is a module that provides simple wrapping services for logging.
It is responsible for tying together possibbly different logging engines,
configuring them ...<br/>
Logfiles are in $HOME/.angel_app/log/<br/>
The directory $HOME/.angel_app/log/ will automatically get created if needed.
<p>
See the documentation of the  
<a href="http://docs.python.org/lib/module-logging.html">python logging module</a>
and  
<a href="http://twistedmatrix.com/projects/core/documentation/howto/logging.html">twisted.log</a>
for more information.
</p>
"""

import logging
import angel_app.config.config
from twisted.python import log as twistedlog

from twisted.python.filepath import FilePath
from os import environ, path, mkdir, linesep

DEBUG = False # this will start printing to the console if set to True
"""
Defaults for the logging backend (RotatingFileHandler)
"""
log_maxbytes = 1024 * 1024 # each logfile has a max of 1 MB
log_backupcount = 7        # max 7 "rotated" logfiles

loggers = {}

appname = "defaultAppname" # this string is prepended with a trailing dot to all log messages

def getLogger(area = ""):
    """
    the most important method in here. Call this to get a logger object, so
    you can log a message using one of the methods 'error' 'info' 'critical' 'debug' ...
    See the pyhton 'logging' module documentation for more information.
    Additionally, this method can be called using an additionnal parameter called 'area'.
    The area is used to tag the logged messages, so it is easier to read the log.
    The value of area really can be anyt string you like, it might make sense to use
    for example the class/module name you are in.
    In logged messages, the area appears just behind the applicaton name, prepended with a dot:
    "presenter.config" means the log message is from application presenter and area config.
    """
    if len(area) > 0:
        area = appname+ '.' + area
    else:
        area = appname
    return _getLogger(area)


def _getLogger(area = ''):
    if not loggers.has_key(area):
        loggers[area] = logging.getLogger(area)
    return loggers[area]


def getAngelLogPath():
    from angel_app.config.config import getConfig
    angelConfig = getConfig()
    
    angelLogPath = angelConfig.get("common", "logdir")
    return angelLogPath


def getAngelLogFilename():
    return getAngelLogFilenameForApp(appname)

def getAngelLogFilenameForApp(app):
    return path.join(getAngelLogPath(), app + ".log")

from logging import Filter
import re
class AngelLogFilter(Filter):
    def __init__(self, f):
        self.f = f
    def filter(self, record):
        if DEBUG: print "HIT THE FILTER"
        stringobj = str(record.msg) # this enables us to log all sorts of types, by using their string representation
        record.msg = stringobj.replace("\n", "\\n") # TODO: this is not safe enough, there might be control chars, and record.args also can contain bad data
        if record.levelno >= self.f[1]:
            if DEBUG: record.msg = "PASS FILTER" + record.msg
            return True
        else:
            if DEBUG: record.msg = "STOP FILTER" + record.msg
            return False
        return True

class AngelLogTwistedFilter(Filter):
    def __init__(self):
        self.re = re.compile("HTTPChannel,\d+,.*: (PROPFIND )|(HEAD )\/.* HTTP\/1\.1")
    def filter(self, record):
        if DEBUG: print "TWISTED LOGFILTER"
        if self.re.search(record.msg):
            return False
        else:
            return True


def initializeLogging(appname = "defaultAppname", handlers = []):
    """
    This is the single-step routine to initialize the logging system.
    """
    angel_app.log.appname = appname
    setup()
    for handler in handlers:
        enableHandler(handler)
    getReady()

def setup():
    """
    setup() creates the needed internal directory structure for logging
    (.angel_app/log/). It must be called once during bootstrap.
    """
    __configLoggerBasic()
    angelLogPath = getAngelLogPath()
    if not path.exists(angelLogPath):
        mkdir(angelLogPath)
    elif not path.isdir(angelLogPath):
        raise "Filesystem entry '%s' occupied, cannot create directory here." % angelLogPath

def enableHandler(handlername, handler = None):
    if handlername == "console":
        __addConsoleHandler()
    if handlername == "socket":
        __addSocketHandler()
    if handlername == "file":
        __addRotatingFileHandler()
    if handlername == "wx":
        handler.setLevel(logging.DEBUG) # for the console logger, we always use DEBUG!
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(name)s %(levelname)-6s %(filename)s:%(lineno)d %(message)s')
        # tell the handler to use this format
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

def getReady():
    """
    must be called after setup() and after enabling handlers with enableHandler()
    """
    
    ourTwistedLogger = getLogger("twisted")
    ourTwistedLogger.addFilter( AngelLogTwistedFilter() )
    filters = getLoggingFilters()
    for f in filters:
        logger = _getLogger(f[0])
        logger.addFilter( AngelLogFilter(f) )
        
    twistedlog.startLoggingWithObserver(logTwisted, setStdout=0)


def logTwisted(eventDict):
    """
    callback for the twisted logging engine
    """
    # TODO : beautify more... see twisted.python.log for details on how to implement that
    ourTwistedLogger = getLogger("twisted")
    # according to the twisted doc, the eventDict always has the 'isError' key set to indicate wether it is an error or not
    isError = eventDict['isError']
    # buggy twisted: sometimes it also has the eventDict-key isErr:
    if eventDict.has_key('isErr'):
        isError = eventDict['isErr']

    if eventDict.has_key('failure'):
        import string
        ourTwistedLogger.critical(eventDict.get('why') or 'Unhandled Error')
        if callable(getattr(eventDict['failure'], 'getTraceback')):
            for line in string.split(eventDict['failure'].getTraceback(), '\n'):
                #print "line: %s" % line
                ourTwistedLogger.critical(line)
        else:
            ourTwistedLogger.critical("failure has no getTraceBack() method. hmmm")
        return


    text = ""
    if eventDict.has_key("system"):
        text = eventDict["system"] + ": "
    if eventDict.has_key("message"):
        text += " ".join([str(m) for m in eventDict["message"]])

    if isError == 1:
        ourTwistedLogger.error(text)
    else:
        ourTwistedLogger.info(text)
        


def __configLoggerBasic():
    # leave this as is. It is the default root logger and goes to /dev/null
    # the way to call basicConfig() changed from version 2.3 to version 2.4
    # to be able to run in 2.3 (although with slightly messy logging), we detect this here:
    from platform import python_version_tuple
    (major,minor,patchlevel) = python_version_tuple()
    major = int(major)
    minor = int(minor)
    if (major >=2 and minor > 3 ):
        logging.basicConfig(level=logging.DEBUG, format='%(message)s', filename='/dev/null', filemode='w')
        #format='%(name)s %(asctime)s %(levelname)-8s %(message)s',
    else:
        logging.basicConfig()

def loglevelToInt(loglevel = 'NOTSET'):
    return logging._levelNames[loglevel]
#    levels = { "NOTSET": 0, "DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
#    if not levels.has_key(level):
#        raise NameError, "The given loglevel %s is not defined" % level
#    return levels[level]

def __getConfiguredLogLevel():
    AngelConfig = angel_app.config.config.getConfig()
    loglevel = AngelConfig.get('common', 'loglevel')
    return loglevelToInt(loglevel)


def __addConsoleHandler():
    # define a console Handler:
    console = logging.StreamHandler()
    console.setLevel(__getConfiguredLogLevel())
    #console.setLevel(logging.WARN) # for the console logger, we always use DEBUG!
    # set a format which is simpler for console use
    AngelConfig = angel_app.config.config.getConfig()
    formatstring = AngelConfig.get('common', 'consolelogformat', True)
    formatter = logging.Formatter(formatstring)
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the app's logger
    logging.getLogger().addHandler(console)
    #getLogger().addHandler(console)


def __addRotatingFileHandler():
    import logging.handlers # needed to instiate the RotatingFileHandler
    # define a file Handler:
    fileHandler = logging.handlers.RotatingFileHandler(getAngelLogFilename(), 'a', log_maxbytes, log_backupcount)
    fileHandler.setLevel(__getConfiguredLogLevel())
    # set a format which is simpler for console use
    AngelConfig = angel_app.config.config.getConfig()
    formatstring = AngelConfig.get('common', 'logformat', True)
    formatter = logging.Formatter(formatstring)
    # tell the handler to use this format
    fileHandler.setFormatter(formatter)    
    # add the handler to the app's logger
    logging.getLogger().addHandler(fileHandler)
    #getLogger().addHandler(fileHandler)


def __addSocketHandler():
    import logging.handlers # needed to instiate the SocketHandler
    # define a socket Handler:
    socketHandler = logging.handlers.SocketHandler('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    socketHandler.setLevel(__getConfiguredLogLevel())
    # don't bother with a formatter, since a socket handler sends the event as
    # an unformatted pickle
    # add the handler to the app's logger
    logging.getLogger().addHandler(socketHandler)
    #getLogger().addHandler(socketHandler)


def getLoggingFilters():
    """
    Reads per module loglevels from the 'logfilters' section of the
    config file.
    Levels can be: NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
    The default loglevel applies, so even if the per module 
    value is lower (==more verbosity), it won't get logged.
    This method returns a list of tuples, each of which has
    two values:
        - module name (string)
        - loglevel (int)

    Example:
    [logfilters]
    master.angel_app.admin.initializeRepository = WARN
    master.config = INFO
    master.ExternalProcessManager = ERROR
    presenter.delete = INFO
    presenter = INFO
    presenter.twisted = INFO
    provider.angel_app.resource.local.external.methods.proppatch = INFO
    """
    import re
    digits = re.compile("\d+")
    sectionname = 'logfilters'
    log = getLogger(__name__)
    from angel_app.config.config import getConfig
    angelConfig = getConfig()
    if not angelConfig.config.has_section(sectionname):
        log.warn("No section '%s' in config file, skipping" % sectionname)
        return []
    filters = []
    #print "=======LOGGING CONFIG================"
    #print "Default LOGLEVEL: " + str(__getConfiguredLogLevel())
    for logfilter in angelConfig.config.options(sectionname):
        level = angelConfig.config.get(sectionname, logfilter)
        if not digits.match(level):
            level = loglevelToInt(level)
        #print "LOGLEVEL " + str(level) + " for " + logfilter
        filters.append( [ logfilter, level] )
    #print "=======END CONFIG================"
    return filters
