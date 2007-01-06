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
See the documentation of the python logging module for more information.
</p>
"""

import logging
from twisted.python import log as twistedlog

from twisted.python.filepath import FilePath
from os import environ, path, mkdir

# twisted logging:
#http://twistedmatrix.com/projects/core/documentation/howto/logging.html

# python logging:
# http://docs.python.org/lib/module-logging.html

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

def setup():
	"""
	setup() creates the needed internal directory structure for logging
	(.angel_app/log/). It must be called once during bootstrap.
	"""
	angelhomePath = FilePath(getAngelHomePath())
	if not angelhomePath.exists():
		mkdir(angelhomePath.path, 0750)
	angelLogPath = FilePath(getAngelLogPath())
	if not angelLogPath.exists():
		mkdir(angelLogPath.path, 0750)

def __configTwistedLogger():
	twistedlog.addObserver(logTwisted)

def logTwisted(dict):
	"""
	callback for the twisted logging engine
	"""
	# TODO : here we could take the received dict object and beautify the output a lot...
	ourTwistedLogger = getLogger("twisted")
	ourTwistedLogger.info(dict)


def __configLoggerBasic():
	setup()
	# leave this as is. It is the default root logger and goes to /dev/null
	logging.basicConfig(level=logging.DEBUG,
					#format='%(name)s %(asctime)s %(levelname)-8s %(message)s',
					format='%(message)s',
                    filename='/dev/null',
                    filemode='w')

def __addConsoleHandler(area = ""):
	# define a console Handler:
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)
	# set a format which is simpler for console use
	formatter = logging.Formatter('%(name)-20s: %(levelname)-8s %(message)s')
	# tell the handler to use this format
	console.setFormatter(formatter)
	# add the handler to the app's logger
	getLogger(area).addHandler(console)

def __addRotatingFileHandler(area = ""):
	import logging.handlers # needed to instiate the RotatingFileHandler
	# define a file Handler:
	from angel_app.config.defaults import log_maxbytes, log_backupcount
	fileHandler = logging.handlers.RotatingFileHandler(getAngelLogFilename(), 'a', log_maxbytes, log_backupcount)
	fileHandler.setLevel(logging.DEBUG)
	# set a format which is simpler for console use
	formatter = logging.Formatter('%(name)-20s %(asctime)s %(levelname)-8s %(message)s')
	# tell the handler to use this format
	fileHandler.setFormatter(formatter)	
	# add the handler to the app's logger
	getLogger(area).addHandler(fileHandler)

def __addSocketHandler(area = ""):
	import logging.handlers # needed to instiate the SocketHandler
	# define a socket Handler:
	socketHandler = logging.handlers.SocketHandler('localhost',
                    logging.handlers.DEFAULT_TCP_LOGGING_PORT)
	socketHandler.setLevel(logging.DEBUG)
	# don't bother with a formatter, since a socket handler sends the event as
	# an unformatted pickle
	# add the handler to the app's logger
	getLogger(area).addHandler(socketHandler)

def __configLoggerForForeground():
	__configLoggerBasic()
	__addConsoleHandler()
	# also log to file, even if in console foreground mode:
	__addRotatingFileHandler()
	__configTwistedLogger()


def __configLoggerForDaemon():
	__configLoggerBasic()
	__addRotatingFileHandler()
	__addSocketHandler()
	twistedlog.startLogging(open('/dev/null', 'w'), setStdout=False)
	__configTwistedLogger()

