"""
Module for Mac OS X specific methods
"""

import os
import common
import subprocess

APPLESCRIPT_PATH=os.path.join(common.getResourcePath(), "applescript")

def showRepositoryInFilemanager(interface, port):
    script = os.path.join(APPLESCRIPT_PATH, "mount_repository.applescript")
    subprocess.call( ["/usr/bin/osascript", str(script), str(interface), str(port)] )

def showURLInBrowser(url):
    subprocess.call( ["open", str(url)] )
