# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

"""Directory listing."""

# system imports
import os
import urllib
import stat
import time

# twisted imports
from twisted.web2 import resource, http, http_headers

from angel_app.config import config
nodename = config.getConfig().get("maintainer","nodename")

def formatFileSize(size):
    if size < 1024:
        return '%i' % size
    elif size < (1024**2):
        return '%iK' % (size / 1024)
    elif size < (1024**3):
        return '%iM' % (size / (1024**2))
    else:
        return '%iG' % (size / (1024**3))

def formatClones(path):
    from angel_app.resource.local import basic
    
    try:
        return ", \n".join([              
                   '<a href="' + `clone`+ '">' + clone.host + '</a>'
                   for clone in basic.Basic(path).clones()])
    except:
        return ""


def getStatistics():  
    from angel_app.tracker.connectToTracker import connectToTracker
    stats = connectToTracker()
    return "<br/>".join(stats.split("\n"))

def showStatistics():
    return "<h2>Global Network</h2><p>The following global statistics are available for the ANGEL APPLICATION network: <br/>" + getStatistics() + "</p>" 

def htmlHead(title):
    return """
<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <title>ANGEL APPLICATION: %s</title>
    <link href="http://www.missioneternity.org/themes/m221e/css/main.css" rel="stylesheet" type="text/css" media="all" />
    <link rel="shortcut icon" href="http://www.missioneternity.org/themes/m221e/buttons/m221e-favicon.ico" type="image/x-icon" />
    <style type="text/css">
        .even-dir { background-color: #ffffff }
        .even { background-color: #ffffff }
        .odd-dir {background-color: #eeeeee }
        .odd { background-color: #eeeeee }
        td { vertical-align: top;}
        th { white-space:nowrap; text-align:left; padding-right: 10px;}
    </style>
</head>""" % title

def showClones(path):
    return "<h2>Resource Network</h2><p>Replicas of this resource have last been seen at the following locations: <br/>" + formatClones(path) + "</p>"

def showFile(even, link, linktext, size, lastmod, type):
    even = even and "even" or "odd"
    s = """
<tr class="%s">
    <td>
        <a href="%s">%s</a>
    </td>
    <td align="right">%s</td>
    <td>%s</td>
    <td>%s</td>
</tr>
""" % (even, link, linktext, size, lastmod, type)    
    return s

def showFileListing(data_listing):
    s = """
<div id="bilder">
    <div style="line-height: 1.6em; padding: 0 0 0 35px; margin:0 0 10px 0;">
        <table  style="background-color: #ffffff;" width="480px;">
        <tr>
            <th>Filename</th>
            <th>Size</th>
            <th>Last Modified</th>
            <th>File Type</th>
        </tr>"""
    even = False
    for row in data_listing:
        s += '\n' + showFile(even, row["link"], row["linktext"], row["size"], row["lastmod"], row["type"])
        even = not even               
    s += "\n</table></div></div>"
    return s

def showDirectoryListing(linkList):
    return "<p>Directory listing for %s</p>" % linkList

def showBlurb(linkList, hostName):
    return """
<p>%s</p>
<p>
You are viewing a directory listing of the ANGEL APPLICATION,
an autonomous peer-to-peer file system developed for MISSION ETERNITY.
</p>
<p>
Much like <a href="http://freenetproject.org/">freenet</a>, it decouples the storage 
process from the physical storage medium by embedding data in a social network. 
Unlike freenet, the primary goal of the ANGEL APPLICATION is not anonymity, but 
data preservation.
</p>
<p>
This node is hosted on %s. 
</p>
""" % (linkList, hostName)

def showNavi():
    return """
<div id="topnavi">
    <ul>
        <li><a href="http://missioneternity.org/cult-of-the-dead/">MISSION ETERNITY</a></li>
        <li><a href="http://missioneternity.org/data-storage/">DATA STORAGE</a></li>
        <li><a href="http://missioneternity.org/angel-application/">ANGEL APPLICATION</a></li>
    </ul>
</div>
"""

class DirectoryLister(resource.Resource):
    def __init__(self, pathname, dirs=None,
                 contentTypes={},
                 contentEncodings={},
                 defaultType='text/html'):
        self.contentTypes = contentTypes
        self.contentEncodings = contentEncodings
        self.defaultType = defaultType
        # dirs allows usage of the File to specify what gets listed
        self.dirs = dirs
        self.path = pathname
        resource.Resource.__init__(self)

    def data_listing(self, request, data):
        if self.dirs is None:
            directory = os.listdir(self.path)
            directory.sort()
        else:
            directory = self.dirs

        files = []

        directory.sort()

        directory = [item for item in directory if not item.startswith(".")]

        for path in directory:
            url = urllib.quote(path, '/')
            fullpath = os.path.join(self.path, path)
            try:
                st = os.stat(fullpath)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode):
                url = url + '/'
                files.append({
                    'link': url,
                    'linktext': path + "/",
                    'size': '',
                    'type': '-',
                    'lastmod': time.strftime("%Y-%b-%d %H:%M", time.localtime(st.st_mtime)),
                    'clones': formatClones(fullpath)
                    })
            else:
                from twisted.web2.static import getTypeAndEncoding
                mimetype, dummyencoding = getTypeAndEncoding(
                    path,
                    self.contentTypes, self.contentEncodings, self.defaultType)
                
                filesize = st.st_size
                files.append({
                    'link': url,
                    'linktext': path,
                    'size': formatFileSize(filesize),
                    'type': mimetype,
                    'lastmod': time.strftime("%Y-%b-%d %H:%M", time.localtime(st.st_mtime)),
                    'clones': formatClones(fullpath)
                    })

        return files

    def __repr__(self):  
        return '<DirectoryLister of %r>' % self.path
        
    __str__ = __repr__


    def render(self, request):
        title = "Directory listing for %s" % urllib.unquote(request.path)
        # TODO we need a better way to transform between url paths and file paths...
        pathSegments = ["/"] + urllib.unquote(request.path.strip("/")).split(os.sep)
        linkTargets = ["/"]
        accumulated = "/"
        for segment in pathSegments[1:]:
            accumulated += urllib.quote(segment) + "/"
            linkTargets.append(accumulated)
        linkList = '<a href="%s">%s</a>' % ("/", "/")  + \
            "/".join(['<a href="%s">%s</a>' % (linkTarget, pathSegment) 
                    for (linkTarget, pathSegment) in 
                    zip(linkTargets[1:], pathSegments[1:])
                    ])
    
        s= """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">"""
        s += htmlHead(title)
        s += """
        <body class="bg-still3">
        <div id="metanavi"><a href="http://www.etoy.com/">etoy.CORPORATION</a> 2007</div>
        <div id="content">
        <h1 class="rechts">
            <a href="http://www.missioneternity.org/">
                <img src="http://www.missioneternity.org/themes/m221e/images/m221e-logo2-o.gif" alt="" border="0" />
            </a>
        </h1>
              
        <h1>Directory Listing</h1>"""
        s += '\n' + showBlurb(linkList, nodename)
        s += "\n<br/><br/>"     
        s += showClones(self.path)
        s += "\n<br/><br/>"  
        s += showStatistics()
        s += "\n</div>"
        s += '\n' + showNavi()
        s += showFileListing(self.data_listing(request, None))   
        s += "\n</body></html>"
        response = http.Response(200, {}, s)
        response.headers.setHeader("content-type", http_headers.MimeType('text', 'html'))
        return response

__all__ = ['DirectoryLister']
