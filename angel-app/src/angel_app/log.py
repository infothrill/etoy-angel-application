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
	from angel_app.config.defaults import appname
	if len(area) > 0:
		return logging.getLogger(appname+ '.' + area)
	else:
		return logging.getLogger(appname)


def getAngelHomePath():
	from angel_app.config.defaults import getAngelHomePath
	return getAngelHomePath()


def getAngelLogPath():
	logPath = path.join(getAngelHomePath(), "log")
	return logPath


def getAngelLogFilename():
	from angel_app.config.defaults import appname
	return path.join(getAngelLogPath(), appname + ".log")


from logging import Filter
class AngelLogFilter(Filter):
	def filter(self, record):
		record.msg = record.msg.replace("\n", "\\n") # TODO: this is not safe enough, there might be control chars, and record.args also can contain bad data
		return 1


def setup():
	"""
	setup() creates the needed internal directory structure for logging
	(.angel_app/log/). It must be called once during bootstrap.
	"""
	__configLoggerBasic()
	angelhomePath = FilePath(getAngelHomePath())
	if not angelhomePath.exists():
		mkdir(angelhomePath.path, 0750)
	angelLogPath = FilePath(getAngelLogPath())
	if not angelLogPath.exists():
		mkdir(angelLogPath.path, 0750)


def enableHandler(handlername):
	if handlername == "console":
		__addConsoleHandler()
	if handlername == "socket":
		__addSocketHandler()
	if handlername == "file":
		__addRotatingFileHandler()


def getReady():
	"""
	must be called after setup() and after enabling handlers with enableHandler()
	"""
	twistedlog.startLoggingWithObserver(logTwisted, setStdout=1)


def logTwisted(dict):
	"""
	callback for the twisted logging engine
	"""
	# TODO : beautify more... see twisted.python.log for details on how to implement that
	ourTwistedLogger = getLogger("twisted")
	del dict['time'] # we don't need to see the time twice in the log... the accuracy should not be a problem
	# according to the twisted doc, the dict always has the 'isError' key set to indicate wether it is an error or not
	isError = dict['isError']
	del dict['isError']
	# buggy twisted: sometimes it also has the dict-key isErr:
	if dict.has_key('printed'):
		del dict['printed']
	if dict.has_key('isErr'):
		isError = dict['isErr']
		del dict['isErr']
	if dict.has_key('why') and dict['why'] == None:
		del dict['why']

	errortext = None
	if isError == 1 and dict.has_key('failure'):
		errortext = ((dict.get('why') or 'Unhandled Error')
				+ os.linesep + dict['failure'].getTraceback())

	text = ""
	if dict.has_key("system"):
		text = dict["system"] + ": "
	if dict.has_key("message"):
		text += " ".join([str(m) for m in dict["message"]])
	
	if isError == 1:
		ourTwistedLogger.error(text)
		if not errortext == None:
			ourTwistedLogger.critical(errortext)
	else:
		ourTwistedLogger.info(text)


def __configLoggerBasic():
	# leave this as is. It is the default root logger and goes to /dev/null
    logging.basicConfig(level=logging.DEBUG, format='%(message)s', filename='/dev/null', filemode='w')
					#format='%(name)s %(asctime)s %(levelname)-8s %(message)s',
					

def __getConfiguredLogLevel():
	AngelConfig = angel_app.config.config.getConfig()
	loglevel = AngelConfig.get('common', 'loglevel')
	return logging._levelNames[loglevel] # this is a bit ugly, we need to map a configured string to a loglevel int


def __getConfiguredLogFormat():
	AngelConfig = angel_app.config.config.getConfig()
	return AngelConfig.get('common', 'logformat', True)


def __addConsoleHandler():
    # define a console Handler:
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG) # for the console logger, we always use DEBUG!
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)s %(levelname)-6s %(filename)s:%(lineno)d %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    #console.addFilter(AngelLogFilter())
    # add the handler to the app's logger
    logging.getLogger().addHandler(console)
    #getLogger().addHandler(console)


def __addRotatingFileHandler():
    import logging.handlers # needed to instiate the RotatingFileHandler
    # define a file Handler:
    from angel_app.config.defaults import log_maxbytes, log_backupcount
    fileHandler = logging.handlers.RotatingFileHandler(getAngelLogFilename(), 'a', log_maxbytes, log_backupcount)
    fileHandler.setLevel(__getConfiguredLogLevel())
    # set a format which is simpler for console use
    formatter = logging.Formatter(__getConfiguredLogFormat())
    # tell the handler to use this format
    fileHandler.setFormatter(formatter)	
    fileHandler.addFilter(AngelLogFilter())
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

