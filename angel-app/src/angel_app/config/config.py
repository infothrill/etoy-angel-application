"""
Basic configuration getter for angel-app 
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

author = """Paul Kremer, 2006"""

from os import environ, path, mkdir
from ConfigParser import SafeConfigParser
from twisted.python.filepath import FilePath
import angel_app.log

configObject = None # holder for a Config object

def getConfig():
	"""
	Returns an instance of Config()
	"""
	global configObject
	if configObject == None:
		configObject = Config()
	return configObject

class Config:
    """
    This is a basic configuration engine that provides access to the configuration
    file of angel-app. In case there is no config file, this class will create one
    with default values on __del__. The path to the config file is currently
    restricted to $HOME/.angel_app/config
    Comment lines in the config file will get stripped off if it is rewritten.
    The directory $HOME/.angel_app will automatically get created if needed.

	<p>
	In angel-app, you will most probably not instantiate this class directly,
	but use the routine "getConfig()" in this module.
	</p>

    <p>
    See the documentation of the python SafeConfigParser module for information
    on the configuration file syntax.
    </p>
    """

    def __init__(self):
		self.__needscommit = False
		self.cfgvars = {}
		from angel_app.config.defaults import getAngelHomePath
		self.cfgvars["angelhome"] = getAngelHomePath()
		self.cfgvars["mainconfigfile"] = path.join(self.cfgvars["angelhome"], "config")

		self.config = SafeConfigParser()
		self.config.read(self.cfgvars["mainconfigfile"])
		#dump entire config file (debug)
		#for section in self.config.sections():
		#	getLogger("config").debug(section)
		#	for option in self.config.options(section):
		#		getLogger("config").debug(" " + option + "=" + self.config.get(section, option))

    def get(self, section, key, raw = False):
        self.__checkGetter(section, key)
        val = self.config.get(section, key, raw)
        angel_app.log.getLogger("config").debug("get(%s, %s) returns '%s'", section, key, val)
        return val

    def getint(self, section, key):
        self.__checkGetter(section, key)
        val = self.config.getint(section, key)
        angel_app.log.getLogger("config").debug("getint(%s, %s) returns '%d'", section, key, val)
        return val

    def getboolean(self, section, key):
        self.__checkGetter(section, key)
        val = self.config.getboolean(section, key)
        angel_app.log.getLogger("config").debug("getboolean(%s, %s) returns '%s'", section, key, val)
        return val

    def __checkGetter(self, section, option):
        self.__checkSection(section)
        self.__checkOption(section, option)

    def __isAllowedSection(self, section):
        allowedSections = ["presenter", "common", "maintainer", "provider"]
        if not section in allowedSections:
            return False
        else:
            return True

    def __getDefaultValue(self, section, key):
        """
        Attention:
          - all keys must be lower case!
          - all values in the dictionary defaultValues must be of type string
        """
        s = section.lower()
        k = key.lower()
        defaultValues = {
                         "common" : {
									"repository": path.join(self.cfgvars["angelhome"], "repository"),
									"loglevel": "DEBUG",
									"logformat": '%(name)-20s %(asctime)s %(levelname)-6s %(filename)s:%(lineno)d %(message)s',
									}, 
                         "presenter": { "listenport": "9998", "listeninterface": "127.0.0.1" }, 
						 "provider" : { "listenport": "9999" }, 
						 "maintainer" : { "peers": "localhost:9999" }
                         }
        if k not in defaultValues[s]:
            return False
        else:
            return defaultValues[s][k]

    def __checkSection(self, section):
        if not self.__isAllowedSection(section):
            raise NameError, "ConfigError: Section name '"+section+"' is not allowed"
        if not self.config.has_section(section):
            self.config.add_section(section)
            self.__needscommit = True

    def __checkOption(self, section, key):
        if not self.config.has_option(section, key):
            if not self.__getDefaultValue(section, key):
                raise NameError, "ConfigError: Section '"+section+"' has no option '"+key+"' and there is no default value available"
            else:
                self.config.set(section, key, self.__getDefaultValue(section, key)) 
                self.__needscommit = True

    def __del__(self):
        if self.__needscommit:
            configfilePath = FilePath(self.cfgvars["mainconfigfile"])
            angelhomePath = FilePath(self.cfgvars["angelhome"])
            if not angelhomePath.exists():
                mkdir(angelhomePath.path, 0750)
            if not configfilePath.exists():
                angel_app.log.getLogger("config").info("Creating a new, empty config file in '"+configfilePath.path+"'")
            angel_app.log.getLogger("config").info("committing the config file to '"+self.cfgvars["mainconfigfile"]+"'")
            f = open(self.cfgvars["mainconfigfile"], 'w')
            self.config.write(f)
