"""

Defaults for the angel-app. This contains values/methods that influence the way
angel-app works, but which are _not_ user-configurable. They may be dynamic though!

"""

"""
The listen port that we expect from other peers
"""
publiclistenport = 9999

"""
The name of the currently running application. This must be set during bootstrapping!
(e.g. to presenter/provider ...) It is currently used for logging and pidfiles.
"""

appname = "defaultAppname"

"""
This is the path leading to the individual programs of angel-app, e.g.
presenter, provider and maintainer. This config key should be set during
bootstrap, and _before_ switching to daemon mode, so that the master
process can find the programs.
"""

binpath = ""

"""
Defaults for the logging backend (RotatingFileHandler)
"""
log_maxbytes = 1024 * 1024 # each logfile has a max of 1 MB
log_backupcount = 7        # max 7 "rotated" logfiles


"""
the clones of the local repository

tuples of (host names  IP addresses, port numbers) of the master (default) nodes.
the port numbers are optional and default to the value defined in config.external.py
"""
peers = [
           ("localhost", 9999),
           ("missioneternity.org", 9999)
           ]

def getAngelHomePath():
	from os import environ, path
	home = environ["HOME"]
	return path.join(home, ".angel_app");
