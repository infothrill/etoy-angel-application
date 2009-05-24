
#for (int count = 0; count < browsers.length && browser == null; count++)
#if (Runtime.getRuntime().exec(new String[] {"which", browsers[count]}).waitFor() == 0) browser = browsers[count]; 
#if (browser == null) throw new Exception("Could not find web browser"); else Runtime.getRuntime().exec(new String[] {browser, url}); } }
#catch (Exception e) { JOptionPane.showMessageDialog(null, errMsg + ":\n" + e.getLocalizedMessage()); } } }


"""
Module for Unix/Linux specific methods
"""

import os
import subprocess

def _which (filename):
    """
    emulates the `which` command line tool
    """
    if not os.environ.has_key('PATH') or os.environ['PATH'] == '':
        p = os.defpath
    else:
        p = os.environ['PATH']

    pathlist = p.split (os.pathsep)

    for path in pathlist:
        f = os.path.join(path, filename)
        if os.access(f, os.X_OK):
            return f
    return None

def _findAvailableTool( tools ):
    for p in tools:
        tool = _which(p)
        if not tool == None:
            return tool
    return None

def showRepositoryInFilemanager(interface, port):
    # Notes on popular X11 filemanagers:
    #  - konqueror can open urls with protocol "webdav"
    #  - nautilus can open urls with protocol "dav"
    fmanager = _findAvailableTool([ "nautilus", "konqueror", "dolphin" ])
    if fmanager == None:
        return # TODO : alert user that no web-browser was found!
    elif fmanager == "nautilus":
        subprocess.call( [fmanager, "dav://%s:%s/" % (str(interface), str(port)) ] )
    elif fmanager == 'konqueror':
        subprocess.call( [fmanager, "webdav://%s:%s/" % (str(interface), str(port)) ] )
    else:
        subprocess.call( [fmanager, "http://%s:%s/" % (str(interface), str(port)) ] ) # no idea how dolphin handles this

def showURLInBrowser(url):
    browser = _findAvailableTool([ "xdg-open", "x-www-browser", "mozilla-firefox", "firefox", "iceweasel", "konqueror", "epiphany", "mozilla", "netscape", "opera"])
    if browser == None:
        return # TODO : alert user that no web-browser was found!
    subprocess.call( [browser, str(url)] )

