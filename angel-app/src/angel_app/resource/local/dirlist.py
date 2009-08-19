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

from angel_app.version import getVersionString
from angel_app.tracker.connectToTracker import connectToTracker
from angel_app.config.config import getConfig
nodename = getConfig().get("maintainer","nodename")

CSS = """
<style type="text/css">
<!--
html { height: 100% } 
body {
    min-height: 101%;
    background-color: #ffffff;
    font-family: Arial, Helvetica, SunSans-Regular, sans-serif;
    color:#343434;  
    padding:0;
    margin: 0;
    border-top: #ff6600 solid 3px;
}

a { color:#ff6600;  text-decoration: none; }
a:visited {color:#ff6600;}
a:hover {color: #444444;}
a:active { color:#000000;}

h1 {font-weight: normal;}
h2 {font-weight: normal;}
h3 {font-weight: normal;}
h4 {font-weight: normal;}

#content {
    min-height: 100%; 
    width: 90%;
    padding: 20px 0; 
    margin: 0 auto;
    background-color: #ffffff;
}

h1 {
    padding: 0 15px;
    margin:0 0 20px 0;
}
h2, h3, h4 {
    padding: 0 15px;
    margin:0 0 5px 0;
}
p {
    padding: 0 15px;
    margin:0 0 10px 0;
}

#content li {
    padding: 0 15px 0 0px;
    margin: 0;
}

.center{ text-align:center;}
.rechts{ text-align:right;}

code, pre {
  font-family: Courier, "Courier New", monospace;
}

table#angel-listing {
   font-family: Courier, "Courier New", monospace;
   margin: 0 20px 15px 0;
   padding: 5px;
   border-bottom:1px solid #555;
   width: 100%;
}

table#angel-listing td { padding:2px; padding-right:8px; }
table#angel-listing td a { color:#ff6600;  text-decoration: none; }
table#angel-listing td a:visited {color:#444;}
table#angel-listing td a:hover {color: #444444;}
table#angel-listing td a:active { color:#000000;}

tr.even { background-color: #ffffff }
tr.odd { background-color: #eeeeee }
-->
</style>
"""

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
                   '<a href="' + repr(clone)+ '">' + clone.host + '</a>'
                   for clone in basic.Basic(path).clones()])
    except:
        return ""

_STATISTICS_CACHE = [0, ""] # timestamp, buffer
def getStatistics():
    now = time.time()
    # query the tracker max once per hour:
    if _STATISTICS_CACHE[0] + 3600 < now:
        _STATISTICS_CACHE[0] = now
        _STATISTICS_CACHE[1] = connectToTracker()
    return "<br/>".join(_STATISTICS_CACHE[1].split("\n"))

def showStatistics():
    return """<p>%s</p>""" % getStatistics()

def showDisclaimer():
    return """<p class="disclaimer">
DISCLAIMER: Lifetime estimate assumes:
(i) Availability of digital communication, the absence of 
nuclear wars, major meteorite impacts and lethal pandemics. 
(ii) Maintenance of the ANGEL APPLICATION by etoy and
its contributors. 
<br/>
Please help us make these assumptions hold, by becoming an
<a href="http://www.etoy.com/fundamentals/etoy-share/">etoy.INVESTOR</a>.
</p>"""

def htmlHead(title):
#    <link href="http://www.missioneternity.org/themes/m221e/css/angel-app.css" rel="stylesheet" type="text/css" media="all" />
    return """
<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <title>ANGEL APPLICATION: %s</title>
    <link rel="shortcut icon" href="http://www.missioneternity.org/themes/m221e/buttons/m221e-favicon.ico" type="image/x-icon"/>
    %s
</head>""" % (title, CSS)

def showClones(path):
    return """
Recently seen replicas of this resource: 
<br/>%s""" % formatClones(path)

def showFile(even, link, linktext, size, lastmod, mimetype):
    even = even and "even" or "odd"
    if size == '':
        size = '-'
    s = """<tr class="%s"><td align="left"><a href="%s">%s</a></td><td align="center">%s</td><td align="right">%s</td><td align="right">%s</td></tr>\n""" % (even, link, linktext, lastmod, size, mimetype)
    return s

def showFileListing(data_listing):
    s = """<table border="0" cellpadding="0" cellspacing="0" id="angel-listing">
        <tr><th align="left">Name</th><th>Last Modified</th><th>Size</th><th>File Type</th></tr>\n"""
    even = False
    for row in data_listing:
        s += showFile(even, row["link"], row["linktext"], row["size"], row["lastmod"], row["type"])
        even = not even               
    s += "</table>\n"
    return s

def showDirectoryNavigation(linkList):
    return "<h1>Index of %s</h1>" % linkList

def showBlurb():
    return """<p>This is a directory listing of the <a href="http://www.missioneternity.org/angel-application/">ANGEL APPLICATION</a>,
an autonomous peer-to-peer file system developed for <a href="http://www.missioneternity.org/">MISSION ETERNITY</a>.</p>
<p>Much like <a href="http://freenetproject.org/">freenet</a>, it decouples the storage 
process from the physical storage medium by embedding data in a root-less and therefore fail-safe social network. 
Unlike freenet, our primary goal is not anonymity, but data preservation.</p>"""

def showHelpPreserve():
    return """<h3>Like the content on this site?</h3>
<ul>
<li>You can help preserving and sharing it (and add your own) 
by running the <a href="http://angelapp.missioneternity.org">ANGEL APPLICATION</a> 
on your computer.</li>
<li>The ANGEL APPLICATION fully supports WebDAV. You can make this directory part of your desktop.
E.g. on Mac OS X, simply type Command-K in the Finder, and "connect to" this page's URL.</li>
</ul>"""

def showHost(nodeName):
    return """<strong>This node is hosted on: %s</strong>""" % nodeName

def showResourceStatistics(path, nodeName):
    return """<h2>About This Network</h2>
<p>%s<br/>
    %s
</p>
%s
""" % (showHost(nodeName), showClones(path), showStatistics())

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
        linkList = '<a href="%s">%s</a>' % ("/", nodename)  +  "/" + \
            "/".join(['<a href="%s">%s</a>' % (linkTarget, pathSegment) 
                    for (linkTarget, pathSegment) in 
                    zip(linkTargets[1:], pathSegments[1:])
                    ])

        s = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">"""
        s += htmlHead(title)
        s += """<body>
        <div id="content">
        <h1 class="rechts">
            <a href="http://www.missioneternity.org/">
                <img src="http://www.missioneternity.org/themes/m221e/images/m221e-logo2-o.gif" alt="" border="0" />
            </a>
        </h1>"""

        s += showDirectoryNavigation(linkList)
        s += showFileListing(self.data_listing(request, None))   
        s += showBlurb()
        s += showResourceStatistics(self.path, nodename)
        s += showHelpPreserve()
        s += showDisclaimer()
        s += "<hr/>"
        s += "<address>Angel/"+ getVersionString() + " Server at " + nodename +"</address>"
        s += "</div>"
        s += "\n</body></html>"
        response = http.Response(200, {}, s)
        response.headers.setHeader("content-type", http_headers.MimeType('text', 'html'))
        return response

__all__ = ['DirectoryLister']
