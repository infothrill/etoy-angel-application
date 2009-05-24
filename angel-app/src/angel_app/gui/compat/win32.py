"""
Module for Windows specific methods
"""

import subprocess

def showRepositoryInFilemanager(interface, port):
    subprocess.call( ["start", "http://%s:%s/" % (interface, str(port)) ] )

def showURLInBrowser(url):
    subprocess.call( ["start", str(url) ] )
