"""

Defaults for the angel-app. This lists values that influence the way
angel-app works, but which are not user-configurable.

"""

"""
The listen port that we expect from other peers
"""
publiclistenport = 9999


"""
the clones of the local repository

tuples of (host names  IP addresses, port numbers) of the master (default) nodes.
the port numbers are optional and default to the value defined in config.external.py
"""
peers = [
           ("localhost", 9999),
           ("missioneternity.org", 9999)
           ]
