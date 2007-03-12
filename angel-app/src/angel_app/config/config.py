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

from os import environ, path
from ConfigParser import SafeConfigParser
import angel_app.log

configObject = None # holder for a Config object

def getConfig(configfile = None):
	"""
	Returns an instance of Config()
	"""
	global configObject
	if configObject == None:
		configObject = Config(configfile)
	return configObject

class Config:
    """
    This is a basic configuration engine that provides access to the 
    configuration file of angel-app. In case there is no config file,
    this class will create one with default values on __del__. The path
    to the config file is currently restricted to $HOME/.angelrc.
    Comment lines in the config file will get stripped off if it is
    rewritten. The directory $HOME/.angel-app will automatically get
    created if needed.

	<p>
	In angel-app, you will most probably not instantiate this class
    directly, but use the routine "getConfig()" in this module.
	</p>

    <p>
    See the documentation of the python SafeConfigParser module for
    information on the configuration file syntax.
    </p>
    """

    def __init__(self, configfilepath = None):
        self.cfgvars = {}
        if configfilepath == None:
            self.cfgvars["mainconfigfile"] = self.getDefaultConfigFilePath()
        else:
            self.cfgvars["mainconfigfile"] = configfilepath

        self.config = SafeConfigParser()
        self.config.optionxform = str # overwrite method to remain case sensitive
        self.config.read(self.cfgvars["mainconfigfile"])
        self.bootstrapping = True
		#dump entire config file (debug)
		#for section in self.config.sections():
		#	getLogger("config").debug(section)
		#	for option in self.config.options(section):
		#		getLogger("config").debug(" " + option + "=" + self.config.get(section, option))

    def getDefaultConfigFilePath(self):
        home = environ["HOME"]
        return path.join(home, ".angelrc");

    def getConfigFilename(self):
        return self.cfgvars["mainconfigfile"]

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
                                    "angelhome": path.join(environ["HOME"], ".angel-app"),
                                    "repository": path.join(environ["HOME"], ".angel-app", "repository"),
                                    "keyring": path.join(environ["HOME"], ".angel-app", "keyring"),
                                    "logdir": path.join(environ["HOME"], ".angel-app", "log"),
                                    "maxclones": str(5),
									"loglevel": "INFO",
                                    # FIXME: %(funcName)s is only available in Python 2.5 ;-(
                                    # also, for some reason, macpython always shows __init__.py as filename, so we leave it off ( %(filename)s:%(lineno)d )
                                    "logformat": '%(asctime)s %(levelname)-6s %(name)-20s - %(message)s',
                                    "consolelogformat": '%(levelname)-6s %(name)-20s - %(message)s',
									}, 
                         "presenter": { "listenport": "6222", "listeninterface": "127.0.0.1" }, 
						 "provider" : { "listenport": "6221" },
						 "maintainer" : {
                                         # it's nice to be fast on the first traversal
                                         "initialsleep": "1",
                                         # we want a tree traversal to take about one day after the initial synch
                                         "treetraversaltime" : str(24 * 3600),
                                         "maxsleeptime" : str(100)
                                         }
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
            self.commit()

    def __checkOption(self, section, key):
        if not self.config.has_option(section, key):
            if not self.__getDefaultValue(section, key):
                raise NameError, "ConfigError: Section '"+section+"' has no option '"+key+"' and there is no default value available"
            else:
                self.config.set(section, key, self.__getDefaultValue(section, key)) 
                self.commit()

    def commit(self):
        """
        Commits the current values of the config object to the config
        file. This method is currently called automatically whenever a
        configuration value is changed through set/get. We do not
        implement this in the destructor, because in the destructor we
        cannot be sure about which stuff is already garbage collected
        during shutdown and so it might fail there.
        """
        if self.bootstrapping:
            return
        configfilePath = self.cfgvars["mainconfigfile"]
        if not path.exists(configfilePath):
            angel_app.log.getLogger("config").info("Creating a new, empty config file in '"+configfilePath+"'")
        angel_app.log.getLogger("config").info("committing the config file to '"+configfilePath+"'")
        from angel_app.singlefiletransaction import SingleFileTransaction
        t = SingleFileTransaction()
        f = t.open(configfilePath, 'w')
        self.config.write(f)
        f.close()
        t.commit()