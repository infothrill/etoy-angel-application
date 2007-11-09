"""
Module providing config file facilities through configObj

Sample usage for getting config values:

    cfg = getConfig()
    if cfg.has_section('common'):
        cfg.get('common', 'logdir')
        # or:
        cfg.config['common']['logdir']

Sample usage for setting values:

    cfg = getConfig()
    cfg.container['section']['path'] = '/tmp/'

To save:

    cfg.commit()

"""
__author__ = "Paul Kremer"

import unittest
import os

from angel_app.contrib.cfgobj.configobj import ConfigObj
from angel_app.contrib.cfgobj.validate import Validator

def isValidConfig(cfgObj):
    """
    Method to validate the parsed config against the config_spec from _configspec_lines()
    
    See the configObj documentation for further information
    """
    validation_result = cfgObj.validate(Validator(), preserve_errors=True)
    if not validation_result == True:
        raise Exception, "The configuration failed to be validated: %s" % (validation_result)
    return True

def getDefaultConfigObj():
    """
    Return a configobj instance with default values
    """
    from logging.handlers import DEFAULT_TCP_LOGGING_PORT

    #some defaults have to be computed first:
    defaults = {
            "angelhome" : os.path.join(os.environ["HOME"], ".angel-app"),
            "repository" : os.path.join(os.environ["HOME"], ".angel-app", "repository"),
            "keyring" : os.path.join(os.environ["HOME"], ".angel-app", "keyring"),
            "logdir" : os.path.join(os.environ["HOME"], ".angel-app", "log"),
            "loglistenport" : str(DEFAULT_TCP_LOGGING_PORT),
            "logformat" : '%(asctime)s %(levelname)-6s %(name)-20s - %(message)s',
            "consolelogformat" : '%(levelname)-6s %(name)-20s - %(message)s',
                }
    
    # create a string for the default config:
    defaultconfig_txt = """
    [common]
    angelhome = "%(angelhome)s"
    repository =  "%(repository)s"
    keyring = "%(keyring)s"
    logdir = "%(logdir)s"
    maxclones = 5
    loglevel = INFO
    loglistenport = %(loglistenport)s
    logformat = '%(logformat)s'
    consolelogformat = '%(consolelogformat)s'
    
    [presenter]
    enable = True
    listenPort = 6222
    listenInterface = localhost
    
    [provider]
    enable = True
    listenPort = 6221
    useIPv6 = False
    
    [maintainer]
    enable = True
    initialsleep = 1 # it's nice to be fast on the first traversal
    treetraversaltime = 86400 # we want a tree traversal to take about one day after the initial sync
    maxsleeptime = 100
    nodename = localhost
    
    [mounttab]
    "http://missioneternity.org:6221/" = "MISSION ETERNITY"

    """ % ( defaults )

    cfg = ConfigObj(defaultconfig_txt.splitlines(), configspec = _configspec_lines())
    cfg.interpolation = False
    assert isValidConfig(cfg) == True
    return cfg

def _configspec_lines():
    """
    Returns the textual config specification for use in validation and type-conversion
    """
    config_spec = """
    [common]
    angelhome = string
    repository =  string
    keyring = string
    logdir = string
    maxclones = integer(min=1, max=20)
    loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL', default='INFO')
    loglistenport = integer(min=1025)
    logformat = string
    consolelogformat = string
    
    [presenter]
    enable = boolean(default=True)
    listenPort = integer(min=1025)
    listenInterface = string
    
    [provider]
    enable = boolean(default=True)
    listenPort = integer(min=1025)
    useIPv6 = boolean(default=False)
    
    [maintainer]
    enable = boolean(default=True)
    initialsleep = integer(min=1)
    treetraversaltime = integer(min=600)
    maxsleeptime = integer(min=2)    
    nodename = string
    """
    return config_spec.splitlines()

def getDefaultConfigFilePath():
    """
    Returns the filename pointing to the default configuration file.
    """
    home = os.environ["HOME"]
    return os.path.join(home, ".angelrc");

configObject = None # holder for a ConfigWrapper object
def getConfig(configfilename = getDefaultConfigFilePath()):
    """
    Implements a singleton for getting a ConfigWrapper object

    @return: ConfigWrapper instance
    """
    global configObject
    
    if configObject == None:
        if configfilename is None: configfilename = getDefaultConfigFilePath()
        configObject = ConfigWrapper(configfilename)
        if (not os.path.isfile(configfilename)): # if config was non-existant, save it
            configObject.commit()
    return configObject


configObj = None # holder for a configObj object
def getConfigObj(configfilename = getDefaultConfigFilePath()):
    """
    Implements a singleton for getting a configObj object with user values and default values
    for unconfigured options.

    @return: configObj instance
    """
    global configObj
    if configObj == None:
        user_config = ConfigObj(configfilename, configspec = _configspec_lines())
        user_config.interpolation = False
        configObj = getDefaultConfigObj()
        configObj.merge(user_config)
        assert isValidConfig(configObj) == True
    return configObj


class ConfigWrapper(object):
    """
    The only purpose of this class is to serve as a compatibility interface for our old
    config class which provided the get() getint() and getboolean() methods.

    <p>
    In angel-app, you will most probably not instantiate this class
    directly, but use the method "getConfig()" in this module.
    </p>
    """
    def __init__(self, configfilepath = getDefaultConfigFilePath()):
        self.configfilename = configfilepath
        self.container = getConfigObj(configfilepath)

    def has_section(self, section):
        return self.container.has_key(section)

    def get(self, *args):
        assert len(args) > 0
        temp = self.container[args[0]]
        if len(args) > 1:
            for arg in args[1:]:
                temp = temp[arg]
        return temp

    def getint(self, *args):
        value = self.get(*args)
        return int(value)
        
    def getboolean(self, *args):
        value = self.get(*args)
        return bool(value)

    def getConfigFilename(self):
        return self.configfilename
    
    def commit(self):
        self.container.write(open(self.configfilename, 'w'))


class ConfigTestCase(unittest.TestCase):
    
    def setUp(self):
        unittest.TestCase.setUp(self)
    
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        
    def testDefaultConfigObj(self):
        default_config = getDefaultConfigObj()
        sections = default_config.keys()
        # just make sure we can do a 2-level depth loop into sections/values:
        for s in sections:
            for ss in default_config[s].keys():
                default_config[s][ss]
        
    def testGetRealConfigObj(self):
        self.assertTrue(os.path.isfile(getDefaultConfigFilePath()))
        config = ConfigObj(getDefaultConfigFilePath())
        config.keys()
        
    def testGetMergedConfigObj(self):
        config = getConfigObj()
        self.assertFalse(config == None)
        config.keys()
        
    def testConfigCompat(self):
        configObj = getConfigObj()
        self.assertTrue(type(configObj['provider']['listenPort']) == type(1))
        config = getConfig()
        self.assertTrue(config != None)
        self.assertTrue(type(config.get('provider', 'listenPort')) == type(1))
        
if __name__ == '__main__':
    unittest.main()

